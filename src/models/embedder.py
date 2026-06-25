"""
afterglow/src/models/embedder.py
────────────────────────────────
Embedding Pipeline

Uses sentence-transformers (all-MiniLM-L6-v2) to encode every movie's
`movie_text` field into a 384-dimensional dense vector.

Embeddings are saved to data/processed/embeddings.npy and an index
mapping row → title to data/processed/movie_index.parquet.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

log = logging.getLogger(__name__)

PROCESSED_DIR = Path(__file__).parents[2] / "data" / "processed"
EMBEDDINGS_PATH = PROCESSED_DIR / "embeddings.npy"
INDEX_PATH = PROCESSED_DIR / "movie_index.parquet"

MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 64


def build_embeddings(df: pd.DataFrame, force: bool = False) -> np.ndarray:
    """
    Generate sentence embeddings for every movie in `df`.

    Args:
        df:     Master DataFrame (must contain `movie_text` column).
        force:  Re-encode even if cached embeddings exist.

    Returns:
        embeddings  – np.ndarray of shape (N, 384)
    """
    if EMBEDDINGS_PATH.exists() and INDEX_PATH.exists() and not force:
        log.info("Embeddings cache found. Loading …")
        return np.load(EMBEDDINGS_PATH)

    log.info(f"Loading sentence-transformer model: {MODEL_NAME} …")
    # Lazy import so the rest of the app starts fast without torch
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(MODEL_NAME)

    texts = df["movie_text"].tolist()
    log.info(f"Encoding {len(texts):,} movies in batches of {BATCH_SIZE} …")

    all_embeddings = []
    for i in tqdm(range(0, len(texts), BATCH_SIZE), desc="Embedding"):
        batch = texts[i : i + BATCH_SIZE]
        embs = model.encode(batch, show_progress_bar=False, normalize_embeddings=True)
        all_embeddings.append(embs)

    embeddings = np.vstack(all_embeddings).astype(np.float32)

    # Save
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    np.save(EMBEDDINGS_PATH, embeddings)
    df[["title", "genres_text", "keywords_text", "vote_average", "runtime"]].to_parquet(
        INDEX_PATH, index=True
    )
    log.info(f"Saved embeddings → {EMBEDDINGS_PATH}  shape={embeddings.shape}")
    return embeddings


def embed_text(text: str) -> np.ndarray:
    """
    Embed a single free-form text string (for query / intent encoding).

    Returns:
        np.ndarray of shape (384,)  – L2-normalised
    """
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(MODEL_NAME)
    vec = model.encode([text], normalize_embeddings=True)[0]
    return vec.astype(np.float32)


def load_embeddings() -> np.ndarray:
    """Load pre-computed embeddings from disk."""
    if not EMBEDDINGS_PATH.exists():
        raise FileNotFoundError(
            "Embeddings not found. Run: python -m src.models.embedder"
        )
    return np.load(EMBEDDINGS_PATH)


if __name__ == "__main__":
    from src.etl.pipeline import run_pipeline

    df = run_pipeline()
    build_embeddings(df, force=True)
