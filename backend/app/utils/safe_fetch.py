"""
Safe outbound HTTP fetching (SSRF guard).

Every server-side fetch of a user-supplied URL goes through `safe_fetch`:

- only http and https URLs are accepted;
- the host is resolved and every resolved address must be public: private, loopback,
  link-local (including cloud metadata), shared, reserved, multicast and unspecified
  ranges are refused for IPv4 and IPv6, and IPv4-mapped IPv6 addresses are unwrapped;
- the connection goes to the address that was checked (the URL host is replaced by the
  IP, with the original name kept in the Host header and as the TLS SNI/verification
  name), so a second DNS lookup cannot swap in a different address;
- redirects are never followed automatically; each hop is re-validated, up to a limit;
- the body is streamed and aborted past a size cap, with a timeout and a content-type
  allowlist.
"""

import asyncio
import ipaddress
import socket
from collections.abc import Iterable
from dataclasses import dataclass

import httpx

from app.core.constants import SAFE_FETCH_MAX_REDIRECTS, SAFE_FETCH_TIMEOUT_SECONDS


IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address

_ALLOWED_SCHEMES = {"http", "https"}
_DEFAULT_PORTS = {"http": 80, "https": 443}
_USER_AGENT = "Mozilla/5.0 (compatible; RecipeCatalog/1.0)"


class SafeFetchError(Exception):
    """Raised when a URL is refused or the fetch fails."""


@dataclass(frozen=True)
class FetchResult:
    """A successfully fetched response body."""

    url: str
    content: bytes
    content_type: str


def is_public_address(ip: IPAddress) -> bool:
    """Return True only for globally routable unicast addresses."""
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return ip.is_global and not ip.is_multicast


async def _resolve(host: str, port: int) -> list[IPAddress]:
    """Resolve a host name to its IP addresses without blocking the event loop."""
    loop = asyncio.get_running_loop()
    infos = await loop.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    addresses: list[IPAddress] = []
    for info in infos:
        # sockaddr[0] is the address; IPv6 link-local results may carry a "%scope" suffix
        address = ipaddress.ip_address(str(info[4][0]).split("%", 1)[0])
        if address not in addresses:
            addresses.append(address)
    return addresses


async def _resolve_public_address(host: str, port: int) -> IPAddress:
    """Resolve `host` and return an address to connect to, refusing non-public ones."""
    try:
        literal: IPAddress | None = ipaddress.ip_address(host)
    except ValueError:
        literal = None

    if literal is not None:
        addresses = [literal]
    else:
        try:
            addresses = await _resolve(host, port)
        except (OSError, UnicodeError) as e:
            raise SafeFetchError(f"Could not resolve host {host!r}") from e

    if not addresses:
        raise SafeFetchError(f"Could not resolve host {host!r}")

    # Refuse if any address is non-public, so a mixed DNS answer cannot be used to reach
    # an internal service.
    for address in addresses:
        if not is_public_address(address):
            raise SafeFetchError(f"Refusing to fetch from non-public address {address}")

    return addresses[0]


def _normalize_content_type(value: str) -> str:
    return value.split(";", 1)[0].strip().lower()


async def safe_fetch(
    url: str,
    *,
    max_bytes: int,
    allowed_content_types: Iterable[str],
    timeout: float = SAFE_FETCH_TIMEOUT_SECONDS,
    max_redirects: int = SAFE_FETCH_MAX_REDIRECTS,
    transport: httpx.AsyncBaseTransport | None = None,
) -> FetchResult:
    """
    Fetch `url` under the SSRF rules described in the module docstring.

    Args:
        url: Absolute http(s) URL to fetch
        max_bytes: Maximum response body size in bytes
        allowed_content_types: Accepted MIME types (parameters such as charset are ignored)
        timeout: Timeout in seconds for each request
        max_redirects: Maximum number of redirects to follow, each one re-validated
        transport: Optional httpx transport (tests only)

    Returns:
        FetchResult with the final URL, body and normalized content type

    Raises:
        SafeFetchError: If the URL is refused or the fetch fails for any reason
    """
    allowed = {_normalize_content_type(t) for t in allowed_content_types}
    current_url = url

    # trust_env=False: an environment proxy would make the connection somewhere other
    # than the address checked here.
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=False,
        trust_env=False,
        transport=transport,
    ) as client:
        for _ in range(max_redirects + 1):
            try:
                parsed = httpx.URL(current_url)
            except (httpx.InvalidURL, TypeError) as e:
                raise SafeFetchError("Invalid URL") from e

            if parsed.scheme not in _ALLOWED_SCHEMES:
                raise SafeFetchError(f"Unsupported URL scheme {parsed.scheme!r}")
            if not parsed.host:
                raise SafeFetchError("URL has no host")

            port = parsed.port or _DEFAULT_PORTS[parsed.scheme]
            address = await _resolve_public_address(parsed.host, port)

            pinned_url = parsed.copy_with(host=str(address))
            extensions = {}
            if parsed.scheme == "https":
                # Verify the certificate against the name, not the pinned IP
                extensions["sni_hostname"] = parsed.host

            request = client.build_request(
                "GET",
                pinned_url,
                headers={
                    "Host": parsed.netloc.decode("ascii"),
                    "User-Agent": _USER_AGENT,
                    "Accept": ", ".join(sorted(allowed)) or "*/*",
                },
                extensions=extensions,
            )

            try:
                response = await client.send(request, stream=True)
            except httpx.HTTPError as e:
                raise SafeFetchError(f"Request failed: {e.__class__.__name__}") from e

            try:
                if response.is_redirect:
                    location = response.headers.get("Location")
                    if not location:
                        raise SafeFetchError("Redirect without a Location header")
                    current_url = str(parsed.join(location))
                    continue

                if response.status_code >= 400:
                    raise SafeFetchError(f"Upstream returned HTTP {response.status_code}")

                content_type = _normalize_content_type(response.headers.get("Content-Type", ""))
                if content_type not in allowed:
                    raise SafeFetchError(f"Content type {content_type!r} is not allowed")

                declared_length = response.headers.get("Content-Length")
                if (
                    declared_length
                    and declared_length.isdigit()
                    and int(declared_length) > max_bytes
                ):
                    raise SafeFetchError("Response exceeds the size limit")

                body = bytearray()
                try:
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > max_bytes:
                            raise SafeFetchError("Response exceeds the size limit")
                except httpx.HTTPError as e:
                    raise SafeFetchError(f"Request failed: {e.__class__.__name__}") from e

                return FetchResult(url=str(parsed), content=bytes(body), content_type=content_type)
            finally:
                await response.aclose()

    raise SafeFetchError("Too many redirects")
