import json
from types import SimpleNamespace

from limits import parse
from slowapi.errors import RateLimitExceeded

from app.main import app, rate_limit_exceeded_handler


async def test_rate_limit_uses_error_envelope():
    limit = SimpleNamespace(limit=parse("5/minute"), error_message=None)
    request = SimpleNamespace(
        app=app,
        headers={"X-Correlation-ID": "abc"},
        state=SimpleNamespace(view_rate_limit=None),
    )
    response = await rate_limit_exceeded_handler(request, RateLimitExceeded(limit))
    body = json.loads(response.body)
    assert response.status_code == 429
    assert body["error_code"] == "RATE_LIMIT_EXCEEDED"
    assert body["correlation_id"] == "abc"
    assert set(body) == {"error_code", "message", "details", "correlation_id"}
