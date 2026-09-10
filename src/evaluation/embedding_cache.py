"""Embedding cache for sentence-transformer embeddings.

Provides deterministic caching tied to dataset identity,
preprocessing version, and embedding model configuration.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _compute_cache_key(
    texts: list[str],
    embedding_model: str,
    normalize: bool,
    split_name: str,
) -> str:
    """Compute a deterministic cache key for the embedding configuration."""
    text_hash = hashlib.sha256("\n".join(texts).encode("utf-8")).hexdigest()[:16]
    config_str = f"{embedding_model}|{normalize}|{split_name}|{text_hash}"
    return hashlib.sha256(config_str.encode("utf-8")).hexdigest()[:32]


def get_cache_path(
    cache_dir: Path,
    split_name: str,
    embedding_model: str,
) -> Path:
    """Get the file path for a cached embedding file."""
    model_short = embedding_model.split("/")[-1]
    return cache_dir / f"{split_name}_{model_short}.npy"


def get_metadata_path(
    cache_dir: Path,
    split_name: str,
    embedding_model: str,
) -> Path:
    """Get the metadata path for a cached embedding."""
    model_short = embedding_model.split("/")[-1]
    return cache_dir / f"{split_name}_{model_short}_metadata.json"


def load_cache(
    cache_dir: Path,
    split_name: str,
    embedding_model: str,
    normalize: bool,
    texts: list[str],
) -> np.ndarray | None:
    """Load cached embeddings if valid.

    Returns None if cache is stale or missing.
    """
    cache_path = get_cache_path(cache_dir, split_name, embedding_model)
    metadata_path = get_metadata_path(cache_dir, split_name, embedding_model)

    if not cache_path.exists() or not metadata_path.exists():
        return None

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    # Validate cache
    expected_key = _compute_cache_key(texts, embedding_model, normalize, split_name)
    if metadata.get("cache_key") != expected_key:
        return None
    if metadata.get("n_examples") != len(texts):
        return None

    return np.load(cache_path)


def save_cache(
    embeddings: np.ndarray,
    cache_dir: Path,
    split_name: str,
    embedding_model: str,
    normalize: bool,
    texts: list[str],
) -> Path:
    """Save embeddings to cache."""
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_path = get_cache_path(cache_dir, split_name, embedding_model)
    metadata_path = get_metadata_path(cache_dir, split_name, embedding_model)

    np.save(cache_path, embeddings)

    cache_key = _compute_cache_key(texts, embedding_model, normalize, split_name)
    metadata = {
        "cache_key": cache_key,
        "embedding_model": embedding_model,
        "normalize": normalize,
        "split_name": split_name,
        "n_examples": len(texts),
        "embedding_dim": embeddings.shape[1] if embeddings.ndim > 1 else 0,
    }

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return cache_path
