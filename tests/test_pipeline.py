"""
afterglow/tests/test_pipeline.py
─────────────────────────────────
Basic unit tests for the ETL pipeline and recommender logic.

Run:
    python -m pytest tests/ -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import numpy as np
import pandas as pd
import pytest


# ── ETL tests ─────────────────────────────────────────────────────────────────

def test_pipeline_returns_dataframe():
    """ETL pipeline should return a non-empty DataFrame."""
    from src.etl.pipeline import run_pipeline
    df = run_pipeline()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0


def test_pipeline_has_required_columns():
    from src.etl.pipeline import run_pipeline
    df = run_pipeline()
    required = {"title", "overview", "genres_text", "movie_text"}
    assert required.issubset(set(df.columns))


def test_movie_text_non_empty():
    from src.etl.pipeline import run_pipeline
    df = run_pipeline()
    assert df["movie_text"].str.len().gt(0).all(), "Some movie_text fields are empty"


def test_no_duplicate_titles():
    from src.etl.pipeline import run_pipeline
    df = run_pipeline()
    assert df["title"].duplicated().sum() == 0, "Duplicate titles found"


# ── Recommender tests ─────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def engine():
    from src.etl.pipeline import run_pipeline
    from src.models.embedder import build_embeddings
    from src.models.recommender import AfterglowRecommender

    df = run_pipeline()
    embeddings = build_embeddings(df)
    return AfterglowRecommender(df, embeddings)


def test_recommend_returns_dataframe(engine):
    results = engine.recommend(intent_text="cozy rainy day film", top_k=5)
    assert isinstance(results, pd.DataFrame)
    assert len(results) == 5


def test_recommend_has_explanation(engine):
    results = engine.recommend(intent_text="something funny under 90 minutes", top_k=3)
    assert "explanation" in results.columns
    assert results["explanation"].str.len().gt(10).all()


def test_recommend_with_favourites(engine):
    results = engine.recommend(
        intent_text="hopeful romance",
        favourite_titles=["La La Land"],
        top_k=5,
    )
    # Favourite title should not appear in results
    assert "La La Land" not in results["title"].tolist()


def test_runtime_filter(engine):
    results = engine.recommend(
        intent_text="quick movie",
        max_runtime=95,
        top_k=10,
    )
    valid = results[results["runtime"] > 0]
    assert (valid["runtime"] <= 95).all(), "Runtime filter not working"


def test_rating_filter(engine):
    results = engine.recommend(
        intent_text="great film",
        min_rating=7.5,
        top_k=10,
    )
    assert (results["vote_average"] >= 7.5).all(), "Rating filter not working"


def test_scores_between_0_and_1(engine):
    results = engine.recommend(intent_text="drama", top_k=5)
    assert results["score"].between(-1, 1).all()
