#!/usr/bin/env python3
"""Build the retrieval vector index.

Usage:
    python scripts/build_retrieval_index.py
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval.embedder import RetrieverEmbedder
from src.retrieval.vector_index import VectorIndex
from src.intents.tfidf_baseline import preprocess_text


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config() -> dict:
    config_path = PROJECT_ROOT / "configs" / "retrieval.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build retrieval index.")
    args = parser.parse_args()

    project_root = find_project_root()
    config = load_config()
    retrieval_config = config.get("retrieval", {})

    # Load knowledge base
    kb_path = project_root / retrieval_config.get("data_source", {}).get("knowledge_base_path", "data/processed/knowledge_base.jsonl")
    if not kb_path.exists():
        print("Error: Knowledge base not found.")
        print("Run: python scripts/build_knowledge_base.py")
        return 1

    records = []
    with open(kb_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    print(f"Loaded {len(records):,} knowledge records")

    # Apply quality filters
    quality_config = retrieval_config.get("quality_filter", {})
    exclude_flags = quality_config.get("exclude", [])

    filtered_records = []
    for record in records:
        flags = record.get("quality_flags", [])
        if any(f in flags for f in exclude_flags):
            continue
        filtered_records.append(record)

    print(f"After quality filter: {len(filtered_records):,} records")

    # Get retrieval texts
    texts = [preprocess_text(r.get("resolution_text", "")) for r in filtered_records]
    knowledge_ids = [r.get("knowledge_id", "") for i, r in enumerate(filtered_records)]

    # Build embeddings
    print("\nBuilding embeddings...")
    embedding_config = retrieval_config.get("embedding_model", {})
    embedder = RetrieverEmbedder(
        model_name=embedding_config.get("name", "sentence-transformers/all-MiniLM-L6-v2"),
        normalize=embedding_config.get("normalize_embeddings", True),
        batch_size=embedding_config.get("batch_size", 32),
    )

    embeddings = embedder.encode_documents(texts)
    print(f"Embeddings shape: {embeddings.shape}")

    # Build index
    print("\nBuilding FAISS index...")
    index = VectorIndex(
        dimension=embeddings.shape[1],
        metric=retrieval_config.get("index", {}).get("metric", "cosine"),
    )
    index.build(embeddings, knowledge_ids)
    print(f"Index size: {index.size()}")

    # Save index
    save_dir = project_root / retrieval_config.get("index", {}).get("save_dir", "data/processed/retrieval_index")
    index.save(save_dir)

    # Save records for retriever
    records_path = save_dir / "records.jsonl"
    with open(records_path, "w", encoding="utf-8") as f:
        for record in filtered_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # Save metadata
    metadata = {
        "embedding_model": embedding_config.get("name", "sentence-transformers/all-MiniLM-L6-v2"),
        "normalize_embeddings": embedding_config.get("normalize_embeddings", True),
        "embedding_dimension": int(embeddings.shape[1]),
        "similarity_metric": retrieval_config.get("index", {}).get("metric", "cosine"),
        "index_type": retrieval_config.get("index", {}).get("type", "IndexFlatIP"),
        "n_indexed_records": len(filtered_records),
        "n_total_records": len(records),
        "quality_filter_excluded": len(records) - len(filtered_records),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "seed": retrieval_config.get("seed", 42),
    }
    index.save_metadata(save_dir, metadata)

    print(f"\nIndex saved to: {save_dir}")
    print(f"Metadata saved to: {save_dir / 'index_metadata.json'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
