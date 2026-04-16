from typing import List, Dict, Any

import chromadb
from chromadb.utils import embedding_functions


class VectorStore:
    COLLECTION_NAME = "anatel_normativos"

    def __init__(self, persist_dir: str):
        self.persist_dir = persist_dir
        self.client = chromadb.PersistentClient(path=persist_dir)
        # Multilingual sentence transformer — good coverage for Portuguese legal text
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.collection = self._get_or_create()

    def _get_or_create(self):
        return self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        if not documents:
            return
        batch_size = 50
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            self.collection.add(
                ids=[d['id'] for d in batch],
                documents=[d['text'] for d in batch],
                metadatas=[{
                    'file': d['file'],
                    'chunk_idx': d['chunk_idx'],
                    'total_chunks': d['total_chunks'],
                } for d in batch],
            )

    def search(self, query: str, top_k: int = 6) -> List[Dict[str, Any]]:
        n = min(top_k, self.collection.count())
        if n == 0:
            return []
        results = self.collection.query(query_texts=[query], n_results=n)
        return [
            {
                'text': text,
                'file': meta['file'],
                'chunk_idx': meta['chunk_idx'],
            }
            for text, meta in zip(results['documents'][0], results['metadatas'][0])
        ]

    def count(self) -> int:
        return self.collection.count()

    def reset(self) -> None:
        self.client.delete_collection(self.COLLECTION_NAME)
        self.collection = self._get_or_create()
