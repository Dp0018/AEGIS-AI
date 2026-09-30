import uuid
import pytest
import asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.main import app
from app.core.config import settings
from app.db.session import engine
from app.db.redis import redis_client
from app.services.tools import (
    lookup_customer,
    create_support_ticket,
    send_smtp_email,
    customer_db,
    ticket_registry,
    email_log
)

def run_async(coro):
    return asyncio.run(coro)

async def clear_db():
    """Clear database tables."""
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
def reset_registries():
    """Reset shared CRM, ticket and email simulation memories before each test."""
    ticket_registry.clear()
    email_log.clear()
    
    # Reset CRM counters
    for key in customer_db:
        customer_db[key]["active_tickets_count"] = 0
    yield

def test_standalone_tools():
    """Verify customer lookup, SMTP dispatch, and support ticketing return correct values."""
    # Customer Lookup
    profile = lookup_customer("billing-issue@aegisai.com")
    assert profile["found"] is True
    assert profile["subscription_tier"] == "pro"
    assert profile["billing_status"] == "past_due"

    unknown = lookup_customer("non-existent@aegisai.com")
    assert unknown["found"] is False

    # Ticketing
    ticket = create_support_ticket("billing-issue@aegisai.com", "Double charge on account", "high")
    assert ticket["ticket_id"].startswith("TIC-")
    assert ticket["status"] == "open"
    assert ticket_registry[ticket["ticket_id"]]["issue"] == "Double charge on account"
    assert customer_db["billing-issue@aegisai.com"]["active_tickets_count"] == 1

    # SMTP Dispatch
    log = send_smtp_email("test@aegisai.com", "Welcome", "Hello!")
    assert log["message_id"].startswith("MSG-")
    assert log["status"] == "delivered"
    assert email_log[0]["to"] == "test@aegisai.com"


def test_agent_tools_integration():
    """Verify that RAG/LangGraph workflows invoke tools during escalations and approvals."""
    async def _test():
        await clear_db()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # 1. Register/Login operator
            operator_payload = {
                "email": "operator-tools@aegisai.com",
                "full_name": "Operator Tools",
                "role": "operator",
                "password": "secure_operator_password_123"
            }
            await ac.post("/api/v1/auth/register", json=operator_payload)
            
            login_res = await ac.post(
                "/api/v1/auth/token",
                data={"username": "operator-tools@aegisai.com", "password": "secure_operator_password_123"}
            )
            token = login_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 2. Trigger Escalation -> should automatically create a ticket
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
            
            # Verify ticket was generated and customer counter incremented
            assert len(ticket_registry) == 1
            ticket = list(ticket_registry.values())[0]
            assert ticket["email"] == "billing-issue@aegisai.com"
            assert customer_db["billing-issue@aegisai.com"]["active_tickets_count"] == 1

            # 3. Trigger Response & Approval -> should dispatch SMTP email
            thread_run_id = uuid.uuid4()
            
            # Start run (will pause at response draft)
            run_res = await ac.post(
                "/api/v1/agent/run",
                json={
                    "query": "SMTP setup instructions query from customer@aegisai.com",
                    "thread_id": str(thread_run_id)
                },
                headers=headers
            )
            assert run_res.status_code == 200
            assert run_res.json()["requires_approval"] is True
            assert len(email_log) == 0  # Not sent yet

            # Approve (should route to email_dispatch node)
            approve_res = await ac.post(
                "/api/v1/agent/approve",
                json={
                    "thread_id": str(thread_run_id),
                    "approved": True
                },
                headers=headers
            )
            assert approve_res.status_code == 200
            assert approve_res.json()["requires_approval"] is False
            
            # Verify email log generated
            assert len(email_log) == 1
            email = email_log[0]
            assert email["to"] == "customer@aegisai.com"
            assert "mock draft" in email["body"].lower()

            # Cleanup connection pools
            await engine.dispose()
            try:
                await redis_client.aclose()
            except Exception:
                pass

    run_async(_test())
