import asyncio
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from app.main import app
from app.db.session import engine
from app.core.security import get_password_hash, verify_password
from app.db.redis import redis_client

def run_async(coro):
    """Helper to run async test coroutines in a clean event loop."""
    return asyncio.run(coro)

async def clear_db():
    """Utility to clear users and audit logs tables."""
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE audit_logs CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE users CASCADE;"))
    await engine.dispose()
    try:
        await redis_client.aclose()
    except Exception:
        pass

def test_password_hashing():
    """Verify password hashing and verification functions work correctly."""
    password = "SuperSecretPassword123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_auth_lifecycle():
    """Verify complete auth lifecycle: bootstrapping, registration, RBAC, refresh, and logout."""
    async def _test():
        await clear_db()
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # --- 1. BOOTSTRAPPING REGISTER (First user becomes Admin) ---
            reg_payload_1 = {
                "email": "admin@aegisai.com",
                "full_name": "Initial Administrator",
                "role": "admin",
                "password": "secure_admin_password_123"
            }
            res_reg1 = await ac.post("/api/v1/auth/register", json=reg_payload_1)
            assert res_reg1.status_code == 201
            data_reg1 = res_reg1.json()
            assert data_reg1["email"] == "admin@aegisai.com"
            assert data_reg1["role"] == "admin"
            assert data_reg1["is_active"] is True
            
            # --- 2. LOGIN (Retrieve Access & Refresh Tokens) ---
            login_data = {
                "username": "admin@aegisai.com",
                "password": "secure_admin_password_123"
            }
            res_login = await ac.post("/api/v1/auth/token", data=login_data)
            assert res_login.status_code == 200
            tokens = res_login.json()
            assert "access_token" in tokens
            assert "refresh_token" in tokens
            
            admin_headers = {"Authorization": f"Bearer {tokens['access_token']}"}
            
            # --- 3. SUBSEQUENT REGISTER WITHOUT TOKEN (Should Fail 401) ---
            reg_payload_2 = {
                "email": "operator@aegisai.com",
                "full_name": "Standard Operator",
                "role": "operator",
                "password": "secure_operator_password_123"
            }
            res_reg2_anon = await ac.post("/api/v1/auth/register", json=reg_payload_2)
            assert res_reg2_anon.status_code == 401
            
            # --- 4. REGISTER OPERATOR WITH ADMIN TOKEN (Should Succeed) ---
            res_reg2_auth = await ac.post(
                "/api/v1/auth/register",
                json=reg_payload_2,
                headers=admin_headers
            )
            assert res_reg2_auth.status_code == 201
            assert res_reg2_auth.json()["role"] == "operator"
            
            # --- 5. LOGIN AS OPERATOR ---
            operator_login = {
                "username": "operator@aegisai.com",
                "password": "secure_operator_password_123"
            }
            res_op_login = await ac.post("/api/v1/auth/token", data=operator_login)
            assert res_op_login.status_code == 200
            op_tokens = res_op_login.json()
            op_headers = {"Authorization": f"Bearer {op_tokens['access_token']}"}
            
            # --- 6. RBAC RESTRICTION VERIFICATION ---
            # Admin can access admin-only endpoint
            res_admin_test = await ac.get("/api/v1/auth/test-admin", headers=admin_headers)
            assert res_admin_test.status_code == 200
            assert res_admin_test.json()["email"] == "admin@aegisai.com"
            
            # Operator CANNOT access admin-only endpoint (Forbidden 403)
            res_op_admin_test = await ac.get("/api/v1/auth/test-admin", headers=op_headers)
            assert res_op_admin_test.status_code == 403
            
            # Both Admin and Operator can access operator-only endpoint
            res_admin_op_test = await ac.get("/api/v1/auth/test-operator", headers=admin_headers)
            assert res_admin_op_test.status_code == 200
            
            res_op_op_test = await ac.get("/api/v1/auth/test-operator", headers=op_headers)
            assert res_op_op_test.status_code == 200
            
            # --- 6.5 USERS ENDPOINT ACCESS VERIFICATION ---
            # Admin can retrieve users list
            res_admin_users = await ac.get("/api/v1/auth/users", headers=admin_headers)
            assert res_admin_users.status_code == 200
            users_list = res_admin_users.json()
            assert len(users_list) == 2  # Admin + Operator
            
            # Operator CANNOT access users list (Forbidden 403)
            res_op_users = await ac.get("/api/v1/auth/users", headers=op_headers)
            assert res_op_users.status_code == 403
            
            # --- 7. REFRESH TOKEN ROTATION ---
            refresh_payload = {
                "refresh_token": tokens["refresh_token"]
            }
            res_refresh = await ac.post("/api/v1/auth/refresh", json=refresh_payload)
            assert res_refresh.status_code == 200
            new_tokens = res_refresh.json()
            assert "access_token" in new_tokens
            assert "refresh_token" in new_tokens
            assert new_tokens["access_token"] != tokens["access_token"]
            
            # Old refresh token should be blacklisted and fail on repeat refresh
            res_refresh_repeat = await ac.post("/api/v1/auth/refresh", json=refresh_payload)
            assert res_refresh_repeat.status_code == 400
            
            # --- 8. LOGOUT (Token Revocation) ---
            logout_payload = {
                "refresh_token": new_tokens["refresh_token"]
            }
            # Add new access token headers for authenticated logout call
            new_admin_headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}
            res_logout = await ac.post(
                "/api/v1/auth/logout",
                json=logout_payload,
                headers=new_admin_headers
            )
            assert res_logout.status_code == 200
            
            # Logged out access token should fail to access test endpoints
            res_post_logout_test = await ac.get("/api/v1/auth/test-admin", headers=new_admin_headers)
            assert res_post_logout_test.status_code == 401

            await engine.dispose()
            try:
                await redis_client.aclose()
            except Exception:
                pass

    run_async(_test())
