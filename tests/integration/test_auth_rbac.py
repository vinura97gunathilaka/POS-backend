import pytest
from fastapi.testclient import TestClient

def test_initial_admin_setup(client):
    res = client.post("/api/v1/auth/setup-initial-admin")
    assert res.status_code == 200
    data = res.json()["data"]
    assert "admin@smartpos.com" in data["message"]

def test_login_success_and_token_structure(client):
    client.post("/api/v1/auth/setup-initial-admin")

    res = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@smartpos.com", "password": "admin123"}
    )
    assert res.status_code == 200
    payload = res.json()["data"]
    assert "access_token" in payload
    assert "refresh_token" in payload
    assert payload["email"] == "admin@smartpos.com"
    assert payload["is_superadmin"] is True

def test_login_invalid_password(client):
    client.post("/api/v1/auth/setup-initial-admin")

    res = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@smartpos.com", "password": "wrongpassword"}
    )
    assert res.status_code == 401

def test_token_refresh_flow(client):
    client.post("/api/v1/auth/setup-initial-admin")

    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@smartpos.com", "password": "admin123"}
    )
    refresh_token = login_res.json()["data"]["refresh_token"]

    refresh_res = client.post(f"/api/v1/auth/refresh?refresh_token={refresh_token}")
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()["data"]

def test_get_me_profile(client):
    client.post("/api/v1/auth/setup-initial-admin")

    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@smartpos.com", "password": "admin123"}
    )
    token = login_res.json()["data"]["access_token"]

    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["data"]["email"] == "admin@smartpos.com"

def test_list_roles_and_permissions_auto_seeding(client):
    client.post("/api/v1/auth/setup-initial-admin")

    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@smartpos.com", "password": "admin123"}
    )
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    roles_res = client.get("/api/v1/users/roles", headers=headers)
    assert roles_res.status_code == 200
    roles = roles_res.json().get("data") or []
    assert len(roles) >= 5

    perms_res = client.get("/api/v1/users/permissions", headers=headers)
    assert perms_res.status_code == 200
    perms = perms_res.json().get("data") or []
    assert len(perms) >= 20

def test_create_user_and_role_assignment(client):
    client.post("/api/v1/auth/setup-initial-admin")

    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@smartpos.com", "password": "admin123"}
    )
    token = login_res.json()["data"]["access_token"]
    company_id = login_res.json()["data"]["company_id"]
    headers = {"Authorization": f"Bearer {token}"}

    roles_res = client.get("/api/v1/users/roles", headers=headers)
    roles = roles_res.json().get("data") or []
    cashier_role = next((r for r in roles if r["name"] == "Cashier"), None)
    assert cashier_role is not None

    create_user_res = client.post(
        "/api/v1/users",
        json={
            "company_id": company_id,
            "name": "John Cashier",
            "email": "john.cashier@smartpos.com",
            "password": "cashierpassword123",
            "role_ids": [cashier_role["id"]]
        },
        headers=headers
    )
    assert create_user_res.status_code == 200
    new_user = create_user_res.json()["data"]
    assert new_user["email"] == "john.cashier@smartpos.com"

    cashier_login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "john.cashier@smartpos.com", "password": "cashierpassword123"}
    )
    assert cashier_login_res.status_code == 200
    cashier_data = cashier_login_res.json()["data"]
    assert "CHECKOUT_ORDER" in cashier_data["permissions"]

def test_role_based_access_control_permission_denied(client):
    client.post("/api/v1/auth/setup-initial-admin")

    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@smartpos.com", "password": "admin123"}
    )
    admin_token = login_res.json()["data"]["access_token"]
    company_id = login_res.json()["data"]["company_id"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    roles_res = client.get("/api/v1/users/roles", headers=admin_headers)
    roles = roles_res.json().get("data") or []
    cashier_role = next((r for r in roles if r["name"] == "Cashier"), None)
    assert cashier_role is not None

    client.post(
        "/api/v1/users",
        json={
            "company_id": company_id,
            "name": "Limited User",
            "email": "limited@smartpos.com",
            "password": "limitedpassword123",
            "role_ids": [cashier_role["id"]]
        },
        headers=admin_headers
    )

    limited_login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "limited@smartpos.com", "password": "limitedpassword123"}
    )
    limited_token = limited_login_res.json()["data"]["access_token"]
    limited_headers = {"Authorization": f"Bearer {limited_token}"}

    unauthorized_res = client.post(
        "/api/v1/users",
        json={
            "company_id": company_id,
            "name": "Hacker User",
            "email": "hacker@smartpos.com",
            "password": "password123"
        },
        headers=limited_headers
    )
    assert unauthorized_res.status_code == 403

def test_company_onboarding_and_subscription_flow(client):
    client.post("/api/v1/auth/setup-initial-admin")

    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@smartpos.com", "password": "admin123"}
    )
    token = login_res.json()["data"]["access_token"]
    super_headers = {"Authorization": f"Bearer {token}"}

    # 1. Onboard new Tenant Company with max_users limit of 1
    onboard_res = client.post(
        "/api/v1/companies/onboard",
        json={
            "company_name": "Test Retail Corp",
            "admin_name": "Tenant Owner",
            "admin_email": "owner@testretail.com",
            "admin_password": "ownerpassword123",
            "subscription_plan": "starter",
            "max_users": 1
        },
        headers=super_headers
    )
    assert onboard_res.status_code == 200
    onboard_data = onboard_res.json()
    assert onboard_data["success"] is True
    assert "onboarded successfully" in onboard_data["message"]
    company_id = onboard_data["data"]["id"]

    # 2. Login as Tenant Owner and verify primary branch assignment
    owner_login = client.post(
        "/api/v1/auth/login",
        data={"username": "owner@testretail.com", "password": "ownerpassword123"}
    )
    assert owner_login.status_code == 200
    owner_token = owner_login.json()["data"]["access_token"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    me_res = client.get("/api/v1/auth/me", headers=owner_headers)
    assert me_res.status_code == 200
    user_branches = me_res.json()["data"]["branches"]
    assert len(user_branches) == 1
    assert user_branches[0]["name"] == "Main Branch"

    # 3. Tenant owner attempts to create a 2nd user (violates max_users=1 limit)
    quota_err_res = client.post(
        "/api/v1/users",
        json={
            "company_id": company_id,
            "name": "Second User",
            "email": "second@testretail.com",
            "password": "userpassword123"
        },
        headers=owner_headers
    )
    assert quota_err_res.status_code == 400
    assert "limit reached" in quota_err_res.json()["error"]

    # 4. Super Admin suspends the tenant company
    sub_res = client.patch(
        f"/api/v1/companies/{company_id}/subscription",
        json={"status": "suspended"},
        headers=super_headers
    )
    assert sub_res.status_code == 200
    assert sub_res.json()["data"]["status"] == "suspended"

    # 5. Suspended tenant owner tries to access API -> blocked with 403
    blocked_res = client.get("/api/v1/auth/me", headers=owner_headers)
    assert blocked_res.status_code == 403
    assert "suspended" in blocked_res.json()["error"]

