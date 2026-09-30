import os
import uuid
from typing import List, Optional
import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from app.core.config import settings
from app.models.document import Document, DocumentStatus
from app.repositories.document import DocumentRepository
from app.repositories.audit import AuditLogRepository

class MockEmbeddingFunction(EmbeddingFunction):
    """Deterministic local mock embedding function for sandboxed testing."""
    def __init__(self) -> None:
        pass

    def name(self) -> str:
        return "mock"

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            val = float(len(text) % 100) / 100.0
            embeddings.append([val] * 3072)
        return embeddings

class RecursiveCharacterTextSplitter:
    """Custom light splitter mimicking LangChain's RecursiveCharacterTextSplitter interface."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", " ", ""]

    def split_text(self, text: str) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]
        
        separator = self.separators[-1]
        for s in self.separators:
            if s in text:
                separator = s
                break
        
        splits = text.split(separator)
        chunks = []
        current_chunk = ""
        
        for split in splits:
            if len(current_chunk) + len(split) + (len(separator) if current_chunk else 0) <= self.chunk_size:
                if current_chunk:
                    current_chunk += separator + split
                else:
                    current_chunk = split
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                if len(split) > self.chunk_size:
                    for i in range(0, len(split), self.chunk_size - self.chunk_overlap):
                        chunks.append(split[i:i + self.chunk_size])
                    current_chunk = ""
                else:
                    current_chunk = split
        
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks

class VectorStoreAdapter:
    """Unified adapter interface wrapping Pinecone, ChromaDB, and in-memory mock indexing."""
    mock_store = {}  # Shared class dictionary fallback for mock Pinecone tests

    def __init__(self, provider: str, embedding_function: EmbeddingFunction):
        self.provider = provider
        self.embedding_function = embedding_function
        self.is_mock = False

        if self.provider == "pinecone":
            if settings.PINECONE_API_KEY and settings.PINECONE_API_KEY != "dummy_pinecone_key":
                from pinecone import Pinecone
                self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
                self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)
                self.is_mock = False
            else:
                self.is_mock = True
        else:
            # Fallback to local ChromaDB
            os.makedirs(settings.CHROMA_DB_DIR, exist_ok=True)
            self.chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_DIR)
            self.collection = self.chroma_client.get_or_create_collection(
                name="documents",
                embedding_function=self.embedding_function
            )

    def add_document(self, document_id: uuid.UUID, filename: str, chunks: List[str]) -> None:
        """Upsert text chunks and metadata to the configured vector store."""
        embeddings = self.embedding_function(chunks)
        # Convert to native Python floats to avoid serialization issues (e.g. numpy.float32) in Pinecone
        embeddings = [[float(x) for x in emb] for emb in embeddings]
        
        if self.provider == "pinecone":
            if not self.is_mock:
                vectors = [
                    {
                        "id": f"{document_id}_{i}",
                        "values": embeddings[i],
                        "metadata": {
                            "document_id": str(document_id),
                            "chunk_index": i,
                            "filename": filename,
                            "text": chunks[i]
                        }
                    }
                    for i in range(len(chunks))
                ]
                # Batch upsert in chunks of 100 to stay within Pinecone payload limits
                batch_size = 100
                for batch_start in range(0, len(vectors), batch_size):
                    batch = vectors[batch_start:batch_start + batch_size]
                    self.index.upsert(vectors=batch)
            else:
                # In-memory mock storage
                self.mock_store[str(document_id)] = [
                    {
                        "id": f"{document_id}_{i}",
                        "text": chunks[i],
                        "metadata": {"filename": filename, "chunk_index": i}
                    }
                    for i in range(len(chunks))
                ]
        else:
            # ChromaDB
            ids = [f"{document_id}_{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "document_id": str(document_id),
                    "chunk_index": i,
                    "filename": filename
                }
                for i in range(len(chunks))
            ]
            self.collection.add(
                ids=ids,
                documents=chunks,
                metadatas=metadatas
            )

    def delete_document(self, document_id: uuid.UUID) -> None:
        """Remove document vectors from the configured vector store."""
        if self.provider == "pinecone":
            if not self.is_mock:
                try:
                    self.index.delete(filter={"document_id": str(document_id)})
                except Exception:
                    # Silently ignore if namespace/vectors not found (doc never indexed)
                    pass
            else:
                self.mock_store.pop(str(document_id), None)
        else:
            try:
                self.collection.delete(where={"document_id": str(document_id)})
            except Exception:
                pass

    def get_document_chunks(self, document_id: uuid.UUID) -> List[str]:
        """Fetch indexed text chunks for verification and tests."""
        if self.provider == "pinecone":
            if self.is_mock:
                return [item["text"] for item in self.mock_store.get(str(document_id), [])]
            return []
        else:
            res = self.collection.get(where={"document_id": str(document_id)})
            return res.get("documents", []) or []

    def query_similarity(
        self,
        query_text: str,
        top_k: int = 5,
        document_ids: Optional[List[uuid.UUID]] = None
    ) -> List[dict]:
        """Perform similarity queries returning matches (text, filename, score, document_id)."""
        if self.provider == "pinecone":
            embeddings = self.embedding_function([query_text])
            # Convert to native Python floats to avoid serialization issues (e.g. numpy.float32) in Pinecone
            query_vector = [float(x) for x in embeddings[0]]
            
            if not self.is_mock:
                filter_dict = {}
                if document_ids:
                    filter_dict["document_id"] = {"$in": [str(d) for d in document_ids]}
                
                res = self.index.query(
                    vector=query_vector,
                    top_k=top_k,
                    include_metadata=True,
                    filter=filter_dict if filter_dict else None
                )
                
                results = []
                for match in res.get("matches", []):
                    metadata = match.get("metadata", {})
                    results.append({
                        "text": metadata.get("text", ""),
                        "filename": metadata.get("filename", ""),
                        "score": match.get("score", 0.0),
                        "document_id": metadata.get("document_id", "")
                    })
                return results
            else:
                # In-memory keyword overlap similarity search for Pinecone testing
                all_chunks = []
                for doc_id, chunks in self.mock_store.items():
                    if document_ids and doc_id not in [str(d) for d in document_ids]:
                        continue
                    for chunk in chunks:
                        all_chunks.append(chunk)
                
                query_words = set(query_text.lower().split())
                scored_chunks = []
                for chunk in all_chunks:
                    chunk_text = chunk["text"]
                    chunk_words = set(chunk_text.lower().split())
                    match_count = len(query_words.intersection(chunk_words))
                    score = float(match_count) / max(len(query_words), 1)
                    scored_chunks.append({
                        "text": chunk_text,
                        "filename": chunk["metadata"]["filename"],
                        "score": score,
                        "document_id": str(chunk["id"].split("_")[0])
                    })
                
                scored_chunks.sort(key=lambda x: x["score"], reverse=True)
                return scored_chunks[:top_k]
        else:
            # ChromaDB
            where_clause = None
            if document_ids:
                if len(document_ids) == 1:
                    where_clause = {"document_id": str(document_ids[0])}
                else:
                    where_clause = {"document_id": {"$in": [str(d) for d in document_ids]}}
                    
            res = self.collection.query(
                query_texts=[query_text],
                n_results=top_k,
                where=where_clause
            )
            
            results = []
            if res and res.get("documents"):
                documents = res["documents"][0]
                metadatas = res["metadatas"][0]
                distances = res["distances"][0] if "distances" in res else [0.0] * len(documents)
                
                for i in range(len(documents)):
                    score = 1.0 - distances[i]
                    results.append({
                        "text": documents[i],
                        "filename": metadatas[i].get("filename", ""),
                        "score": score,
                        "document_id": metadatas[i].get("document_id", "")
                    })
            return results

class DocumentService:
    """Service layer handling document storage, content parsing, splitting, and vector indexing."""

    def __init__(self, document_repo: DocumentRepository, audit_repo: AuditLogRepository):
        self.document_repo = document_repo
        self.audit_repo = audit_repo
        
        # Ensure upload directory exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Initialize the vector store adapter
        self.vector_store = VectorStoreAdapter(
            provider=settings.VECTOR_DB_PROVIDER,
            embedding_function=self._get_embedding_function()
        )

    def _get_embedding_function(self) -> EmbeddingFunction:
        """Resolve embedding function. Uses OpenAI if key is present, else falls back to Mock."""
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "dummy_key_replace_in_env":
            return OpenAIEmbeddingFunction(
                api_key=settings.OPENAI_API_KEY,
                model_name="text-embedding-3-large"
            )
        return MockEmbeddingFunction()

    def _parse_file(self, file_path: str, content_type: str) -> str:
        """Extract text from file depending on content type (PDF, DOCX, or text/MD)."""
        if "pdf" in content_type:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        elif "word" in content_type or file_path.endswith(".docx"):
            import docx
            doc = docx.Document(file_path)
            text_parts = []
            
            for p in doc.paragraphs:
                if p.text.strip():
                    text_parts.append(p.text)
                    
            seen_cells = set()
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell._tc not in seen_cells:
                            seen_cells.add(cell._tc)
                            if cell.text.strip():
                                text_parts.append(cell.text)
                                
            return "\n".join(text_parts)
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

    async def process_document(
        self,
        document_id: uuid.UUID,
        file_path: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Parse, segment, and index document chunks asynchronously."""
        document = await self.document_repo.update_status(document_id, DocumentStatus.PROCESSING)
        if not document:
            return

        try:
            # 1. Parse content
            text = self._parse_file(file_path, document.content_type)
            if not text.strip():
                raise ValueError("Extracted text is empty")

            # 2. Chunk content
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = splitter.split_text(text)

            # 3. Add to Vector Store
            self.vector_store.add_document(document_id, document.filename, chunks)

            # 4. Mark Complete
            await self.document_repo.update_status(document_id, DocumentStatus.COMPLETED)
            
            await self.audit_repo.create(
                user_id=None,
                action="document_processed",
                ip_address=ip_address,
                user_agent=user_agent,
                payload={"document_id": str(document_id), "filename": document.filename, "chunks_count": len(chunks)}
            )

        except Exception as e:
            error_msg = str(e)[:1000]
            await self.document_repo.update_status(document_id, DocumentStatus.FAILED, error_message=error_msg)
            
            await self.audit_repo.create(
                user_id=None,
                action="document_processing_failed",
                ip_address=ip_address,
                user_agent=user_agent,
                payload={"document_id": str(document_id), "filename": document.filename, "error": error_msg}
            )

    async def delete_document(
        self,
        document_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Remove document file, database metadata, and vector index references."""
        document = await self.document_repo.get_by_id(document_id)
        if not document:
            return False

        # 1. Delete vectors
        self.vector_store.delete_document(document_id)

        # 2. Remove physical file
        file_path = os.path.join(settings.UPLOAD_DIR, f"{document_id}_{document.filename}")
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

        # 3. Delete DB record
        success = await self.document_repo.delete(document_id)
        
        if success:
            await self.audit_repo.create(
                user_id=None,
                action="document_deleted",
                ip_address=ip_address,
                user_agent=user_agent,
                payload={"document_id": str(document_id), "filename": document.filename}
            )
            
        return success
