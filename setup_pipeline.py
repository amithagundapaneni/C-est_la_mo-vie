"""
afterglow/setup_pipeline.py
────────────────────────────
One-time setup: run ETL → build embeddings → cluster movies.
Run from the project root:

    python setup_pipeline.py

Flags:
    --force   Re-run even if cached outputs exist.
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")


def main(force: bool = False) -> None:
    from src.etl.pipeline import run_pipeline
    from src.models.embedder import build_embeddings
    from src.models.recommender import build_clusters

    print("\n" + "═" * 55)
    print("  🎬  AFTERGLOW  —  Setup Pipeline")
    print("═" * 55 + "\n")

    print("Step 1/3  ETL …")
    df = run_pipeline(force=force)
    print(f"          ✓ {len(df):,} movies loaded\n")

    print("Step 2/3  Embedding …")
    embeddings = build_embeddings(df, force=force)
    print(f"          ✓ Embeddings shape: {embeddings.shape}\n")

    print("Step 3/3  Clustering …")
    labels = build_clusters(embeddings, force=force)
    print(f"          ✓ {len(set(labels))} vibe clusters created\n")

    print("═" * 55)
    print("  Setup complete!  Run the app with:")
    print("  streamlit run app/streamlit_app.py")
    print("═" * 55 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Re-run even if cache exists")
    args = parser.parse_args()
    main(force=args.force)
