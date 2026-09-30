import io
import uuid
import pytest
import asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.main import app
from app.core.config import settings
from app.db.session import engine
from app.db.redis import redis_client
from app.services.document import VectorStoreAdapter, MockEmbeddingFunction

def run_async(coro):
    return asyncio.run(coro)

async def clear_db():
    """Clear all database tables."""
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE audit_logs CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE documents CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE users CASCADE;"))
    await engine.dispose()
    try:
        await redis_client.aclose()
    except Exception:
        pass

@pytest.fixture(autouse=True)
def clean_vector_store():
    """Reset the VectorStoreAdapter mock_store or Chroma collection before each test."""
    adapter = VectorStoreAdapter(
        provider=settings.VECTOR_DB_PROVIDER,
        embedding_function=MockEmbeddingFunction()
    )
    if settings.VECTOR_DB_PROVIDER == "pinecone":
        VectorStoreAdapter.mock_store.clear()
    else:
        try:
            adapter.chroma_client.delete_collection("documents")
        except Exception:
            pass
    yield

def test_rag_retrieval_and_grounding():
    """Verify context similarity retrieve and grounded prompt compilation."""
    async def _test():
        await clear_db()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # 1. Register and login as Admin
            admin_payload = {
                "email": "admin@aegisai.com",
                "full_name": "Admin User",
                "role": "admin",
                "password": "secure_admin_password_123"
            }
            await ac.post("/api/v1/auth/register", json=admin_payload)
            
            login_res = await ac.post(
                "/api/v1/auth/token",
                data={"username": "admin@aegisai.com", "password": "secure_admin_password_123"}
            )
            token = login_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 2. Upload sample documents to establish index content
            doc1_content = "The AegisAI platform supports integrations with SMTP for sending simulated notifications."
            doc2_content = "ChromaDB and Pinecone are vector databases. Pinecone is a cloud serverless vector database."
            
            res_upload1 = await ac.post(
                "/api/v1/documents/upload",
                files={"file": ("smtp_docs.txt", io.BytesIO(doc1_content.encode("utf-8")), "text/plain")},
                headers=headers
            )
            assert res_upload1.status_code == 201
            doc1_id = res_upload1.json()["id"]

            res_upload2 = await ac.post(
                "/api/v1/documents/upload",
                files={"file": ("vector_docs.md", io.BytesIO(doc2_content.encode("utf-8")), "text/markdown")},
                headers=headers
            )
            assert res_upload2.status_code == 201
            doc2_id = res_upload2.json()["id"]

            # Wait briefly for background parsing tasks to complete
            await asyncio.sleep(0.5)

            # 3. Query RAG Context Retrieve endpoint (POST /api/v1/rag/retrieve)
            retrieve_payload = {
                "query": "SMTP integration",
                "top_k": 2,
                "document_ids": [doc1_id, doc2_id]
            }
            
            res_retrieve = await ac.post(
                "/api/v1/rag/retrieve",
                json=retrieve_payload,
                headers=headers
            )
            assert res_retrieve.status_code == 200
            chunks = res_retrieve.json()
            assert len(chunks) > 0
            
            # Verify the top chunk matches the SMTP query
            assert "SMTP" in chunks[0]["text"]
            assert chunks[0]["filename"] == "smtp_docs.txt"
            assert chunks[0]["document_id"] == doc1_id

            # 4. Query RAG Query endpoint (POST /api/v1/rag/query)
            query_payload = {
                "query": "What database is Pinecone?",
                "top_k": 2
            }
            res_query = await ac.post(
                "/api/v1/rag/query",
                json=query_payload,
                headers=headers
            )
            assert res_query.status_code == 200
            query_data = res_query.json()
            assert "prompt" in query_data
            assert query_data["context_chunks_count"] > 0
            
            prompt = query_data["prompt"]
            assert "AegisAI" in prompt
            assert "Pinecone" in prompt
            assert "What database is Pinecone?" in prompt

            # 5. Access control verify: anonymized request fails
            res_anon = await ac.post(
                "/api/v1/rag/retrieve",
                json=retrieve_payload
            )
            assert res_anon.status_code == 401

            # Cleanup connection pools
            await engine.dispose()
            try:
                await redis_client.aclose()
            except Exception:
                pass

    run_async(_test())
