from typing import List, Dict, Any, Tuple

import anthropic

from .config import MODEL, SYSTEM_PROMPT, TOP_K_RESULTS
from .store import VectorStore


class AnatelAssistant:
    def __init__(self, vector_store: VectorStore):
        self.store = vector_store
        self.client = anthropic.Anthropic()
        self.history: List[Dict[str, Any]] = []

    def _build_context(self, docs: List[Dict[str, Any]]) -> str:
        if not docs:
            return ""
        parts = ["## Trechos dos documentos normativos relevantes para esta consulta:\n"]
        for i, doc in enumerate(docs, 1):
            parts.append(f"### [{i}] Fonte: {doc['file']}\n```\n{doc['text']}\n```\n")
        return "\n".join(parts)

    def chat(self, user_message: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Retrieve relevant doc chunks, stream Claude's response, return (full_text, sources)."""
        docs = self.store.search(user_message, top_k=TOP_K_RESULTS)
        context = self._build_context(docs)

        augmented = (f"{context}\n---\n\n**Consulta:**\n{user_message}") if context else user_message

        # Build messages: full history with clean user turns + current augmented turn
        messages = self.history + [{"role": "user", "content": augmented}]

        full_text = ""
        with self.client.messages.stream(
            model=MODEL,
            max_tokens=8192,
            thinking={"type": "adaptive"},
            system=[{
                "type": "text",
                "text": SYSTEM_PROMPT,
                # Cache the stable system prompt across turns
                "cache_control": {"type": "ephemeral"},
            }],
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
                full_text += text

        # Store clean user message in history (without doc context) to avoid token explosion
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": full_text})

        return full_text, docs

    def reset(self) -> None:
        self.history = []
