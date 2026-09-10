#!/usr/bin/env python3
"""Train the semantic intent classifier.

Usage:
    python scripts/train_semantic_classifier.py
    python scripts/train_semantic_classifier.py --config configs/semantic_classifier.yaml
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.data_loader import load_train_data
from src.intents.semantic_classifier import SemanticIntentClassifier


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config(config_path: Path | None = None) -> dict:
    if config_path is None:
        config_path = PROJECT_ROOT / "configs" / "semantic_classifier.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Train semantic classifier.")
    parser.add_argument("--config", type=str, default=None, help="Config file path.")
    args = parser.parse_args()

    project_root = find_project_root()
    config = load_config(Path(args.config) if args.config else None)
    sc_config = config.get("semantic_classifier", {})

    # Load training data
    print("Loading training data...")
    train_df = load_train_data()
    print(f"Train: {len(train_df):,} examples")
    print(f"Intents: {train_df['label'].nunique()}")

    # Create cache directory
    cache_dir = project_root / sc_config.get("embedding_cache", {}).get("cache_dir", "data/interim/embeddings")

    # Train classifier
    print(f"\nTraining semantic classifier...")
    print(f"  Embedding model: {sc_config.get('embedding_model')}")
    print(f"  Classifier: {sc_config.get('classifier', {}).get('type')}")

    clf = SemanticIntentClassifier(
        embedding_model=sc_config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2"),
        normalize_embeddings=sc_config.get("normalize_embeddings", True),
        batch_size=sc_config.get("batch_size", 32),
        max_iter=sc_config.get("classifier", {}).get("max_iter", 1000),
        class_weight=sc_config.get("classifier", {}).get("class_weight", "balanced"),
        random_state=sc_config.get("classifier", {}).get("random_state", 42),
        cache_dir=cache_dir,
    )

    clf.fit(train_df["text"], train_df["label"], split_name="train")
    print("Training complete.")

    # Save model
    save_dir = project_root / sc_config.get("save_dir", "models/semantic_classifier")
    clf.save(save_dir)
    print(f"\nModel saved to: {save_dir}")

    # Print summary
    print(f"\n--- Training Summary ---")
    print(f"Embedding model: {clf.embedding_model_name}")
    print(f"Classifier: Logistic Regression")
    print(f"Classes: {len(clf.classes_)}")
    print(f"Training examples: {len(train_df)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
