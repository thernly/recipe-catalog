# Security & Authentication Improvements

**Date**: November 22, 2025  
**Status**: ✅ Completed

## Overview

Unified authentication security across both app-based (email/password) and OAuth/IdP (Google, Microsoft, etc.) login methods by implementing a consistent cookie-based authentication pattern with modern CSRF protection.

## Changes Made

### 1. Unified Cookie-Based Authentication

**Problem**: OAuth login returned tokens in JSON response body (vulnerable to XSS), while app login used HttpOnly cookies.

**Solution**: Updated OAuth callback endpoints to set HttpOnly cookies, matching the app login pattern.

**Files Modified**:
- `backend/app/api/oauth.py`
  - Added `Response` parameter to `oauth_callback()`
  - Changed all three login paths to set cookies:
    - Existing user login via OAuth
    - Linked account login (OAuth + existing email)
    - New user registration via OAuth
  - All now return `{"message": "Login successful"}` instead of tokens in body

**Benefits**:
- Consistent security across all authentication methods
- Protection from XSS attacks (tokens can't be accessed by JavaScript)
- Simplified frontend (no token storage logic needed)

### 2. Removed Broken CSRF Token Implementation

**Problem**: 
- Frontend fetched CSRF tokens and sent them in `X-CSRF-Token` header
- Backend generated tokens but never validated them
- Security theater providing no actual protection

**Solution**: Removed CSRF token endpoint and handling, relying on SameSite cookies for CSRF protection.

**Files Modified**:
- `backend/app/api/auth.py` - Removed `/csrf-token` endpoint
- `backend/app/core/config.py` - Removed `X-CSRF-Token` from `ALLOWED_HEADERS`
- `frontend/src/lib/api/client.ts`:
  - Removed `skipCsrf` option
  - Removed `csrfToken` storage
  - Removed `fetchCsrfToken()` function
  - Removed `getCsrfToken()` function
  - Removed CSRF token header injection
  - Removed CSRF retry logic
- `frontend/src/lib/api/client.test.ts` - Updated tests to remove CSRF mocking

**Benefits**:
- Eliminates unnecessary complexity
- Removes security theater
- Cleaner, more maintainable code

### 3. Modern CSRF Protection via SameSite Cookies

**Current Implementation**:
Both app login (`/api/auth/login`) and OAuth login set cookies with:
```python
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,                              # XSS protection
    secure=not settings.TESTING,                # HTTPS-only in production
    samesite="strict",                          # CSRF protection
    max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
)
```

**Cookie Attributes Explained**:
- `httponly=True`: Prevents JavaScript access → XSS protection
- `secure=True`: Only sent over HTTPS → MITM protection
- `samesite="strict"`: Only sent in same-site requests → CSRF protection

## Security Model

### Defense in Depth Layers

1. **JWT Signature Validation** (authentication)
   - Every protected endpoint validates JWT signature
   - Tokens signed with `SECRET_KEY`
   - Prevents token tampering

2. **HttpOnly Cookies** (XSS protection)
   - Tokens stored in HttpOnly cookies
   - JavaScript cannot access tokens
   - Malicious scripts cannot steal credentials

3. **SameSite=Strict** (CSRF protection)
   - Browser prevents cross-site cookie sending
   - Attacker sites can't make authenticated requests
   - Modern, standards-based protection

4. **CORS** (origin restriction)
   - Only configured origins can make requests
   - Additional layer beyond SameSite

5. **Secure Flag** (HTTPS enforcement)
   - Cookies only sent over encrypted connections
   - Prevents MITM attacks

6. **Token Expiration** (limited attack window)
   - Access tokens: 15 minutes
   - Refresh tokens: 30 days
   - Automatic rotation on refresh

### Why This Is Better Than CSRF Tokens

**Old Approach (CSRF tokens)**:
- Complex implementation (generate, store, validate)
- More code to maintain and secure
- Additional attack surface
- Required for older browsers (pre-2020)

**New Approach (SameSite cookies)**:
- Built into browser security model
- No server-side storage needed
- Less code to maintain
- Widely supported (Chrome 51+, Firefox 60+, Safari 12+)

## Authentication Flows

### App-Based Login
```
User submits credentials
    ↓
POST /api/auth/login
    ↓
Backend validates password
    ↓
Sets access_token + refresh_token cookies (HttpOnly, Secure, SameSite=Strict)
    ↓
Returns {"message": "Login successful"}
```

### OAuth/IdP Login
```
User clicks "Sign in with Google"
    ↓
GET /api/auth/google/authorize → Redirects to Google
    ↓
User authenticates with Google
    ↓
Google redirects to /api/auth/google/callback
    ↓
Backend validates OAuth response
    ↓
Sets access_token + refresh_token cookies (HttpOnly, Secure, SameSite=Strict)
    ↓
Returns {"message": "Login successful"}
```

### Protected API Request
```
Frontend makes API request (credentials: 'include')
    ↓
Browser automatically sends cookies
    ↓
Backend middleware extracts access_token cookie
    ↓
JWT signature validation (decode_token)
    ↓
User lookup from database
    ↓
Check user is active
    ↓
Request proceeds with authenticated user
```

## Browser Compatibility

### SameSite Cookie Support
- ✅ Chrome 51+ (May 2016)
- ✅ Firefox 60+ (May 2018)
- ✅ Safari 12+ (Sep 2018)
- ✅ Edge 16+ (Oct 2017)

**Coverage**: >95% of users globally (as of 2025)

### Fallback for Older Browsers
For browsers without SameSite support, CORS still provides protection since:
- Only configured origins can make requests
- Origin header must match allowed origins
- Not as strong as SameSite, but still effective

## Testing

All 74 frontend tests passing after changes:
- ✅ Auth store tests (6 tests)
- ✅ API client tests (24 tests) - CSRF mocking removed
- ✅ Collections store tests (15 tests)
- ✅ RecipeCard component tests (29 tests)

## Migration Notes

### For Developers
- Frontend no longer needs to manage tokens in localStorage
- No CSRF token handling needed in API calls
- All requests use `credentials: 'include'` to send cookies
- OAuth responses now match app login responses

### For Deployment
- Ensure `ENVIRONMENT=production` in `.env` for `secure=True` cookies
- HTTPS required in production (cookies won't be sent otherwise)
- No database migrations needed
- No breaking changes to existing sessions

## Security Best Practices Followed

✅ **Principle of Least Privilege**: Tokens only accessible by backend  
✅ **Defense in Depth**: Multiple security layers  
✅ **Secure by Default**: HTTPS-only cookies in production  
✅ **Industry Standards**: Modern browser security features  
✅ **Simplicity**: Less code = fewer vulnerabilities  
✅ **Consistency**: Same security model for all auth methods  

## Future Considerations

### Potential Enhancements
1. **Refresh Token Rotation**: Implement on every use (already structured for this)
2. **Device Fingerprinting**: Track sessions per device
3. **Rate Limiting**: Already implemented via SlowAPI
4. **Audit Logging**: Log all authentication events

### Not Recommended
❌ **Double-submit CSRF tokens**: Adds complexity without benefit  
❌ **Stateful CSRF tokens**: Requires session storage  
❌ **Bearer tokens in headers**: Less secure than cookies  

## References

- [MDN: SameSite Cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite)
- [OWASP: Cross-Site Request Forgery Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [RFC 6749: OAuth 2.0 Authorization Framework](https://datatracker.ietf.org/doc/html/rfc6749)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)

---

**Reviewed By**: AI Agent  
**Approved By**: [Pending Human Review]
