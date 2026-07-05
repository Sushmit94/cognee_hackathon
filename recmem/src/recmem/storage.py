import faiss
import numpy as np
from .config import EMBEDDING_DIM

class VectorStore:
    def __init__(self):
        self.index = faiss.IndexFlatIP(EMBEDDING_DIM)
        self.memory_units = {}

    def add(self, unit_id: str, embedding: list[float], unit_data: dict):
        vec = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(vec)
        self.index.add(vec)
        self.memory_units[unit_id] = unit_data

    def query(self, embedding: list[float], k: int = 20) -> list[dict]:
        if self.index.ntotal == 0:
            return []
        vec = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(vec)
        D, I = self.index.search(vec, min(k, self.index.ntotal))
        ids = list(self.memory_units.keys())
        results = []
        for dist, idx in zip(D[0], I[0]):
            if idx == -1:
                continue
            unit_id = ids[idx]
            results.append({**self.memory_units[unit_id], "similarity": float(dist)})
        return results

store = VectorStore()


fact_store = {}