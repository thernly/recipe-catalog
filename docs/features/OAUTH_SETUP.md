# OAuth / Identity Provider Authentication Setup

This guide explains how to set up OAuth/OIDC authentication with Google, Microsoft, and GitHub for the Recipe Catalog application.

## Overview

Feature 14 adds support for:
- **Google OAuth 2.0 / OIDC** - Primary authentication method
- **Microsoft OAuth 2.0 / OIDC** - Primary authentication method
- **GitHub OAuth 2.0** - Optional authentication method
- **Account Linking** - Users can link multiple providers to one account
- **Passwordless Accounts** - Users can sign up without a password using IdPs

## Architecture

### Database Schema

**`identity_providers` table:**
- `id` - Primary key
- `user_id` - Foreign key to users table
- `provider_name` - Provider identifier (google, microsoft, github)
- `provider_subject` - Unique user ID from provider
- `email_at_provider` - Email address from provider
- `created_at` - When link was created
- `last_used_at` - Last successful authentication

**`users` table changes:**
- `hashed_password` - Now nullable (for IdP-only accounts)
- `email_verified_at` - Timestamp when email was verified

### API Endpoints

- `GET /api/v1/auth/providers` - List available OAuth providers
- `GET /api/v1/auth/{provider}/authorize` - Initiate OAuth flow
- `GET /api/v1/auth/{provider}/callback` - Handle OAuth callback
- `GET /api/v1/auth/me/providers` - List user's linked providers
- `DELETE /api/v1/auth/providers/{id}` - Unlink a provider

## Provider Setup

### 1. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Enable Google+ API (or Google Identity)
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Configure OAuth consent screen:
   - User Type: External
   - App name: Recipe Catalog
   - Scopes: openid, email, profile
6. Create OAuth 2.0 Client ID:
   - Application type: Web application
   - Authorized redirect URIs:
     - `http://localhost:8000/api/v1/auth/google/callback` (development)
     - `https://your-domain.com/api/v1/auth/google/callback` (production)
7. Copy Client ID and Client Secret

**Environment Variables:**
```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

### 2. Microsoft OAuth Setup

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to "Azure Active Directory" → "App registrations"
3. Click "New registration"
   - Name: Recipe Catalog
   - Supported account types: "Accounts in any organizational directory and personal Microsoft accounts"
   - Redirect URI: Web → `http://localhost:8000/api/v1/auth/microsoft/callback`
4. After creation, note the "Application (client) ID"
5. Go to "Certificates & secrets" → "New client secret"
   - Description: Recipe Catalog Backend
   - Copy the secret value (only shown once!)
6. Go to "API permissions"
   - Add permission → Microsoft Graph → Delegated permissions
   - Add: openid, email, profile

**Environment Variables:**
```bash
MICROSOFT_CLIENT_ID=your-application-id
MICROSOFT_CLIENT_SECRET=your-client-secret
```

### 3. GitHub OAuth Setup (Optional)

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click "New OAuth App"
   - Application name: Recipe Catalog
   - Homepage URL: `http://localhost:5173` (development)
   - Authorization callback URL: `http://localhost:8000/api/v1/auth/github/callback`
3. Copy Client ID and generate Client Secret

**Environment Variables:**
```bash
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

## Configuration

### Backend Environment Variables

Add to `backend/.env`:

```bash
# OAuth / Identity Providers
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret

GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# OAuth Redirect URI base (must match provider configuration)
OAUTH_REDIRECT_BASE_URL=http://localhost:8000/api/v1/auth
```

### Frontend Configuration

The frontend needs to be configured to:
1. Display OAuth provider buttons on login/signup pages
2. Handle OAuth redirect flows
3. Allow users to manage linked providers in settings

## Security Considerations

### CSRF Protection

- State tokens are generated and validated for each OAuth flow
- Tokens are stored temporarily and deleted after use
- State includes provider name to prevent substitution attacks

### Account Linking

- Automatic linking only occurs if:
  - Email from provider matches existing account email
  - Provider has verified the email address
- Users can link multiple providers to one account
- Users cannot remove their last authentication method

### Email Verification

- Emails verified by IdP are trusted
- `is_verified` flag set to true for IdP signups
- `email_verified_at` timestamp recorded

### Data Minimization

- Only essential user data is stored (subject ID, email, display name)
- No access tokens or refresh tokens are persisted
- Provider responses are not logged

## Testing

### Manual Testing

1. Start the backend server: `cd backend && uv run uvicorn app.main:app --reload`
2. Visit http://localhost:8000/api/v1/auth/providers to see configured providers
3. Test OAuth flow:
   - Navigate to http://localhost:8000/api/v1/auth/google/authorize
   - Complete Google authentication
   - Verify redirect to callback and token generation
4. Test account linking:
   - Create account with email/password
   - Link Google account with same email
   - Verify both authentication methods work

### Production Deployment

**Important:** Update redirect URIs in all provider configurations to use production URLs:
- Google: `https://your-domain.com/api/v1/auth/google/callback`
- Microsoft: `https://your-domain.com/api/v1/auth/microsoft/callback`
- GitHub: `https://your-domain.com/api/v1/auth/github/callback`

Update `OAUTH_REDIRECT_BASE_URL` in production environment:
```bash
OAUTH_REDIRECT_BASE_URL=https://your-domain.com/api/v1/auth
```

## Troubleshooting

### "Provider not configured" error
- Verify environment variables are set correctly
- Restart backend server after changing .env file
- Check that CLIENT_ID and CLIENT_SECRET are not empty strings

### "Invalid state parameter" error
- Clear browser cookies
- State tokens expire after OAuth flow
- Do not refresh the callback page

### "Email already registered" with different provider
- This is expected behavior for account security
- User should log in with existing method first
- Then link additional provider from settings

### OAuth callback URL mismatch
- Verify OAUTH_REDIRECT_BASE_URL matches provider configuration exactly
- Include protocol (http:// or https://)
- Ensure no trailing slashes

## Migration Notes

For existing users:
- Existing accounts continue to work with email/password
- Users can optionally link OAuth providers in settings
- No data migration required for Feature 14
- `hashed_password` made nullable but existing passwords remain

## Future Enhancements

- **Passkey Support** - WebAuthn/FIDO2 passwordless authentication
- **Persistent State Storage** - Redis for production state management
- **Token Refresh** - Store refresh tokens for long-lived sessions
- **Provider Management UI** - Frontend settings page
- **Admin Dashboard** - View OAuth usage analytics
