"""Local Research Library powered by ChromaDB."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

def _ok(result: Any) -> dict:
    return {"success": True, "result": result, "error": None}

def _err(msg: str) -> dict:
    return {"success": False, "result": None, "error": msg}

class LocalLibrary:
    def __init__(self, persist_dir: str = ".siri/library"):
        self.persist_dir = persist_dir
        if CHROMA_AVAILABLE:
            self.client = chromadb.PersistentClient(path=self.persist_dir)
            self.collection = self.client.get_or_create_collection(name="research_papers")
        else:
            self.client = None
            self.collection = None

    def library_save(self, title: str, abstract: str, metadata: dict = None) -> dict:
        if not CHROMA_AVAILABLE:
            return _err("ChromaDB not installed. Run: pip install chromadb")
            
        try:
            doc_id = title.replace(" ", "_").lower()
            self.collection.add(
                documents=[abstract],
                metadatas=[metadata or {}],
                ids=[doc_id]
            )
            return _ok(f"Saved '{title}' to local library.")
        except Exception as e:
            return _err(f"Failed to save to library: {e}")

    def library_search(self, query: str, n_results: int = 3) -> dict:
        if not CHROMA_AVAILABLE:
            return _err("ChromaDB not installed.")
            
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            return _ok(results)
        except Exception as e:
            return _err(f"Library search failed: {e}")

_library_instance = None

def get_library() -> LocalLibrary:
    global _library_instance
    if _library_instance is None:
        import os
        lib_path = os.path.expanduser("~/.siri/library")
        _library_instance = LocalLibrary(persist_dir=lib_path)
    return _library_instance

def library_save(title: str, abstract: str) -> dict:
    return get_library().library_save(title, abstract)

def library_search(query: str) -> dict:
    return get_library().library_search(query)
