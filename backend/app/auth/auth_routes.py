from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth import auth_service
from app.auth.auth_dependencies import get_current_user, require_permission, RoleChecker
from app.auth.auth_schemas import LoginRequest, PublicRegisterRequest, RegisterRequest, UserRoleUpdateRequest, UserUpdateRequest
from app.utils.response_utils import api_success

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
def login(payload: LoginRequest):
    return api_success(auth_service.login(payload.username, payload.password), "Login successful")


@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):
    return api_success({"username": current_user["username"]}, "Logout successful")


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return api_success(current_user)


@router.post("/register")
def register(payload: RegisterRequest, current_user: dict = Depends(require_permission("USER_MANAGE"))):
    return api_success(auth_service.create_user(payload), "User created successfully")


@router.post("/public-register")
def public_register(payload: PublicRegisterRequest):
    """Public registration endpoint - không yêu cầu authentication"""
    return api_success(auth_service.create_public_user(payload), "Registration successful")


@router.get("/users")
def users(current_user: dict = Depends(require_permission("USER_MANAGE"))):
    return api_success(auth_service.list_users())


@router.put("/users/{user_id}")
def update_user(user_id: int, payload: UserUpdateRequest, current_user: dict = Depends(require_permission("USER_MANAGE"))):
    return api_success(auth_service.update_user(user_id, payload), "User updated")


@router.patch("/users/{user_id}/role")
def update_user_role(user_id: int, payload: UserRoleUpdateRequest, current_user: dict = Depends(RoleChecker(["Admin"]))):
    """
    API chỉ dành cho ADMIN để thay đổi role của user
    """
    return api_success(auth_service.update_user_role(user_id, payload.role), "User role updated successfully")


@router.delete("/users/{user_id}")
def delete_user(user_id: int, current_user: dict = Depends(require_permission("USER_MANAGE"))):
    return api_success(auth_service.soft_delete_user(user_id), "User deleted")


@router.get("/roles")
def roles(current_user: dict = Depends(require_permission("USER_MANAGE"))):
    return api_success(auth_service.list_roles())

