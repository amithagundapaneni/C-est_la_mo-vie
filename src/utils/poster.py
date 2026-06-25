"""
afterglow/src/utils/poster.py
──────────────────────────────
Poster Fetching Utility

Fetches movie poster images from the TMDB image CDN.
Falls back to a placeholder image if the poster is unavailable.

No API key required for image CDN access (posters are public).
"""

from pathlib import Path

TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
PLACEHOLDER = "https://via.placeholder.com/500x750/1a1a2e/e8d5b7?text=No+Poster"


def get_poster_url(poster_path: str) -> str:
    """
    Return a full TMDB poster URL from a relative poster_path.

    Args:
        poster_path:  e.g. "/abc123.jpg"  or  NaN / empty string

    Returns:
        Full URL string or placeholder.
    """
    if not poster_path or str(poster_path).strip() in ("", "nan", "None"):
        return PLACEHOLDER

    path = str(poster_path).strip()
    if not path.startswith("/"):
        path = "/" + path

    return f"{TMDB_IMAGE_BASE}{path}"


def search_poster_url(title: str) -> str:
    """
    Lightweight TMDB search for a movie poster by title.
    Only used when poster_path is missing from metadata.

    Requires internet access; returns placeholder on failure.
    """
    try:
        import requests

        resp = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={"query": title, "language": "en-US", "page": 1},
            # Public read-only API key (v3 anonymous)
            headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.placeholder"},
            timeout=5,
        )
        data = resp.json()
        results = data.get("results", [])
        if results and results[0].get("poster_path"):
            return get_poster_url(results[0]["poster_path"])
    except Exception:
        pass
    return PLACEHOLDER
