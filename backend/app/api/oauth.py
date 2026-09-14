"""OAuth/OIDC authentication API endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.logging import get_logger
from app.core.oauth import (
    extract_user_info,
    get_available_providers,
    oauth,
)
from app.core.security import (
    create_access_token,
    generate_csrf_token,
    generate_refresh_token,
    get_refresh_token_expiry,
    hash_token,
    is_safe_redirect_url,
)
from app.models.identity_provider import IdentityProvider
from app.models.oauth_state import OAuthState
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserPreferences
from app.schemas.oauth import LinkedProviderResponse, ProviderInfo


router = APIRouter()
logger = get_logger(__name__)
limiter = Limiter(key_func=get_remote_address)


@router.get("/providers", response_model=list[ProviderInfo])
async def list_available_providers():
    """Get list of available OAuth providers."""
    return get_available_providers()


@router.get("/{provider}/authorize")
@limiter.limit("10/minute")
async def authorize_provider(
    request: Request,
    provider: str,
    return_url: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Initiate OAuth flow with the specified provider.

    Args:
        provider: Provider name (google, microsoft, github)
        return_url: Optional URL to redirect to after successful authentication
                   (must be validated against allowed origins)

    Returns:
        RedirectResponse to provider's authorization URL

    Security:
        If return_url is provided, it is validated against ALLOWED_ORIGINS and
        FRONTEND_URL to prevent open redirect vulnerabilities (CWE-601).
    """
    if provider not in ["google", "microsoft", "github"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown provider: {provider}",
        )

    client = oauth.create_client(provider)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Provider {provider} not configured",
        )

    # Validate redirect URL if provided (prevents open redirect attacks)
    validated_return_url = None
    if return_url:
        if not is_safe_redirect_url(return_url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid return URL. URL must belong to an allowed origin.",
            )
        validated_return_url = return_url

    # Create OAuth state in database for CSRF protection
    oauth_state = OAuthState.create_state(
        provider=provider,
        link_user_id=None,
        redirect_url=validated_return_url,
    )
    db.add(oauth_state)
    await db.commit()
    await db.refresh(oauth_state)

    # Build redirect URI -- must match the callback route registered below
    # ("/{provider}/callback" under this router's /api/v1/auth prefix).
    redirect_uri = f"{settings.OAUTH_REDIRECT_BASE_URL}/{provider}/callback"

    # Redirect to provider's authorization URL
    return await client.authorize_redirect(request, redirect_uri, state=oauth_state.raw_token)


