"""RAG engine with ChromaDB for memory & knowledge retrieval."""
import os
from typing import List, Dict, Any, Optional
import json

# Try importing chromadb; fallback to in-memory if unavailable
try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

class RAGEngine:
    """LangChain-style RAG using ChromaDB for vector storage."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.client = None
        self.collection = None
        self._init_db()

    def _init_db(self):
        if not CHROMA_AVAILABLE:
            return
        os.makedirs(self.db_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.client.get_or_create_collection(
            name="personality_memories",
            metadata={"hnsw:space": "cosine"}
        )

    def add_memories(self, user_id: str, texts: List[str], metadata: Optional[List[Dict]] = None):
        if not CHROMA_AVAILABLE or self.collection is None:
            return
        ids = [f"{user_id}_{i}" for i in range(len(texts))]
        metas = metadata or [{} for _ in texts]
        for m in metas:
            m["user_id"] = user_id
        self.collection.add(
            documents=texts,
            ids=ids,
            metadatas=metas
        )

    def query(self, user_id: str, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        if not CHROMA_AVAILABLE or self.collection is None:
            return []
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where={"user_id": user_id}
        )
        memories = []
        for i, doc in enumerate(results.get("documents", [[]])[0]):
            memories.append({
                "text": doc,
                "distance": results.get("distances", [[]])[0][i] if results.get("distances") else 0.0,
                "metadata": results.get("metadatas", [[]])[0][i] if results.get("metadatas") else {}
            })
        return memories

    def get_all(self, user_id: str) -> List[str]:
        if not CHROMA_AVAILABLE or self.collection is None:
            return []
        results = self.collection.get(where={"user_id": user_id})
        return results.get("documents", [])

class InMemoryRAG:
    """Fallback when ChromaDB not available."""
    def __init__(self, db_path: str = None):
        self.memories: Dict[str, List[str]] = {}

    def add_memories(self, user_id: str, texts: List[str], metadata=None):
        self.memories.setdefault(user_id, []).extend(texts)

    def query(self, user_id: str, query_text: str, n_results: int = 5):
        all_mems = self.memories.get(user_id, [])
        # Simple keyword match fallback
        scored = []
        for m in all_mems:
            score = sum(1 for w in query_text.lower().split() if w in m.lower())
            scored.append((score, m))
        scored.sort(reverse=True)
        return [{"text": m, "distance": 0.0, "metadata": {}} for _, m in scored[:n_results]]

    def get_all(self, user_id: str):
        return self.memories.get(user_id, [])

# Factory
def get_rag(db_path: str):
    if CHROMA_AVAILABLE:
        return RAGEngine(db_path)
    return InMemoryRAG()
