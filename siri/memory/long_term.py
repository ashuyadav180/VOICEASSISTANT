"""Long-term memory via ChromaDB vector store."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

try:
    import chromadb

    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


class LongTermMemory:
    def __init__(self, chroma_dir: str, enabled: bool = True) -> None:
        self.enabled = enabled and CHROMA_AVAILABLE
        self._client = None
        self._collection = None

        if self.enabled:
            try:
                self._client = chromadb.PersistentClient(path=chroma_dir)
                self._collection = self._client.get_or_create_collection(
                    name="siri_memory",
                    metadata={"hnsw:space": "cosine"},
                )
                logger.info("ChromaDB memory loaded at %s", chroma_dir)
            except Exception as e:
                logger.warning("ChromaDB init failed: %s", e)
                self.enabled = False

        self._fallback: list[dict] = []

    def store(self, text: str, metadata: dict | None = None) -> None:
        if not text.strip():
            return
        entry = {
            "id": str(uuid.uuid4()),
            "text": text,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if self.enabled and self._collection:
            try:
                self._collection.add(
                    documents=[text],
                    ids=[entry["id"]],
                    metadatas=[{**entry["metadata"], "timestamp": entry["timestamp"]}],
                )
                return
            except Exception as e:
                logger.warning("ChromaDB store failed: %s", e)

        self._fallback.append(entry)
        if len(self._fallback) > 500:
            self._fallback = self._fallback[-500:]

    def retrieve(self, query: str, n: int = 5) -> list[str]:
        if not query.strip():
            return []

        if self.enabled and self._collection:
            try:
                count = self._collection.count()
                if count == 0:
                    return []
                results = self._collection.query(query_texts=[query], n_results=min(n, count))
                docs = results.get("documents", [[]])[0]
                return docs
            except Exception as e:
                logger.warning("ChromaDB retrieve failed: %s", e)

        # Fallback: simple keyword match
        q = query.lower()
        matches = [e["text"] for e in self._fallback if any(w in e["text"].lower() for w in q.split())]
        return matches[:n]
