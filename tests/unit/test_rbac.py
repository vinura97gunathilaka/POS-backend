import pytest
from app.models.auth import User, Role, Permission, UserRole, RolePermission
from app.models.organization import Company, Branch
from app.api.deps import PermissionChecker
from fastapi import HTTPException

def test_permission_checker_superadmin(db):
    user = User(company_id=1, email="sa@test.com", name="SA", hashed_password="pw", is_superadmin=True)
    checker = PermissionChecker("CREATE_USER")
    res = checker(current_user=user, db=db)
    assert res.is_superadmin is True

def test_permission_checker_assigned_role(db):
    company = Company(name="Test Corp")
    db.add(company)
    db.flush()

    perm = Permission(company_id=company.id, name="Create User", code="CREATE_USER")
    db.add(perm)
    db.flush()

    role = Role(company_id=company.id, name="Admin")
    db.add(role)
    db.flush()

    rp = RolePermission(company_id=company.id, role_id=role.id, permission_id=perm.id)
    db.add(rp)

    user = User(company_id=company.id, email="user@test.com", name="User", hashed_password="pw")
    db.add(user)
    db.flush()

    ur = UserRole(company_id=company.id, user_id=user.id, role_id=role.id)
    db.add(ur)
    db.commit()

    db.refresh(user)

    checker = PermissionChecker("CREATE_USER")
    result = checker(current_user=user, db=db)
    assert result.id == user.id

def test_permission_checker_missing_permission(db):
    company = Company(name="Test Corp 2")
    db.add(company)
    db.flush()

    role = Role(company_id=company.id, name="Waiter")
    db.add(role)
    db.flush()

    user = User(company_id=company.id, email="waiter@test.com", name="Waiter", hashed_password="pw")
    db.add(user)
    db.flush()

    ur = UserRole(company_id=company.id, user_id=user.id, role_id=role.id)
    db.add(ur)
    db.commit()

    db.refresh(user)

    checker = PermissionChecker("DELETE_USER")
    with pytest.raises(HTTPException) as exc_info:
        checker(current_user=user, db=db)
    assert exc_info.value.status_code == 403

