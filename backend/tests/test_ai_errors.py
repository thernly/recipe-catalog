"""AI failures retain actionable server diagnostics and safe API messages."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx2
import pytest

from app.core.exceptions import AIServiceError
from app.services.ai import AIService


@pytest.mark.parametrize("operation", ["recipe", "menu"])
@pytest.mark.parametrize(
    "failure,event",
    [
        ("http", "ai_upstream_http_error"),
        ("timeout", "ai_upstream_timeout"),
        ("connection", "ai_upstream_connection_error"),
        ("json", "ai_response_invalid_json"),
        ("shape", "ai_response_invalid_shape"),
        ("unexpected", "ai_generation_unexpected_error"),
    ],
)
async def test_ai_error_categories(operation, failure, event):
    service = AIService()
    service.api_key = "test-secret-key"
    response = httpx2.Response(
        429,
        headers={"x-request-id": "request-123"},
        request=httpx2.Request("POST", "https://openrouter.ai/api/v1/chat/completions"),
        json={"error": {"message": "private upstream diagnostic"}},
    )
    client = AsyncMock()
    if failure == "http":
        client.post.return_value = response
    elif failure == "timeout":
        client.post.side_effect = httpx2.ReadTimeout("private diagnostic")
    elif failure == "connection":
        client.post.side_effect = httpx2.ConnectError("private diagnostic")
    elif failure == "unexpected":
        client.post.side_effect = RuntimeError("private diagnostic")
    else:
        content = "{invalid" if failure == "json" else "[]"
        client.post.return_value = httpx2.Response(
            200, request=response.request, json={"choices": [{"message": {"content": content}}]}
        )
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=client)
    context.__aexit__ = AsyncMock(return_value=False)
    with (
        patch("app.services.ai.httpx2.AsyncClient", return_value=context),
        patch("app.services.ai.logger") as logger,
    ):
        with pytest.raises(AIServiceError) as caught:
            if operation == "recipe":
                await service.generate_recipe(["flour"])
            else:
                await service.generate_menu(1, ["dinner"])
        assert "private" not in caught.value.message
        assert "test-secret-key" not in caught.value.message
        calls = [
            call
            for method in (logger.error, logger.warning, logger.exception)
            for call in method.call_args_list
        ]
        matching = [call for call in calls if call.args[0] == event]
        assert len(matching) == 1
        fields = matching[0].kwargs
        assert fields["operation"] == operation
        assert fields["model"] == service.model
        assert fields["error_type"]
        assert fields["exc_info"] is True
        if failure == "http":
            assert fields["status_code"] == 429
            assert fields["upstream_request_id"] == "request-123"
