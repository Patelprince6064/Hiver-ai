#!/usr/bin/env python3
"""Validate the retrieval index.

Usage:
    python scripts/validate_retrieval_index.py
"""

import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config() -> dict:
    config_path = PROJECT_ROOT / "configs" / "retrieval.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main() -> int:
    project_root = find_project_root()
    config = load_config()
    retrieval_config = config.get("retrieval", {})

    index_dir = project_root / retrieval_config.get("index", {}).get("save_dir", "data/processed/retrieval_index")

    # Check index exists
    index_path = index_dir / "index.faiss"
    if not index_path.exists():
        print("Error: Index file not found.")
        return 1

    # Load metadata
    metadata_path = index_dir / "index_metadata.json"
    if not metadata_path.exists():
        print("Error: Metadata file not found.")
        return 1

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    # Load mapping
    mapping_path = index_dir / "record_mapping.json"
    if not mapping_path.exists():
        print("Error: Record mapping not found.")
        return 1

    with open(mapping_path, "r") as f:
        mapping = json.load(f)

    # Validate
    print(f"{'='*70}")
    print("RETRIEVAL INDEX VALIDATION")
    print(f"{'='*70}")

    checks = []

    # Check index size
    from src.retrieval.vector_index import VectorIndex
    index = VectorIndex(dimension=metadata.get("embedding_dimension", 384))
    index.load(index_dir)
    index_size = index.size()
    mapping_size = len(mapping)

    if index_size == mapping_size:
        checks.append(("Index/mapping size match", True, f"{index_size} records"))
    else:
        checks.append(("Index/mapping size match", False, f"Index: {index_size}, Mapping: {mapping_size}"))

    # Check unique IDs
    unique_ids = len(set(mapping))
    if unique_ids == mapping_size:
        checks.append(("Knowledge IDs unique", True, f"{unique_ids} unique IDs"))
    else:
        checks.append(("Knowledge IDs unique", False, f"{unique_ids} unique vs {mapping_size} total"))

    # Check metadata
    if metadata.get("embedding_model"):
        checks.append(("Embedding model", True, metadata["embedding_model"]))
    else:
        checks.append(("Embedding model", False, "Missing"))

    if metadata.get("embedding_dimension"):
        checks.append(("Embedding dimension", True, str(metadata["embedding_dimension"])))
    else:
        checks.append(("Embedding dimension", False, "Missing"))

    # Print results
    all_passed = True
    for check_name, passed, detail in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {check_name}: {detail}")
        if not passed:
            all_passed = False

    if all_passed:
        print(f"\n✓ Validation PASSED.")
        return 0
    else:
        print(f"\n✗ Validation FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
