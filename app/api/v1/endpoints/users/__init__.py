from fastapi import APIRouter
from app.api.v1.endpoints.users.permissions import (
    router as permissions_router,
    seed_company_permissions_and_roles,
    SYSTEM_PERMISSIONS,
    STANDARD_ROLES,
    list_permissions,
    get_permission_by_id,
    create_permission,
    update_permission,
    delete_permission,
)
from app.api.v1.endpoints.users.roles import (
    router as roles_router,
    list_roles,
    get_role_by_id,
    create_role,
    update_role,
    delete_role,
    assign_role_permissions,
)
from app.api.v1.endpoints.users.users import (
    router as users_router,
    generate_next_employee_id,
    list_users,
    get_user_by_id,
    create_user,
    update_user,
    delete_user,
    assign_user_roles,
)

router = APIRouter()

# Note: Roles and Permissions must be included before Users so that /roles and /permissions
# routes are matched before the generic user /{id} route.
router.include_router(roles_router)
router.include_router(permissions_router)
router.include_router(users_router)

__all__ = [
    "router",
    "seed_company_permissions_and_roles",
    "SYSTEM_PERMISSIONS",
    "STANDARD_ROLES",
    "list_permissions",
    "get_permission_by_id",
    "create_permission",
    "update_permission",
    "delete_permission",
    "list_roles",
    "get_role_by_id",
    "create_role",
    "update_role",
    "delete_role",
    "assign_role_permissions",
    "generate_next_employee_id",
    "list_users",
    "get_user_by_id",
    "create_user",
    "update_user",
    "delete_user",
    "assign_user_roles",
]
