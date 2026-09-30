import os
import io
import uuid
import pytest
import asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
import docx
import chromadb

from app.main import app
from app.core.config import settings
from app.db.session import engine
from app.services.document import DocumentService, MockEmbeddingFunction, VectorStoreAdapter
from app.repositories.document import DocumentRepository
from app.repositories.audit import AuditLogRepository
from app.db.redis import redis_client

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
def clean_chroma():
    """Clean the ChromaDB documents collection before each test."""
    chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_DIR)
    try:
        chroma_client.delete_collection("documents")
    except Exception:
        pass
    yield

def test_document_ingestion_lifecycle():
    """Verify document upload, parsing, splitting, indexing, and deletion flows."""
    async def _test():
        await clear_db()

        # Minimal PDF bytes that extract "Hello world from PDF"
        pdf_bytes = (
            b"%PDF-1.4\n"
            b"1 0 obj <</Type/Catalog/Pages 2 0 R>> endobj\n"
            b"2 0 obj <</Type/Pages/Kids[3 0 R]/Count 1>> endobj\n"
            b"3 0 obj <</Type/Page/Parent 2 0 R/Resources<</Font<</F1<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>>>>>/MediaBox[0 0 612 792]/Contents 4 0 R>> endobj\n"
            b"4 0 obj <</Length 51>> stream\n"
            b"BT\n/F1 12 Tf\n72 720 Td\n(Hello world from PDF) Tj\nET\nendstream\nendobj\n"
            b"xref\n0 5\n"
            b"0000000000 65535 f\n"
            b"0000000009 00000 n\n"
            b"0000000056 00000 n\n"
            b"0000000111 00000 n\n"
            b"0000000236 00000 n\n"
            b"trailer <</Size 5/Root 1 0 R>>\n"
            b"startxref\n338\n%%EOF"
        )

        # Generate a temporary DOCX file
        docx_io = io.BytesIO()
        doc = docx.Document()
        doc.add_paragraph("This is a test paragraph inside a Word DOCX document.")
        doc.save(docx_io)
        docx_bytes = docx_io.getvalue()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # 1. Register and login to get admin credentials
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

            # 2. Upload Markdown file
            md_content = "# AegisAI Doc\n\nThis is a sample markdown document for RAG processing."
            res_upload_md = await ac.post(
                "/api/v1/documents/upload",
                files={"file": ("sample.md", io.BytesIO(md_content.encode("utf-8")), "text/markdown")},
                headers=headers
            )
            assert res_upload_md.status_code == 201
            md_data = res_upload_md.json()
            md_doc_id = md_data["id"]
            assert md_data["filename"] == "sample.md"
            assert md_data["content_type"] == "text/markdown"

            # 3. Upload PDF file
            res_upload_pdf = await ac.post(
                "/api/v1/documents/upload",
                files={"file": ("sample.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
                headers=headers
            )
            assert res_upload_pdf.status_code == 201
            pdf_data = res_upload_pdf.json()
            pdf_doc_id = pdf_data["id"]

            # 4. Upload DOCX file
            res_upload_docx = await ac.post(
                "/api/v1/documents/upload",
                files={"file": ("sample.docx", io.BytesIO(docx_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                headers=headers
            )
            assert res_upload_docx.status_code == 201
            docx_data = res_upload_docx.json()
            docx_doc_id = docx_data["id"]

            # 5. List uploaded documents
            res_list = await ac.get("/api/v1/documents/", headers=headers)
            assert res_list.status_code == 200
            list_data = res_list.json()
            assert len(list_data) == 3

            # 6. Retrieve detailed status (wait briefly for background tasks to finish)
            await asyncio.sleep(0.5)
            
            res_status_md = await ac.get(f"/api/v1/documents/{md_doc_id}", headers=headers)
            assert res_status_md.json()["status"] == "completed"

            res_status_pdf = await ac.get(f"/api/v1/documents/{pdf_doc_id}", headers=headers)
            assert res_status_pdf.json()["status"] == "completed"

            res_status_docx = await ac.get(f"/api/v1/documents/{docx_doc_id}", headers=headers)
            assert res_status_docx.json()["status"] == "completed"

            # 7. Verify chunking and indexing in the vector store via VectorStoreAdapter
            adapter = VectorStoreAdapter(
                provider=settings.VECTOR_DB_PROVIDER,
                embedding_function=MockEmbeddingFunction()
            )
            
            # Verify Markdown chunks
            md_chunks = adapter.get_document_chunks(md_doc_id)
            assert len(md_chunks) > 0
            assert "AegisAI Doc" in md_chunks[0]

            # Verify PDF chunks
            pdf_chunks = adapter.get_document_chunks(pdf_doc_id)
            assert len(pdf_chunks) > 0
            assert "Hello world from PDF" in pdf_chunks[0]

            # Verify DOCX chunks
            docx_chunks = adapter.get_document_chunks(docx_doc_id)
            assert len(docx_chunks) > 0
            assert "test paragraph inside a Word DOCX" in docx_chunks[0]

            # 8. Delete document
            res_delete = await ac.delete(f"/api/v1/documents/{md_doc_id}", headers=headers)
            assert res_delete.status_code == 200
            
            # Verify deleted from DB
            res_get_deleted = await ac.get(f"/api/v1/documents/{md_doc_id}", headers=headers)
            assert res_get_deleted.status_code == 404

            # Verify deleted from disk
            file_path = os.path.join(settings.UPLOAD_DIR, f"{md_doc_id}_sample.md")
            assert not os.path.exists(file_path)

            # Verify deleted from Vector store
            md_chunks_after = adapter.get_document_chunks(md_doc_id)
            assert len(md_chunks_after) == 0
            
            await engine.dispose()
            try:
                await redis_client.aclose()
            except Exception:
                pass

    run_async(_test())
