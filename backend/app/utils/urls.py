"""Validation for externally supplied recipe links."""

from pydantic import AnyHttpUrl, TypeAdapter, ValidationError


_HTTP_URL = TypeAdapter(AnyHttpUrl)


def validate_http_url(value: str | None) -> str | None:
    if value is None or value == "":
        return value
    if not isinstance(value, str) or len(value) > 2048:
        raise ValueError("URL must be an HTTP(S) URL of at most 2048 characters")
    try:
        _HTTP_URL.validate_python(value)
    except ValidationError as exc:
        raise ValueError("URL must use HTTP or HTTPS and include a host") from exc
    return value


def safe_http_url(value: object) -> str | None:
    """Return `value` if it is a valid HTTP(S) URL, else None (never raises)."""
    try:
        return validate_http_url(value) or None  # type: ignore[arg-type]
    except ValueError:
        return None
