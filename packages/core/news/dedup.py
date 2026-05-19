"""URL canonicalization + stable article id derivation.

Used by the RSS adapter to dedup articles whose URLs differ only by tracking params.
"""

from __future__ import annotations

import hashlib
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

_TRACKING_PARAMS: frozenset[str] = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "utm_id",
        "fbclid",
        "gclid",
        "mc_cid",
        "mc_eid",
        "ref",
        "ref_src",
    }
)


def canonical_url(raw: str) -> str:
    """Return canonical form. Strip tracking params, fragment, trailing slash. Lowercase host."""
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("url must be non-empty string")
    parsed = urlparse(raw.strip())
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"invalid url: {raw!r}")

    host = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or "/"

    pairs = parse_qsl(parsed.query, keep_blank_values=False)
    cleaned = [(k, v) for k, v in pairs if k.lower() not in _TRACKING_PARAMS]
    query = urlencode(sorted(cleaned))

    return urlunparse((parsed.scheme.lower(), host, path, "", query, ""))


def article_id(canonical: str) -> int:
    """Stable 60-bit BIGINT id derived from sha1(canonical_url). DuckDB BIGINT safe."""
    digest = hashlib.sha1(canonical.encode("utf-8"), usedforsecurity=False).hexdigest()
    return int(digest[:15], 16)
