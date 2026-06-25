"""
afterglow/src/models/recommender.py
────────────────────────────────────
Hybrid Recommendation Engine

Combines:
  A) Taste Profile  (40%)  – average embedding of user's favourite movies
  B) Viewing Intent (60%)  – embedding of the user's natural-language prompt

Uses cosine similarity (embeddings are L2-normalised, so dot product == cosine).

Also supports:
  • KMeans vibe-cluster filtering
  • Runtime / rating filters
  • Rule-based explanation generation
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

log = logging.getLogger(__name__)

PROCESSED_DIR = Path(__file__).parents[2] / "data" / "processed"
CLUSTER_PATH = PROCESSED_DIR / "cluster_labels.npy"

# Blend weights
INTENT_WEIGHT = 0.60
TASTE_WEIGHT = 0.40

# Vibe cluster names (assigned heuristically after fitting)
VIBE_NAMES = {
    0: "Comfort Movies",
    1: "Heartbreak Cinema",
    2: "Coming-of-Age",
    3: "Existential Sci-Fi",
    4: "Feel-Good Comedy",
    5: "Action & Adrenaline",
    6: "Dark Thrillers",
    7: "Epic Adventures",
    8: "Romantic Dramas",
    9: "Indie & Arthouse",
}

N_CLUSTERS = len(VIBE_NAMES)


# ── Cluster utilities ─────────────────────────────────────────────────────────

def build_clusters(embeddings: np.ndarray, force: bool = False) -> np.ndarray:
    """Fit KMeans and persist cluster labels."""
    if CLUSTER_PATH.exists() and not force:
        return np.load(CLUSTER_PATH)

    log.info(f"Fitting KMeans with {N_CLUSTERS} clusters …")
    km = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    labels = km.fit_predict(embeddings)
    np.save(CLUSTER_PATH, labels)
    log.info("Cluster labels saved.")
    return labels


def load_clusters() -> Optional[np.ndarray]:
    if CLUSTER_PATH.exists():
        return np.load(CLUSTER_PATH)
    return None


# ── Core engine ───────────────────────────────────────────────────────────────

class AfterglowRecommender:
    """
    Main recommendation engine.

    Usage:
        engine = AfterglowRecommender(df, embeddings)
        results = engine.recommend(
            favourite_titles=["La La Land", "Past Lives"],
            intent_text="hopeful romantic movie not emotionally devastating",
            top_k=10,
        )
    """

    def __init__(self, df: pd.DataFrame, embeddings: np.ndarray):
        self.df = df.reset_index(drop=True)
        self.embeddings = embeddings  # shape (N, D), already L2-normalised
        self.title_to_idx: dict[str, int] = {
            t.lower(): i for i, t in enumerate(df["title"])
        }
        self.cluster_labels = load_clusters()

    # ── Taste profile ─────────────────────────────────────────────────────────

    def _taste_embedding(self, favourite_titles: list[str]) -> Optional[np.ndarray]:
        """Average embeddings of known favourite movies."""
        indices = []
        for t in favourite_titles:
            idx = self.title_to_idx.get(t.strip().lower())
            if idx is not None:
                indices.append(idx)
            else:
                # Fuzzy: partial match
                for key, i in self.title_to_idx.items():
                    if t.strip().lower() in key:
                        indices.append(i)
                        break

        if not indices:
            return None

        avg = self.embeddings[indices].mean(axis=0)
        norm = np.linalg.norm(avg)
        return avg / norm if norm > 0 else avg

    # ── Scoring ───────────────────────────────────────────────────────────────

    def _score(
        self,
        taste_vec: Optional[np.ndarray],
        intent_vec: np.ndarray,
    ) -> np.ndarray:
        """Compute blended cosine similarity scores for all movies."""
        intent_scores = self.embeddings @ intent_vec  # (N,)

        if taste_vec is not None:
            taste_scores = self.embeddings @ taste_vec  # (N,)
            scores = INTENT_WEIGHT * intent_scores + TASTE_WEIGHT * taste_scores
        else:
            scores = intent_scores

        return scores

    # ── Filters ───────────────────────────────────────────────────────────────

    def _apply_filters(
        self,
        scores: np.ndarray,
        exclude_titles: list[str],
        max_runtime: Optional[int],
        min_rating: float,
    ) -> np.ndarray:
        """Zero out scores for movies that don't pass filters."""
        filtered = scores.copy()

        # Exclude favourites from results
        for t in exclude_titles:
            idx = self.title_to_idx.get(t.strip().lower())
            if idx is not None:
                filtered[idx] = -1.0

        # Runtime filter
        if max_runtime and "runtime" in self.df.columns:
            mask = (self.df["runtime"] > max_runtime) | (self.df["runtime"] == 0)
            filtered[mask.values] = -1.0

        # Rating filter
        if "vote_average" in self.df.columns:
            low_rated = self.df["vote_average"] < min_rating
            filtered[low_rated.values] = -1.0

        return filtered

    # ── Explanation generator ─────────────────────────────────────────────────

    def _explain(
        self,
        row: pd.Series,
        score: float,
        intent_text: str,
        favourite_titles: list[str],
    ) -> str:
        """Rule-based human-readable explanation (no external LLM needed)."""
        title = row["title"]
        genres = str(row.get("genres_text", "")).strip()
        keywords = str(row.get("keywords_text", "")).strip()

        # Pick a genre phrase
        genre_list = genres.split()[:3]
        genre_phrase = " / ".join(genre_list) if genre_list else "this genre"

        # Cluster vibe
        vibe = ""
        if self.cluster_labels is not None:
            idx = self.title_to_idx.get(title.lower())
            if idx is not None:
                cluster_id = int(self.cluster_labels[idx])
                vibe = VIBE_NAMES.get(cluster_id, "")

        # Build sentence
        parts = [f'**{title}** fits your request for "{intent_text[:60]}…"']

        if genre_phrase:
            parts.append(f"It belongs to the {genre_phrase} space")

        if vibe:
            parts.append(f'and sits in the "{vibe}" vibe cluster')

        if favourite_titles:
            fav = favourite_titles[0]
            parts.append(
                f"Fans of *{fav}* consistently enjoy this film"
            )

        rating = row.get("vote_average", 0)
        if rating >= 7.5:
            parts.append(f"with a strong audience rating of {rating:.1f}/10")

        return ". ".join(parts) + "."

    # ── Main recommend method ─────────────────────────────────────────────────

    def recommend(
        self,
        intent_text: str,
        favourite_titles: Optional[list[str]] = None,
        top_k: int = 10,
        max_runtime: Optional[int] = None,
        min_rating: float = 5.0,
    ) -> pd.DataFrame:
        """
        Generate top-k movie recommendations.

        Args:
            intent_text:       Free-form description of what the user wants now.
            favourite_titles:  List of movies the user loves (can be empty).
            top_k:             Number of recommendations to return.
            max_runtime:       Optional upper bound on runtime in minutes.
            min_rating:        Minimum vote_average threshold.

        Returns:
            DataFrame with columns:
                title, genres_text, overview, vote_average, runtime,
                score, explanation, poster_path
        """
        from src.models.embedder import embed_text

        favourite_titles = favourite_titles or []

        # Encode intent
        intent_vec = embed_text(intent_text)

        # Build taste profile
        taste_vec = self._taste_embedding(favourite_titles) if favourite_titles else None

        # Score
        scores = self._score(taste_vec, intent_vec)

        # Filter
        scores = self._apply_filters(
            scores,
            exclude_titles=favourite_titles,
            max_runtime=max_runtime,
            min_rating=min_rating,
        )

        # Top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            row = self.df.iloc[idx]
            explanation = self._explain(row, scores[idx], intent_text, favourite_titles)
            results.append(
                {
                    "title": row["title"],
                    "genres_text": row.get("genres_text", ""),
                    "overview": row.get("overview", ""),
                    "vote_average": row.get("vote_average", 0),
                    "runtime": row.get("runtime", 0),
                    "release_date": row.get("release_date", ""),
                    "poster_path": row.get("poster_path", ""),
                    "score": round(float(scores[idx]), 4),
                    "explanation": explanation,
                    "vibe": VIBE_NAMES.get(
                        int(self.cluster_labels[idx]) if self.cluster_labels is not None else -1,
                        "",
                    ),
                }
            )

        return pd.DataFrame(results)


# ── CLI helper ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from src.etl.pipeline import run_pipeline
    from src.models.embedder import build_embeddings, load_embeddings

    df = run_pipeline()
    embeddings = build_embeddings(df)
    build_clusters(embeddings)

    engine = AfterglowRecommender(df, embeddings)
    recs = engine.recommend(
        intent_text="cozy rainy day comfort film",
        favourite_titles=["La La Land"],
        top_k=5,
    )
    print(recs[["title", "score", "explanation"]].to_string())
