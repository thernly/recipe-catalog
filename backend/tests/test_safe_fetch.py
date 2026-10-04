"""Tests for the SSRF-safe fetch helper."""

import ipaddress
from unittest.mock import patch

import httpx
import pytest

from app.utils.safe_fetch import SafeFetchError, is_public_address, safe_fetch


PUBLIC_IP = "93.184.216.34"
IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]


def fake_dns(mapping: dict[str, list[str]]):
    """Patch DNS resolution with a fixed host -> addresses mapping."""

    async def _resolve(host: str, port: int):
        if host not in mapping:
            raise OSError("no such host")
        return [ipaddress.ip_address(a) for a in mapping[host]]

    return patch("app.utils.safe_fetch._resolve", side_effect=_resolve)


def image_handler(requests: list[httpx.Request], body: bytes = b"\x89PNG data"):
    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, headers={"Content-Type": "image/png"}, content=body)

    return handler


async def fetch(url: str, transport: httpx.AsyncBaseTransport, **kwargs):
    kwargs.setdefault("max_bytes", 1024)
    kwargs.setdefault("allowed_content_types", IMAGE_TYPES)
    return await safe_fetch(url, transport=transport, **kwargs)


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.1.2.3",
        "172.16.0.5",
        "192.168.1.10",
        "169.254.169.254",  # cloud metadata
        "100.100.100.200",  # shared address space (Alibaba metadata)
        "0.0.0.0",
        "224.0.0.1",
        "::1",
        "fe80::1",
        "fc00::1",
        "fd00:ec2::254",  # AWS IPv6 metadata
        "::ffff:127.0.0.1",  # IPv4-mapped loopback
        "::ffff:169.254.169.254",
        "::",
    ],
)
def test_non_public_addresses_are_refused(address):
    assert is_public_address(ipaddress.ip_address(address)) is False


@pytest.mark.parametrize("address", [PUBLIC_IP, "1.1.1.1", "2606:4700:4700::1111"])
def test_public_addresses_are_allowed(address):
    assert is_public_address(ipaddress.ip_address(address)) is True


async def test_fetch_connects_to_checked_address():
    requests: list[httpx.Request] = []
    with fake_dns({"images.example.com": [PUBLIC_IP]}):
        result = await fetch(
            "https://images.example.com/a.png?x=1",
            httpx.MockTransport(image_handler(requests)),
        )

    assert result.content == b"\x89PNG data"
    assert result.content_type == "image/png"
    assert len(requests) == 1
    sent = requests[0]
    # Connection goes to the resolved IP; the name travels in Host and SNI
    assert sent.url.host == PUBLIC_IP
    assert sent.url.path == "/a.png"
    assert sent.url.query == b"x=1"
    assert sent.headers["Host"] == "images.example.com"
    assert sent.extensions["sni_hostname"] == "images.example.com"


async def test_ipv6_address_is_bracketed():
    requests: list[httpx.Request] = []
    with fake_dns({"v6.example.com": ["2606:4700:4700::1111"]}):
        await fetch("http://v6.example.com/a.png", httpx.MockTransport(image_handler(requests)))

    assert requests[0].url.host == "2606:4700:4700::1111"
    assert requests[0].headers["Host"] == "v6.example.com"


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com/a.png",
        "gopher://example.com/",
        "/relative/path.png",
    ],
)
async def test_non_http_schemes_are_refused(url):
    requests: list[httpx.Request] = []
    with pytest.raises(SafeFetchError):
        await fetch(url, httpx.MockTransport(image_handler(requests)))
    assert requests == []


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/a.png",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/a.png",
        "http://[::ffff:10.0.0.1]/a.png",
        "http://internal.example.com/a.png",
    ],
)
async def test_private_targets_are_refused(url):
    requests: list[httpx.Request] = []
    with fake_dns({"internal.example.com": ["10.0.0.5"]}), pytest.raises(SafeFetchError):
        await fetch(url, httpx.MockTransport(image_handler(requests)))
    assert requests == []


async def test_mixed_dns_answer_is_refused():
    """One private address among public ones is enough to refuse."""
    requests: list[httpx.Request] = []
    with (
        fake_dns({"rebind.example.com": [PUBLIC_IP, "192.168.0.1"]}),
        pytest.raises(SafeFetchError),
    ):
        await fetch("http://rebind.example.com/a.png", httpx.MockTransport(image_handler(requests)))
    assert requests == []


async def test_unresolvable_host_is_refused():
    with fake_dns({}), pytest.raises(SafeFetchError):
        await fetch("http://nowhere.invalid/a.png", httpx.MockTransport(image_handler([])))


async def test_redirect_to_private_address_is_refused():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(302, headers={"Location": "http://169.254.169.254/latest"})

    with fake_dns({"cdn.example.com": [PUBLIC_IP]}), pytest.raises(SafeFetchError):
        await fetch("http://cdn.example.com/a.png", httpx.MockTransport(handler))

    # Only the first hop was requested; the redirect target was never contacted
    assert len(requests) == 1


async def test_redirect_to_public_address_is_followed_and_revalidated():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.headers["Host"] == "cdn.example.com":
            return httpx.Response(301, headers={"Location": "https://img.example.net/b.png"})
        return httpx.Response(200, headers={"Content-Type": "image/jpeg"}, content=b"jpeg")

    with fake_dns({"cdn.example.com": [PUBLIC_IP], "img.example.net": ["1.1.1.1"]}):
        result = await fetch("http://cdn.example.com/a.png", httpx.MockTransport(handler))

    assert result.content == b"jpeg"
    assert result.url == "https://img.example.net/b.png"
    assert [r.url.host for r in requests] == [PUBLIC_IP, "1.1.1.1"]


async def test_too_many_redirects():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"Location": "/again"})

    with fake_dns({"loop.example.com": [PUBLIC_IP]}), pytest.raises(SafeFetchError):
        await fetch("http://loop.example.com/a.png", httpx.MockTransport(handler), max_redirects=2)


async def test_disallowed_content_type_is_refused():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"Content-Type": "text/html"}, content=b"<html>")

    with fake_dns({"example.com": [PUBLIC_IP]}), pytest.raises(SafeFetchError):
        await fetch("http://example.com/a.png", httpx.MockTransport(handler))


async def test_content_type_parameters_are_ignored():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"Content-Type": "IMAGE/PNG; q=1"}, content=b"png")

    with fake_dns({"example.com": [PUBLIC_IP]}):
        result = await fetch("http://example.com/a.png", httpx.MockTransport(handler))
    assert result.content_type == "image/png"


async def test_body_over_size_cap_is_refused():
    with fake_dns({"example.com": [PUBLIC_IP]}), pytest.raises(SafeFetchError):
        await fetch(
            "http://example.com/a.png",
            httpx.MockTransport(image_handler([], body=b"x" * 2048)),
            max_bytes=1024,
        )


async def test_declared_length_over_size_cap_is_refused():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"Content-Type": "image/png", "Content-Length": "999999"},
            content=b"small",
        )

    with fake_dns({"example.com": [PUBLIC_IP]}), pytest.raises(SafeFetchError):
        await fetch("http://example.com/a.png", httpx.MockTransport(handler))


async def test_http_error_status_is_refused():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    with fake_dns({"example.com": [PUBLIC_IP]}), pytest.raises(SafeFetchError):
        await fetch("http://example.com/a.png", httpx.MockTransport(handler))


async def test_transport_error_is_wrapped():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out")

    with fake_dns({"example.com": [PUBLIC_IP]}), pytest.raises(SafeFetchError):
        await fetch("http://example.com/a.png", httpx.MockTransport(handler))
