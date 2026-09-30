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
    """Reset vector adapter mock store."""
    if settings.VECTOR_DB_PROVIDER == "pinecone":
        VectorStoreAdapter.mock_store.clear()
    yield

def test_agent_graph_execution():
    """Verify routing, escalation, and HITL checkpointer loops in LangGraph agent."""
    settings.OPENAI_API_KEY = "dummy_key_replace_in_env"
    settings.PINECONE_API_KEY = "dummy_pinecone_key"
    
    async def _test():
        await clear_db()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # 1. Register and login as Admin/Operator
            admin_payload = {
                "email": "operator@aegisai.com",
                "full_name": "Operator User",
                "role": "operator",
                "password": "secure_operator_password_123"
            }
            await ac.post("/api/v1/auth/register", json=admin_payload)
            
            login_res = await ac.post(
                "/api/v1/auth/token",
                data={"username": "operator@aegisai.com", "password": "secure_operator_password_123"}
            )
            token = login_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 2. Test direct Escalation routing
            thread_esc_id = uuid.uuid4()
            esc_res = await ac.post(
                "/api/v1/agent/run",
                json={"query": "I want a refund on my credit card immediately", "thread_id": str(thread_esc_id)},
                headers=headers
            )
            assert esc_res.status_code == 200
            esc_data = esc_res.json()
            assert esc_data["escalated"] is True
            assert esc_data["requires_approval"] is False
            assert "escalated" in esc_data["response"].lower()

            # 3. Test research/response routing with HITL Interrupt
            thread_run_id = uuid.uuid4()
            run_res = await ac.post(
                "/api/v1/agent/run",
                json={"query": "docs regarding SMTP setup configuration", "thread_id": str(thread_run_id)},
                headers=headers
            )
            assert run_res.status_code == 200
            run_data = run_res.json()
            assert run_data["escalated"] is False
            assert run_data["requires_approval"] is True
            assert "mock draft" in run_data["response"].lower()

            # 4. Test HITL Reject & Redraft cycle (approved=False + feedback)
            feedback_res = await ac.post(
                "/api/v1/agent/approve",
                json={
                    "thread_id": str(thread_run_id),
                    "approved": False,
                    "feedback": "Please translate to Spanish and keep it short"
                },
                headers=headers
            )
            assert feedback_res.status_code == 200
            feedback_data = feedback_res.json()
            assert feedback_data["requires_approval"] is True  # Paused again
            assert "mock redraft" in feedback_data["response"].lower()
            assert "spanish" in feedback_data["response"].lower()

            # 5. Test HITL Approve (approved=True)
            approve_res = await ac.post(
                "/api/v1/agent/approve",
                json={
                    "thread_id": str(thread_run_id),
                    "approved": True
                },
                headers=headers
            )
            assert approve_res.status_code == 200
            approve_data = approve_res.json()
            assert approve_data["requires_approval"] is False  # Loop completed
            assert approve_data["escalated"] is False

            # Cleanup connection pools
            await engine.dispose()
            try:
                await redis_client.aclose()
            except Exception:
                pass

    run_async(_test())
