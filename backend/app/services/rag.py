import uuid
from typing import List, Optional
from app.services.document import DocumentService

class RAGService:
    """Service layer managing context similarity lookups and prompt formatting."""

    def __init__(self, doc_service: DocumentService):
        self.doc_service = doc_service

    async def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        document_ids: Optional[List[uuid.UUID]] = None
    ) -> List[dict]:
        """Perform similarity search on the vector database adapter for query context."""
        return self.doc_service.vector_store.query_similarity(
            query_text=query,
            top_k=top_k,
            document_ids=document_ids
        )

    def build_grounded_prompt(self, query: str, context_chunks: List[dict]) -> str:
        """Assemble retrieved context chunks into a structured system prompt template."""
        if not context_chunks:
            return (
                "You are an assistant answering user queries.\n"
                "No reference context documents were found matching this search.\n\n"
                f"User Query: {query}\n"
                "Grounded Answer:"
            )

        context_str = ""
        for i, chunk in enumerate(context_chunks):
            filename = chunk.get("filename", "Unknown Document")
            score = chunk.get("score", 0.0)
            text = chunk.get("text", "").strip()
            context_str += f"[Document {i+1}: {filename} (Similarity Score: {score:.4f})]\n{text}\n---\n"

        system_prompt = (
            "You are a helpful customer service AI assistant representing AegisAI.\n"
            "Answer the user query based ONLY on the provided context documents below. "
            "If the answer cannot be confidently derived from the documents, state that "
            "you do not know or do not have enough context, and do not make up facts.\n\n"
            f"Context Documents:\n{context_str}\n"
            f"User Query: {query}\n"
            "Grounded Answer:"
        )
        return system_prompt
