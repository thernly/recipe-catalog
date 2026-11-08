"""Regression coverage for the November application review."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.core.oauth import extract_user_info
from app.models.oauth_state import OAuthState
from app.models.token import PasswordResetToken, VerificationToken
from app.schemas.recipe import RecipeCreate
from app.services.ingredient_parser import parse_ingredient_line
from app.services.recipe_cleanup import parse_duration_minutes
from app.utils.recipe_format import convert_from_schema_org


@pytest.mark.parametrize("model", [PasswordResetToken, VerificationToken, OAuthState])
async def test_sqlite_token_expiry(test_db, test_user, model):
    token = (
        model.create_state("google") if model is OAuthState else model.create_for_user(test_user.id)
    )
    test_db.add(token)
    await test_db.commit()
    await test_db.refresh(token)
    assert token.is_valid()
    token.expires_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)
    assert not token.is_valid()


def test_microsoft_does_not_assert_email_ownership():
    info = extract_user_info(
        "microsoft", {"sub": "attacker", "preferred_username": "victim@example.com"}
    )
    assert not info["email_verified"]
    assert info["email"] is None


@pytest.mark.parametrize(
    "url", ["javascript:alert(1)", "//evil.test", "data:text/html,hi", "https://"]
)
def test_reject_unsafe_recipe_urls(url):
    with pytest.raises(ValidationError):
        RecipeCreate(name="Soup", recipe_data={}, source_url=url)


@pytest.mark.parametrize(
    "duration", [float("inf"), float("nan"), "PT" + "9" * 400 + "M", "9" * 400 + " hours"]
)
def test_extreme_duration_is_unreadable(duration):
    assert parse_duration_minutes(duration) is None


def test_extreme_ingredient_is_safe():
    assert parse_ingredient_line("9" * 400 + " g flour")
    assert parse_ingredient_line("juice of " * 1500 + "1 lemon")


async def test_import_validates_text_and_urls():
    with pytest.raises(ValueError):
        await convert_from_schema_org({"name": 123})
    # An unsafe page URL is dropped rather than rejecting the whole recipe
    converted = await convert_from_schema_org({"name": "Soup", "url": "javascript:alert(1)"})
    assert converted["source_url"] is None


async def test_manual_create_and_update_keep_ampersand(client, test_user_headers):
    created = await client.post(
        "/api/v1/recipes/",
        headers=test_user_headers,
        json={"name": "Mac & Cheese <b>x</b>", "recipe_data": {}},
    )
    assert created.status_code == 201
    assert created.json()["name"] == "Mac & Cheese x"
    updated = await client.patch(
        f"/api/v1/recipes/{created.json()['id']}",
        headers=test_user_headers,
        json={"description": "Salt & pepper"},
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "Salt & pepper"


async def test_duplicate_is_visible_and_collection_ids_are_deduplicated(client, test_user_headers):
    collection = await client.post(
        "/api/v1/collections/", headers=test_user_headers, json={"name": "Regression collection"}
    )
    collection_id = collection.json()["id"]
    created = await client.post(
        "/api/v1/recipes/",
        headers=test_user_headers,
        json={
            "name": "Soup",
            "recipe_data": {},
            "collection_ids": [collection_id, collection_id],
        },
    )
    assert created.status_code == 201
    copied = await client.post(
        f"/api/v1/recipes/{created.json()['id']}/duplicate", headers=test_user_headers
    )
    assert copied.status_code == 201
    assert (
        await client.get(f"/api/v1/recipes/{copied.json()['id']}", headers=test_user_headers)
    ).status_code == 200


async def test_reset_invalidates_previous_tokens_and_revokes_sessions(client, test_db, test_user):
    from sqlalchemy import select

    from app.core.security import hash_token
    from app.models.refresh_token import RefreshToken

    old = PasswordResetToken.create_for_user(test_user.id)
    test_db.add(old)
    refresh = RefreshToken(
        token=hash_token("stolen"),
        user_id=test_user.id,
        expires_at=datetime.now(UTC) + timedelta(days=1),
        revoked=False,
    )
    test_db.add(refresh)
    await test_db.commit()
    response = await client.post(
        "/api/v1/auth/forgot-password", json={"email": test_user.email.upper()}
    )
    assert response.status_code == 200
    await test_db.refresh(old)
    assert old.used
    reset = PasswordResetToken.create_for_user(test_user.id)
    test_db.add(reset)
    await test_db.commit()
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset.raw_token, "new_password": "ChangedPassword123!"},
    )
    assert response.status_code == 200
    await test_db.refresh(refresh)
    assert refresh.revoked
    assert (
        not (await test_db.execute(select(RefreshToken).where(RefreshToken.revoked.is_(False))))
        .scalars()
        .all()
    )


async def test_resend_verification_has_uniform_response(client, test_user):
    existing = await client.post(
        "/api/v1/auth/resend-verification", json={"email": test_user.email}
    )
    unknown = await client.post(
        "/api/v1/auth/resend-verification", json={"email": "unknown@example.com"}
    )
    assert existing.status_code == unknown.status_code == 200
    assert existing.json() == unknown.json()


async def test_email_change_requires_password_and_new_address_verification(
    client, test_user_headers, test_db
):
    from unittest.mock import AsyncMock, patch

    from sqlalchemy import select

    response = await client.patch(
        "/api/v1/users/me", headers=test_user_headers, json={"email": "new@example.com"}
    )
    assert response.status_code == 400
    with patch(
        "app.core.email.email_service.send_verification_email", new_callable=AsyncMock
    ) as send:
        response = await client.patch(
            "/api/v1/users/me",
            headers=test_user_headers,
            json={"email": "new@example.com", "current_password": "SecurePass123!"},
        )
    assert response.status_code == 200
    assert response.json()["email"] != "new@example.com"
    verification = (
        await test_db.execute(
            select(VerificationToken).where(VerificationToken.pending_email == "new@example.com")
        )
    ).scalar_one()
    assert not verification.used
    raw_token = send.call_args.kwargs["verification_token"]
    response = await client.post(f"/api/v1/auth/verify-email/{raw_token}")
    assert response.status_code == 200
    response = await client.get("/api/v1/users/me", headers=test_user_headers)
    assert response.json()["email"] == "new@example.com"


async def test_microsoft_callback_cannot_link_victim_account(client, test_db, test_user):
    from unittest.mock import AsyncMock, patch

    from sqlalchemy import select

    from app.models.identity_provider import IdentityProvider

    state = OAuthState.create_state("microsoft")
    test_db.add(state)
    await test_db.commit()
    provider = AsyncMock()
    provider.authorize_access_token.return_value = {
        "userinfo": {
            "sub": "attacker",
            "email": test_user.email,
            "email_verified": True,
        }
    }
    with patch("app.api.oauth.oauth.create_client", return_value=provider):
        response = await client.get(
            f"/api/v1/auth/microsoft/callback?state={state.raw_token}&code=attack"
        )
    assert response.status_code == 400
    assert "access_token" not in response.cookies
    assert not (await test_db.execute(select(IdentityProvider))).scalars().all()


async def test_oauth_authorize_can_use_browser_session(client):
    from unittest.mock import patch

    from starlette.responses import RedirectResponse

    class Provider:
        async def authorize_redirect(self, request, redirect_uri, state):
            request.session["state"] = state
            return RedirectResponse("https://provider.example/authorize")

    from app.core.config import settings

    # SessionMiddleware configuration was constructed before testing mode was enabled.
    base = "https://test" if settings.ENVIRONMENT == "production" else "http://test"
    with patch("app.api.oauth.oauth.create_client", return_value=Provider()):
        response = await client.get(base + "/api/v1/auth/google/authorize")
    assert response.status_code == 307
    assert "session=" in response.headers["set-cookie"]


async def test_import_limits_and_bad_entries_do_not_abort_batch(test_db, test_user):
    from app.api.import_recipes import _import_recipes_internal
    from app.core.exceptions import InvalidInputError
    from app.models.recipe import Recipe

    for _ in range(2):
        test_db.add(Recipe(user_id=test_user.id, name="Soup", recipe_data={}, source_type="manual"))
    await test_db.commit()
    result = await _import_recipes_internal(
        [None, {"name": 42}, {"name": "Soup"}], test_user.id, 1, "skip", None, test_db
    )
    assert result["failed"] == 2
    assert result["skipped"] == 1
    with pytest.raises(InvalidInputError):
        await _import_recipes_internal(
            [{"name": "Soup"}] * 501, test_user.id, 1, "create", None, test_db
        )


async def test_chunked_upload_and_invalid_content_length(client):
    from app.core.config import settings

    async def oversized_body():
        yield b"x" * (settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024 + 1)

    response = await client.post("/api/v1/auth/login", content=oversized_body())
    assert response.status_code == 413
    response = await client.post(
        "/api/v1/auth/login", content=b"{}", headers={"content-length": "invalid"}
    )
    assert response.status_code == 400


async def test_membership_changes_preserve_access_and_meal_ownership(test_db, test_user):
    from datetime import date

    from sqlalchemy import select

    from app.models.household import HouseholdMember
    from app.models.meal_plan import MealPlan, PlannedMeal
    from app.models.recipe import Recipe
    from app.models.user import User
    from app.services import household as service

    owner = test_user
    member = User(email="member@example.com", is_active=True, is_verified=True)
    test_db.add(member)
    await test_db.flush()
    household = await service.create_household(test_db, "Shared", owner.id)
    test_db.add(HouseholdMember(household_id=household.id, user_id=member.id, role="member"))
    recipe = Recipe(
        user_id=member.id, household_id=household.id, name="Member soup", recipe_data={}
    )
    plan = MealPlan(
        household_id=household.id, week_start_date=date(2026, 11, 2), created_by_user_id=owner.id
    )
    test_db.add_all([recipe, plan])
    await test_db.flush()
    meal = PlannedMeal(
        meal_plan_id=plan.id,
        recipe_id=recipe.id,
        created_by_user_id=member.id,
        day_of_week=0,
        meal_type="dinner",
    )
    test_db.add(meal)
    await test_db.commit()
    meal_id = meal.id
    await service.remove_household_member(test_db, household.id, member.id, owner.id)
    personal = await service.get_user_household(test_db, member.id)
    assert personal and personal.is_personal
    await test_db.refresh(recipe)
    assert recipe.household_id == personal.id
    await test_db.refresh(meal)
    assert meal.meal_plan_id != plan.id
    code = await service.create_invite_link(test_db, household.id, owner.id)
    await service.join_via_invite_link(test_db, code.code, member.id)
    await test_db.refresh(meal)
    assert meal.meal_plan_id == plan.id
    await service.leave_household(test_db, member.id)
    preserved = (
        await test_db.execute(select(PlannedMeal).where(PlannedMeal.id == meal_id))
    ).scalar_one()
    await test_db.refresh(preserved)
    personal = await service.get_user_household(test_db, member.id)
    assert personal and personal.is_personal
    private_plan = await test_db.get(MealPlan, preserved.meal_plan_id)
    assert private_plan.household_id == personal.id
    assert preserved.created_by_user_id == member.id


async def test_delete_household_with_invite_links_preserves_private_data(test_db, test_user):
    from datetime import date

    from sqlalchemy import select, text

    from app.models.household import HouseholdInviteLink
    from app.models.meal_plan import MealPlan, PlannedMeal
    from app.models.recipe import Recipe
    from app.services import household as service

    await test_db.commit()
    await test_db.execute(text("PRAGMA foreign_keys=ON"))
    assert (await test_db.execute(text("PRAGMA foreign_keys"))).scalar() == 1
    household = await service.create_household(test_db, "Delete me", test_user.id)
    recipe = Recipe(user_id=test_user.id, household_id=household.id, name="Keep me", recipe_data={})
    plan = MealPlan(
        household_id=household.id,
        created_by_user_id=test_user.id,
        week_start_date=date(2026, 11, 2),
    )
    test_db.add_all([recipe, plan])
    await test_db.flush()
    meal = PlannedMeal(
        meal_plan_id=plan.id,
        recipe_id=recipe.id,
        created_by_user_id=test_user.id,
        day_of_week=0,
        meal_type="dinner",
    )
    test_db.add(meal)
    await test_db.commit()
    await service.create_invite_link(test_db, household.id, test_user.id)
    await service.delete_household(test_db, household.id, test_user.id)
    private = await service.get_user_household(test_db, test_user.id)
    assert private and private.is_personal
    await test_db.refresh(recipe)
    assert recipe.household_id == private.id
    await test_db.refresh(meal)
    assert (await test_db.get(MealPlan, meal.meal_plan_id)).household_id == private.id
    assert not (await test_db.execute(select(HouseholdInviteLink))).scalars().all()


async def test_public_recovery_flows_work_without_auth_cookies(
    client, test_db, test_user, monkeypatch
):
    from app.core.config import settings

    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    response = await client.post("/api/v1/auth/forgot-password", json={"email": test_user.email})
    assert response.status_code == 200
    response = await client.post(
        "/api/v1/auth/resend-verification", json={"email": test_user.email}
    )
    assert response.status_code == 200
    reset = PasswordResetToken.create_for_user(test_user.id)
    verification = VerificationToken.create_for_user(test_user.id)
    test_db.add_all([reset, verification])
    await test_db.commit()
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset.raw_token, "new_password": "ChangedPassword123!"},
    )
    assert response.status_code == 200
    response = await client.post(f"/api/v1/auth/verify-email/{verification.raw_token}")
    assert response.status_code == 200


def test_pdf_preserves_unicode_with_registered_font_and_handles_core_font():
    from app.utils.pdf_export import _clean_text

    assert _clean_text("Ελληνικά 中文", "NotoSans") == "Ελληνικά 中文"
    assert _clean_text("中文", "helvetica") == "??"


def test_non_finite_recipe_times_are_not_stored_as_invalid_json():
    from app.services.recipe_cleanup import clean_recipe_data

    assert clean_recipe_data({"prepTime": float("inf")}).data["prepTime"] is None


async def test_ai_menu_nulls_recipe_ids_outside_selected_household_catalog(
    client, test_db, test_user_headers
):
    from unittest.mock import AsyncMock, patch

    from sqlalchemy import select

    from app.models.recipe import Recipe
    from app.models.user import User
    from app.services.household import get_user_household

    user = (
        await test_db.execute(select(User).where(User.email == "testuser@example.com"))
    ).scalar_one()
    household = await get_user_household(test_db, user.id)
    recipe = Recipe(user_id=user.id, household_id=household.id, name="Catalog soup", recipe_data={})
    test_db.add(recipe)
    await test_db.commit()
    suggestions = [
        {
            "day": 1,
            "meal_type": "dinner",
            "recipe_name": "Catalog soup",
            "recipe_id": str(recipe.id),
        },
        {"day": 1, "meal_type": "lunch", "recipe_name": "Unknown", "recipe_id": 999999},
    ]
    with patch(
        "app.api.ai.ai_service.generate_menu", new_callable=AsyncMock, return_value=suggestions
    ):
        response = await client.post(
            "/api/v1/ai/generate-menu",
            headers=test_user_headers,
            json={
                "days": 1,
                "meals_per_day": ["dinner"],
                "household_recipe_ids": [recipe.id],
            },
        )
    assert response.status_code == 200
    ids = [suggestion["recipe_id"] for suggestion in response.json()["suggestions"]]
    assert ids == [recipe.id, None]


async def test_departed_owner_can_share_their_new_personal_household(test_db, test_user):
    from app.models.user import User
    from app.services import household as service

    await service.create_household(test_db, "Original", test_user.id)
    await service.leave_household(test_db, test_user.id)
    personal = await service.get_user_household(test_db, test_user.id)
    code = await service.create_invite_link(test_db, personal.id, test_user.id)
    guest = User(email="guest@example.com", is_active=True, is_verified=True)
    test_db.add(guest)
    await test_db.commit()
    await service.join_via_invite_link(test_db, code.code, guest.id)
    assert len(await service.get_household_members(test_db, personal.id)) == 2
    await test_db.refresh(personal)
    assert not personal.is_personal
