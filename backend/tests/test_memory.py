import uuid
import pytest
import asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.main import app
from app.core.config import settings
from app.db.session import engine
from app.db.redis import redis_client

def run_async(coro):
    return asyncio.run(coro)

async def clear_db():
    """Clear database tables."""
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE audit_logs CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE documents CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE messages CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE actions CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE threads CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE memories CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE users CASCADE;"))
    await engine.dispose()
    try:
        await redis_client.aclose()
    except Exception:
        pass

def test_thread_history_and_memory_summarization():
    """Verify threads/messages persistence, tool action logging, and CRM summarization."""
    async def _test():
        await clear_db()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # 1. Register/Login operator
            operator_payload = {
                "email": "operator-memory@aegisai.com",
                "full_name": "Operator Memory",
                "role": "operator",
                "password": "secure_operator_password_123"
            }
            await ac.post("/api/v1/auth/register", json=operator_payload)
            
            login_res = await ac.post(
                "/api/v1/auth/token",
                data={"username": "operator-memory@aegisai.com", "password": "secure_operator_password_123"}
            )
            token = login_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 2. Run agent workflow (will create Thread and user Message)
            thread_id = uuid.uuid4()
            run_res = await ac.post(
                "/api/v1/agent/run",
                json={
                    "query": "SMTP setup instructions query from client@aegisai.com",
                    "thread_id": str(thread_id)
                },
                headers=headers
            )
            assert run_res.status_code == 200
            assert run_res.json()["requires_approval"] is True

            # Check history (should contain only the user's message, as draft is not approved/sent yet)
            hist_res = await ac.get(f"/api/v1/agent/thread/{thread_id}/history", headers=headers)
            assert hist_res.status_code == 200
            messages = hist_res.json()
            assert len(messages) == 1
            assert messages[0]["role"] == "user"
            assert "client@aegisai.com" in messages[0]["content"]

            # 3. Approve draft (will dispatch email and write assistant Message + Action log)
            approve_res = await ac.post(
                "/api/v1/agent/approve",
                json={
                    "thread_id": str(thread_id),
                    "approved": True
                },
                headers=headers
            )
            assert approve_res.status_code == 200
            assert approve_res.json()["requires_approval"] is False

            # Verify history now includes the assistant response
            hist_res_after = await ac.get(f"/api/v1/agent/thread/{thread_id}/history", headers=headers)
            messages_after = hist_res_after.json()
            assert len(messages_after) == 2
            assert messages_after[1]["role"] == "assistant"
            assert "mock draft" in messages_after[1]["content"].lower()

            # 4. Trigger memory summarization on thread
            sum_res = await ac.post(f"/api/v1/agent/thread/{thread_id}/summarize", headers=headers)
            assert sum_res.status_code == 200
            memory_data = sum_res.json()
            assert memory_data["customer_email"] == "client@aegisai.com"
            assert "[mock summary]" in memory_data["summary"].lower()

            # 5. Verify escalation action logging
            thread_esc_id = uuid.uuid4()
            esc_res = await ac.post(
                "/api/v1/agent/run",
                json={
                    "query": "Billing dispute refund request for billing-issue@aegisai.com",
                    "thread_id": str(thread_esc_id)
                },
                headers=headers
            )
            assert esc_res.status_code == 200
            assert esc_res.json()["escalated"] is True

            # Verify escalation log is stored in messages
            esc_hist_res = await ac.get(f"/api/v1/agent/thread/{thread_esc_id}/history", headers=headers)
            esc_messages = esc_hist_res.json()
            assert len(esc_messages) == 2
            assert esc_messages[1]["role"] == "assistant"
            assert "ticket created" in esc_messages[1]["content"].lower()

            # Cleanup connection pools
            await engine.dispose()
            try:
                await redis_client.aclose()
            except Exception:
                pass

    run_async(_test())
