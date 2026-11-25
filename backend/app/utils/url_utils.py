"""URL parsing, validation, and canonical deduplication utilities."""

from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import re
from typing import Optional

# Query parameters commonly used for tracking that should be stripped for deduplication
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "msclkid", "ref", "source", "ref_src", "feature",
    "spm", "from", "yclid", "_ga", "_gl"
}


def normalize_canonical_url(raw_url: str) -> str:
    """
    Produce a canonical URL for source deduplication.
    Strips tracking queries, fragment, trailing slashes, and lowercases scheme/host.
    """
    if not raw_url:
        return ""

    raw_url = raw_url.strip()
    try:
        parsed = urlparse(raw_url)
    except Exception:
        return raw_url

    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        return raw_url

    netloc = parsed.netloc.lower()
    # Remove default port
    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    elif netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]

    # Remove www prefix for canonical comparison if desired, but keep standard netloc
    path = parsed.path
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    # Filter tracking query parameters
    query_params = parse_qsl(parsed.query, keep_blank_values=False)
    filtered_params = [
        (k, v) for k, v in query_params
        if k.lower() not in TRACKING_PARAMS
    ]
    # Sort query params for deterministic canonical representation
    filtered_params.sort(key=lambda x: x[0])
    query = urlencode(filtered_params)

    # Reconstruct without fragment
    canonical = urlunparse((scheme, netloc, path, parsed.params, query, ""))
    return canonical


def extract_domain(url: str) -> str:
    """Extract clean domain name from URL."""
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        # Strip port if present
        domain = netloc.split(":")[0]
        # Strip leading www.
        if domain.startswith("www."):
            domain = domain[4:]
        return domain or "unknown"
    except Exception:
        return "unknown"


def is_valid_http_url(url: str) -> bool:
    """Validate that the URL is a legitimate public web URL."""
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        if not parsed.netloc or "." not in parsed.netloc:
            return False
        # Block access to localhost / link-local metadata addresses
        host = parsed.netloc.split(":")[0].lower()
        if host in ("localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254", "::1"):
            return False
        return True
    except Exception:
        return False
