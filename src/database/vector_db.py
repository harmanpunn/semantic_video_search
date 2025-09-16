import numpy as np
import faiss
import json
import pickle
from typing import List, Dict, Tuple, Any
from pathlib import Path
from config.settings import VECTOR_DB_PATH, EMBEDDINGS_FILE


class VectorDatabase:
    def __init__(self):
        self.index = None
        self.metadata = []
        self.dimension = 1024  # Twelve Labs embedding dimension

    def create_index(self, embeddings: List[List[float]], metadata: List[Dict[str, Any]]):
        """Create FAISS index from embeddings"""
        embeddings_array = np.array(embeddings, dtype=np.float32)
        self.dimension = embeddings_array.shape[1]

        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for similarity

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings_array)

        self.index.add(embeddings_array)
        self.metadata = metadata

        print(f"✅ Created FAISS index with {self.index.ntotal} vectors")

    def save_index(self, path: str = VECTOR_DB_PATH):
        """Save FAISS index and metadata to disk"""
        if self.index is None:
            raise ValueError("No index to save")

        # Save FAISS index
        faiss.write_index(self.index, f"{path}.index")

        # Save metadata
        with open(f"{path}.metadata", 'wb') as f:
            pickle.dump(self.metadata, f)

        print(f"💾 Saved vector database to {path}")

    def load_index(self, path: str = VECTOR_DB_PATH):
        """Load FAISS index and metadata from disk"""
        index_path = f"{path}.index"
        metadata_path = f"{path}.metadata"

        if not (Path(index_path).exists() and Path(metadata_path).exists()):
            return False

        # Load FAISS index
        self.index = faiss.read_index(index_path)

        # Load metadata
        with open(metadata_path, 'rb') as f:
            self.metadata = pickle.load(f)

        print(f"📁 Loaded vector database with {self.index.ntotal} vectors")
        return True

    def search(self, query_embedding: List[float], k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """Search for similar vectors"""
        if self.index is None:
            raise ValueError("Index not loaded")

        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)

        scores, indices = self.index.search(query_array, k)

        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.metadata):
                results.append((self.metadata[idx], float(score)))

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        if self.index is None:
            return {"loaded": False}

        return {
            "loaded": True,
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "metadata_count": len(self.metadata)
        }


def build_vector_database():
    """Build vector database from embeddings file"""
    if not Path(EMBEDDINGS_FILE).exists():
        print(f"❌ Embeddings file not found: {EMBEDDINGS_FILE}")
        print("Run: python -m src.embeddings.generate")
        return False

    # Load embeddings data
    with open(EMBEDDINGS_FILE, 'r') as f:
        embeddings_data = json.load(f)

    if not embeddings_data.get("videos"):
        print("❌ No video data found in embeddings file")
        return False

    print("Building vector database...")

    # For this POC, we'll use Twelve Labs search directly
    # FAISS can be used for custom embeddings if needed
    db = VectorDatabase()

    # Create dummy embeddings for structure (real embeddings come from Twelve Labs search)
    dummy_embeddings = [np.random.rand(1024).tolist() for _ in embeddings_data["videos"]]
    metadata = [
        {
            "video_id": video["video_id"],
            "filename": video["filename"],
            "filepath": video["filepath"]
        }
        for video in embeddings_data["videos"]
    ]

    db.create_index(dummy_embeddings, metadata)
    db.save_index()

    return True


if __name__ == "__main__":
    build_vector_database()