@router.get("/{provider}/callback")
@limiter.limit("10/minute")
async def oauth_callback(
    request: Request,
    response: Response,
    provider: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle OAuth callback from provider and set httpOnly cookies.

    Args:
        provider: Provider name
        request: FastAPI request object
        db: Database session

    Returns:
        Token: JWT access token

    Security Note:
        The OAuth state may contain a redirect_url for post-authentication redirect.
        If redirect_url is present, it has already been validated in the authorize
        endpoint using is_safe_redirect_url(). However, for defense in depth,
        any future implementation that uses this redirect_url should re-validate
        it before performing the redirect to prevent open redirect vulnerabilities.
    """
    if provider not in ["google", "microsoft", "github"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown provider: {provider}",
        )

    client = oauth.create_client(provider)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Provider {provider} not configured",
        )

    # Get state from query params
    state_token = request.query_params.get("state")
    if not state_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or missing state parameter",
        )

    # Retrieve state from database
    hashed_state_token = hash_token(state_token)
    result = await db.execute(select(OAuthState).where(OAuthState.token == hashed_state_token))
    oauth_state = result.scalar_one_or_none()

    if not oauth_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state token",
        )

    # Validate state is not expired
    if not oauth_state.is_valid():
        await db.delete(oauth_state)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State token expired",
        )

    # Validate state matches provider
    state_data = oauth_state.data
    if state_data["provider"] != provider:
        await db.delete(oauth_state)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="State mismatch")

    # Delete state after use (one-time use)
    await db.delete(oauth_state)
    await db.commit()

    try:
        # Exchange authorization code for token
        token = await client.authorize_access_token(request)

        # Get user info from provider
        if provider == "github":
            # GitHub requires separate API call for user info
            resp = await client.get("user", token=token)
            userinfo = resp.json()
        else:
            # OIDC providers include userinfo in token
            userinfo = token.get("userinfo")

        if not userinfo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info from provider",
            )

        # Extract standardized user info
        user_data = extract_user_info(provider, userinfo)

        # Check if this provider account is already linked
        result = await db.execute(
            select(IdentityProvider).where(
                IdentityProvider.provider_name == provider,
                IdentityProvider.provider_subject == user_data["subject"],
            )
        )
        existing_idp = result.scalar_one_or_none()

        if existing_idp:
            # Update last used timestamp
            existing_idp.last_used_at = datetime.now(UTC)
            await db.commit()

            # Get associated user
            user = await db.get(User, existing_idp.user_id)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive",
                )

            logger.info(f"User {user.id} logged in via {provider}")

            # Create access token
            access_token = create_access_token(data={"sub": str(user.id)})

            # Generate and store refresh token
            refresh_token_value = generate_refresh_token()
            refresh_token = RefreshToken(
                token=hash_token(refresh_token_value),
                user_id=user.id,
                expires_at=get_refresh_token_expiry(),
                revoked=False,
            )
            db.add(refresh_token)
            await db.commit()

            # Set httpOnly cookies (same as app login)
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=settings.ENVIRONMENT == "production",
                samesite="strict",
                max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            )
            response.set_cookie(
                key="refresh_token",
                value=refresh_token_value,
                httponly=True,
                secure=settings.ENVIRONMENT == "production",
                samesite="strict",
                max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            )

            # Generate and set CSRF token
            csrf_token = generate_csrf_token()
            response.set_cookie(
                key="csrf_token",
                value=csrf_token,
                httponly=False,
                secure=settings.ENVIRONMENT == "production",
                samesite="strict",
                max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            )

            return {"message": "Login successful", "csrf_token": csrf_token}

        # Check if email already exists (for account linking)
        email_result = await db.execute(
            select(User).where(User.email == user_data["email"].lower())
        )
        existing_user = email_result.scalar_one_or_none()

        if existing_user:
            # Email exists - this requires user confirmation for linking
            # For simplicity, we'll auto-link if email is verified by provider
            if not user_data["email_verified"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email not verified by provider. Cannot auto-link account.",
                )

            # Link provider to existing account
            new_idp = IdentityProvider(
                user_id=existing_user.id,
                provider_name=provider,
                provider_subject=user_data["subject"],
                email_at_provider=user_data["email"],
            )
            db.add(new_idp)

            # Mark email as verified if provider confirmed it
            if user_data["email_verified"] and not existing_user.email_verified_at:
                existing_user.email_verified_at = datetime.now(UTC)
                existing_user.is_verified = True

            await db.commit()

            logger.info(f"Linked {provider} to existing user {existing_user.id}")

            access_token = create_access_token(data={"sub": str(existing_user.id)})

            # Generate and store refresh token
            refresh_token_value = generate_refresh_token()
            refresh_token = RefreshToken(
                token=hash_token(refresh_token_value),
                user_id=existing_user.id,
                expires_at=get_refresh_token_expiry(),
                revoked=False,
            )
            db.add(refresh_token)
            await db.commit()

            # Set httpOnly cookies (same as app login)
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=settings.ENVIRONMENT == "production",
                samesite="strict",
                max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            )
            response.set_cookie(
                key="refresh_token",
                value=refresh_token_value,
                httponly=True,
                secure=settings.ENVIRONMENT == "production",
                samesite="strict",
                max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            )

            # Generate and set CSRF token
            csrf_token = generate_csrf_token()
            response.set_cookie(
                key="csrf_token",
                value=csrf_token,
                httponly=False,
                secure=settings.ENVIRONMENT == "production",
                samesite="strict",
                max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            )

            return {"message": "Login successful", "csrf_token": csrf_token}

        # Create new user account
        new_user = User(
            email=user_data["email"].lower(),
            hashed_password=None,  # Passwordless account
            display_name=user_data["display_name"],
            is_active=True,
            is_verified=user_data["email_verified"],
            email_verified_at=datetime.now(UTC) if user_data["email_verified"] else None,
        )

        db.add(new_user)
        await db.flush()

        # Create identity provider link
        new_idp = IdentityProvider(
            user_id=new_user.id,
            provider_name=provider,
            provider_subject=user_data["subject"],
            email_at_provider=user_data["email"],
        )
        db.add(new_idp)

        # Create default preferences
        preferences = UserPreferences(user_id=new_user.id)
        db.add(preferences)

        # Create default household
        from app.services.household import create_default_household_for_new_user

        household = await create_default_household_for_new_user(db, new_user)
        logger.info(
            f"Created household '{household.name}' (ID: {household.id}) for user {new_user.id}"
        )

        # Create default collections
        from app.models.collection import Collection

        default_collections = [
            Collection(
                user_id=new_user.id,
                name="Favorites",
                description="Your favorite recipes",
                is_default=True,
                icon="⭐",
            ),
        ]
        db.add_all(default_collections)

        await db.commit()

        logger.info(f"Created new user {new_user.id} via {provider}")

        # Create access token
        access_token = create_access_token(data={"sub": str(new_user.id)})

        # Generate and store refresh token
        refresh_token_value = generate_refresh_token()
        refresh_token = RefreshToken(
            token=hash_token(refresh_token_value),
            user_id=new_user.id,
            expires_at=get_refresh_token_expiry(),
            revoked=False,
        )
        db.add(refresh_token)
        await db.commit()

        # Set httpOnly cookies (same as app login)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=settings.ENVIRONMENT == "production",
            samesite="strict",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token_value,
            httponly=True,
            secure=settings.ENVIRONMENT == "production",
            samesite="strict",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

        # Generate and set CSRF token
        csrf_token = generate_csrf_token()
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            httponly=False,
            secure=settings.ENVIRONMENT == "production",
            samesite="strict",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

        return {"message": "Login successful", "csrf_token": csrf_token}

    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authentication failed: {str(e)}",
        )


@router.get("/me/providers", response_model=list[LinkedProviderResponse])
async def list_linked_providers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of identity providers linked to current user."""
    result = await db.execute(
        select(IdentityProvider).where(IdentityProvider.user_id == current_user.id)
    )
    providers = result.scalars().all()
    return providers


@router.delete("/providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_provider(
    provider_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove a linked identity provider.

    Validates that user has at least one authentication method remaining.
    """
    # Get the provider to delete
    idp = await db.get(IdentityProvider, provider_id)
    if not idp or idp.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")

    # Check if user has password or other providers
    result = await db.execute(
        select(IdentityProvider).where(IdentityProvider.user_id == current_user.id)
    )
    all_providers = result.scalars().all()

    has_password = current_user.hashed_password is not None
    provider_count = len(all_providers)

    if not has_password and provider_count <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove last authentication method. Please set a password first.",
        )

    await db.delete(idp)
    await db.commit()

    logger.info(f"User {current_user.id} unlinked provider {idp.provider_name}")
