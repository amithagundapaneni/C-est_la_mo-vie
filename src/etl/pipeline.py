"""
afterglow/src/etl/pipeline.py
─────────────────────────────
Data Engineering Pipeline

Loads data/raw/movie_data.csv with columns:
    adult, backdrop_path, movie_id, original_language, original_title,
    overview, popularity, poster_path, release_date, title, video,
    vote_average, vote_count, genres, keywords, cast, crew

Falls back to data/sample_movies.json if the CSV is missing.
"""

import ast
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

RAW_DIR       = Path(__file__).parents[2] / "data" / "raw"
PROCESSED_DIR = Path(__file__).parents[2] / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

MASTER_PATH  = PROCESSED_DIR / "master_movies.parquet"
CSV_PATH = Path(__file__).parents[2] / "data" / "movie_data.csv"
SAMPLE_PATH  = Path(__file__).parents[2] / "data" / "sample_movies.json"


# ── Parsers ───────────────────────────────────────────────────────────────────

def _parse_names(value, key: str = "name", limit: int = 0) -> str:
    """
    Parse a JSON-like list-of-dicts string and return space-joined values
    for `key`.  Returns "" on any failure.
    """
    if pd.isna(value) or str(value).strip() in ("", "[]", "nan"):
        return ""
    try:
        items = ast.literal_eval(str(value))
        if not isinstance(items, list):
            return ""
        names = [str(i[key]) for i in items if isinstance(i, dict) and key in i]
        if limit:
            names = names[:limit]
        return " ".join(names)
    except Exception:
        return ""


def _parse_cast(value, limit: int = 5) -> str:
    return _parse_names(value, key="name", limit=limit)


def _parse_genres(value) -> str:
    return _parse_names(value, key="name")


def _parse_keywords(value) -> str:
    return _parse_names(value, key="name")


# ── movie_text builder ────────────────────────────────────────────────────────

def _build_movie_text(row: pd.Series) -> str:
    parts = []
    title    = str(row.get("title", "")).strip()
    genres   = str(row.get("genres_text", "")).strip()
    keywords = str(row.get("keywords_text", "")).strip()
    overview = str(row.get("overview", "")).strip()
    cast     = str(row.get("cast_text", "")).strip()

    if title:
        parts.append(f"Title: {title}")
    if genres:
        parts.append(f"Genres: {genres}")
    if keywords:
        parts.append(f"Keywords: {keywords}")
    if overview:
        parts.append(f"Overview: {overview}")
    if cast:
        parts.append(f"Cast: {cast}")

    return ". ".join(parts)


# ── Loaders ───────────────────────────────────────────────────────────────────

def _load_movie_data() -> pd.DataFrame | None:
    if not CSV_PATH.exists():
        return None

    log.info(f"Loading {CSV_PATH.name} ...")
    df = pd.read_csv(
    CSV_PATH,
    engine="python",
    on_bad_lines="skip",
)
    log.info(f"  Raw rows: {len(df):,}  |  Columns: {list(df.columns)}")

    # Normalise the ID column
    if "movie_id" in df.columns:
        df = df.rename(columns={"movie_id": "tmdb_id"})

    # Parse JSON-like columns
    df["genres_text"]   = df["genres"].apply(_parse_genres)    if "genres"   in df.columns else ""
    df["keywords_text"] = df["keywords"].apply(_parse_keywords) if "keywords" in df.columns else ""
    df["cast_text"]     = df["cast"].apply(_parse_cast)         if "cast"     in df.columns else ""

    df["source"] = "movie_data"
    return df


def _load_sample() -> pd.DataFrame:
    log.warning(
        "data/raw/movie_data.csv not found. "
        "Using built-in sample. Drop the CSV into data/raw/ for full results."
    )
    if SAMPLE_PATH.exists():
        df = pd.read_json(SAMPLE_PATH)
        for col in ("genres_text", "keywords_text", "cast_text"):
            if col not in df.columns:
                df[col] = ""
        df["source"] = "sample"
        return df

    # Absolute minimum hard-coded fallback
    return pd.DataFrame([
        {
            "title": "La La Land",
            "overview": "A jazz musician and an aspiring actress fall in love in Los Angeles.",
            "genres_text": "Romance Drama Music",
            "keywords_text": "dreams jazz love ambition",
            "cast_text": "Ryan Gosling Emma Stone",
            "vote_average": 8.0, "runtime": 128,
            "release_date": "2016-12-09", "source": "fallback",
        },
        {
            "title": "Interstellar",
            "overview": "A team of explorers travel through a wormhole in space.",
            "genres_text": "Science Fiction Adventure Drama",
            "keywords_text": "space wormhole survival father daughter",
            "cast_text": "Matthew McConaughey Anne Hathaway",
            "vote_average": 8.6, "runtime": 169,
            "release_date": "2014-11-07", "source": "fallback",
        },
    ])


# ── Master pipeline ───────────────────────────────────────────────────────────

KEEP_COLS = [
    "tmdb_id", "title", "overview",
    "genres_text", "keywords_text", "cast_text",
    "vote_average", "runtime", "release_date",
    "poster_path", "source", "movie_text",
]


def run_pipeline(force: bool = False) -> pd.DataFrame:
    """
    Execute the full ETL pipeline and return the master DataFrame.

    Args:
        force: Re-run even if processed output already exists.

    Returns:
        Cleaned DataFrame ready for embedding.
    """
    if MASTER_PATH.exists() and not force:
        log.info("Processed data found. Loading from cache ...")
        return pd.read_parquet(MASTER_PATH)

    # 1. Load
    df = _load_movie_data()
    if df is None:
        df = _load_sample()

    log.info(f"Loaded {len(df):,} rows before cleaning.")

    # 2. Ensure required columns exist
    for col in ("tmdb_id", "poster_path", "runtime"):
        if col not in df.columns:
            df[col] = np.nan

    # 3. Clean
    df["title"]         = df["title"].astype(str).str.strip()
    df["overview"]      = df.get("overview", pd.Series([""] * len(df))).fillna("").astype(str).str.strip()
    df["genres_text"]   = df["genres_text"].fillna("").astype(str)
    df["keywords_text"] = df["keywords_text"].fillna("").astype(str)
    df["cast_text"]     = df["cast_text"].fillna("").astype(str)
    df["vote_average"]  = pd.to_numeric(df.get("vote_average", 0), errors="coerce").fillna(0.0)
    df["runtime"]       = pd.to_numeric(df.get("runtime", 0), errors="coerce").fillna(0.0)

    # 4. Drop rows without usable title or overview
    df = df[df["title"].str.len() > 1]
    df = df[df["overview"].str.len() > 20]

    # 5. Deduplicate — keep highest-rated entry per title
    df = df.sort_values("vote_average", ascending=False)
    df = df.drop_duplicates(subset=["title"], keep="first").reset_index(drop=True)

    # 6. Build movie_text
    df["movie_text"] = df.apply(_build_movie_text, axis=1)

    # 7. Select output columns
    existing = [c for c in KEEP_COLS if c in df.columns]
    df = df[existing].copy()

    log.info(f"Master dataset: {len(df):,} movies.")

    # 8. Persist
    df.to_parquet(MASTER_PATH, index=False)
    log.info(f"Saved -> {MASTER_PATH}")

    return df


if __name__ == "__main__":
    run_pipeline(force=True)
