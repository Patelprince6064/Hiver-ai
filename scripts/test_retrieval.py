#!/usr/bin/env python3
"""Test the retrieval system with a query.

Usage:
    python scripts/test_retrieval.py --query "My order has not arrived yet"
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval.retriever import HistoricalSupportRetriever


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config() -> dict:
    config_path = PROJECT_ROOT / "configs" / "retrieval.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Test retrieval.")
    parser.add_argument("--query", type=str, required=True, help="Query to search.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results.")
    args = parser.parse_args()

    project_root = find_project_root()
    config = load_config()
    retrieval_config = config.get("retrieval", {})

    # Load retriever
    index_dir = project_root / retrieval_config.get("index", {}).get("save_dir", "data/processed/retrieval_index")
    if not index_dir.exists():
        print("Error: Retrieval index not found.")
        print("Run: python scripts/build_retrieval_index.py")
        return 1

    retriever = HistoricalSupportRetriever(
        embedding_model=retrieval_config.get("embedding_model", {}).get("name", "sentence-transformers/all-MiniLM-L6-v2"),
        normalize_embeddings=retrieval_config.get("embedding_model", {}).get("normalize_embeddings", True),
        default_top_k=args.top_k,
    )
    retriever.load(index_dir)

    # Retrieve
    response = retriever.retrieve(args.query, top_k=args.top_k)

    # Display
    print(f"\n{'='*70}")
    print(f"Query: {args.query}")
    print(f"{'='*70}")

    if response.retrieval_status == "insufficient_evidence":
        print("\nNo results found.")
        return 0

    for result in response.results:
        print(f"\n--- Rank {result.rank} ---")
        print(f"Similarity: {result.similarity_score:.4f}")
        print(f"Intent: {result.intent or 'N/A'}")
        print(f"Resolution: {result.resolution_type or 'N/A'}")
        print(f"\nCustomer:")
        print(f"  {result.customer_message[:150]}")
        print(f"\nSupport:")
        print(f"  {result.support_response[:150]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
