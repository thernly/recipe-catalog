# API Documentation Guide

This guide explains how to properly document API endpoints in the Recipe Catalog application.

## Overview

All API endpoints should include comprehensive documentation with:
- Description of what the endpoint does
- Authentication requirements
- Rate limits (if applicable)
- Request/response examples
- Error responses

This information is automatically displayed in the OpenAPI/Swagger documentation at `/docs`.

## Standard Documentation Pattern

### 1. Response Models

Use the `responses` parameter in the route decorator to document all possible responses:

```python
@router.post(
    "/example",
    response_model=ExampleSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Resource successfully created"},
        400: {
            "description": "Invalid input",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "INVALID_INPUT",
                        "message": "Description of the error",
                        "details": {},
                        "correlation_id": "..."
                    }
                }
            },
        },
        401: {
            "description": "Not authenticated",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "UNAUTHORIZED",
                        "message": "Not authenticated",
                        "details": {},
                        "correlation_id": "..."
                    }
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "VALIDATION_ERROR",
                        "message": "Validation error",
                        "details": {
                            "errors": [
                                {"field": "field_name", "message": "Error description"}
                            ]
                        },
                        "correlation_id": "..."
                    }
                }
            },
        },
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "message": "Rate limit exceeded: 10 per 1 minute",
                        "details": {"limit": "10 per 1 minute"},
                        "correlation_id": "...",
                    }
                }
            }
        },
    },
)
async def example_endpoint(...):
    ...
```

### 2. Docstring Format

Include detailed information in the docstring:

```python
async def example_endpoint(...):
    """
    Brief description of what this endpoint does.

    Detailed explanation of the endpoint's functionality, including any important
    details about how it processes data, what side effects it may have, etc.

    **Authentication:** Required (session cookie or Bearer token) / None required

    **Rate Limit:** X requests per minute per IP address (or "None")

    Args:
        param1: Description of parameter
        param2: Description of parameter
        db: Database session

    Returns:
        ModelName: Description of what is returned

    Raises:
        HTTPException 400: When this specific error occurs
        HTTPException 401: When user is not authenticated
        HTTPException 422: When validation fails
        HTTPException 429: When rate limit is exceeded
    """
```

## Standard Error Response Format

The exception handlers in `app/main.py` shape every error into one envelope:

```python
{
    "error_code": "MACHINE_READABLE_CODE",
    "message": "Human-readable error message",
    "details": {},  # Optional additional context
    "correlation_id": "...",  # Present when a correlation ID is set
}
```

Raise an `AppException` subclass from `app/core/exceptions.py` (e.g. `InvalidInputError`)
rather than building responses by hand. Codes come from its `ErrorCode` enum:
`UNAUTHORIZED`, `INVALID_CREDENTIALS`, `TOKEN_EXPIRED`, `TOKEN_INVALID`,
`INSUFFICIENT_PERMISSIONS`, `INVALID_INPUT`, `VALIDATION_ERROR`, `RECIPE_NOT_FOUND`
(and other `*_NOT_FOUND`), `RATE_LIMIT_EXCEEDED`, `EXTERNAL_SERVICE_ERROR`,
`AI_SERVICE_ERROR`, `INTERNAL_ERROR`. A bare `HTTPException` is mapped by status
(400 `INVALID_INPUT`, 401/403 `UNAUTHORIZED`, 404 `RESOURCE_NOT_FOUND`, 500
`INTERNAL_ERROR`, 503 `EXTERNAL_SERVICE_ERROR`).

## Rate Limiting

If an endpoint uses rate limiting, document it in:
1. The `responses` dict (429 response)
2. The docstring (**Rate Limit:** section)

Example:
```python
@router.post("/login")
@limiter.limit("10/minute")
async def login(...):
    """
    ...

    **Rate Limit:** 10 requests per minute per IP address

    ...
    """
```

## Authentication Requirements

Document authentication requirements in the docstring:

- `**Authentication:** Required (session cookie or Bearer token)` - For protected endpoints
- `**Authentication:** None required` - For public endpoints

## Examples

See these endpoints for complete examples:
- `app/api/auth.py`: `/register` and `/login` endpoints
- `app/api/recipes/crud.py`: `POST /recipes/` endpoint

## Common Response Codes

- `200 OK`: Successful GET, PUT, PATCH, DELETE
- `201 Created`: Successful POST creating a resource
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Authenticated but not authorized
- `404 Not Found`: Resource doesn't exist
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error (handled automatically)

## Checklist for New Endpoints

When creating a new endpoint, ensure:

- [ ] Route decorator includes `responses` dict with all possible status codes
- [ ] Docstring has brief and detailed description
- [ ] Authentication requirements are documented
- [ ] Rate limits are documented (if applicable)
- [ ] All parameters are described in Args section
- [ ] Return type is documented
- [ ] All possible exceptions are listed in Raises section
- [ ] Error responses follow standard format
- [ ] Examples are provided for complex request/response bodies
