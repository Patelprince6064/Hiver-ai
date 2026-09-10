"""Vector index for semantic retrieval.

Provides FAISS-based vector indexing and search.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


class VectorIndex:
    """FAISS-based vector index for retrieval."""

    def __init__(self, dimension: int, metric: str = "cosine") -> None:
        self.dimension = dimension
        self.metric = metric
        self._index = None
        self._record_mapping: list[str] = []

    def build(self, embeddings: np.ndarray, knowledge_ids: list[str]) -> None:
        """Build the index from embeddings."""
        import faiss

        if self.metric == "cosine":
            # For cosine similarity with normalized vectors, use inner product
            self._index = faiss.IndexFlatIP(self.dimension)
        else:
            self._index = faiss.IndexFlatL2(self.dimension)

        self._record_mapping = knowledge_ids
        self._index.add(embeddings.astype(np.float32))

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[tuple[str, float]]:
        """Search the index for similar vectors.

        Returns list of (knowledge_id, similarity_score) tuples.
        """
        if self._index is None:
            raise RuntimeError("Index has not been built. Call build() first.")

        query = query_embedding.reshape(1, -1).astype(np.float32)
        scores, indices = self._index.search(query, min(top_k, self._index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            knowledge_id = self._record_mapping[idx]
            results.append((knowledge_id, float(score)))

        return results

    def save(self, save_dir: Path) -> None:
        """Save the index to disk."""
        import faiss

        save_dir.mkdir(parents=True, exist_ok=True)

        if self._index is not None:
            faiss.write_index(self._index, save_dir / "index.faiss")

        with open(save_dir / "record_mapping.json", "w") as f:
            json.dump(self._record_mapping, f)

    def load(self, save_dir: Path) -> None:
        """Load the index from disk."""
        import faiss

        index_path = save_dir / "index.faiss"
        mapping_path = save_dir / "record_mapping.json"

        if not index_path.exists() or not mapping_path.exists():
            raise FileNotFoundError(f"Index files not found in {save_dir}")

        self._index = faiss.read_index(index_path)
        self.dimension = self._index.d

        with open(mapping_path, "r") as f:
            self._record_mapping = json.load(f)

    def size(self) -> int:
        """Get the number of indexed records."""
        if self._index is None:
            return 0
        return self._index.ntotal

    def save_metadata(self, save_dir: Path, metadata: dict) -> None:
        """Save index metadata."""
        with open(save_dir / "index_metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

    def load_metadata(self, save_dir: Path) -> dict:
        """Load index metadata."""
        metadata_path = save_dir / "index_metadata.json"
        if not metadata_path.exists():
            return {}
        with open(metadata_path, "r") as f:
            return json.load(f)
