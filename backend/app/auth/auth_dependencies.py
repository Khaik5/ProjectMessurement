from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.auth import auth_service
from app.auth.auth_utils import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> dict:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user_id = payload.get("user_id") or payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = auth_service.get_user_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive or not found")
    return user


def require_permission(permission_code: str | list[str]) -> Callable:
    """
    Dependency để kiểm tra permission
    Hỗ trợ cả single permission hoặc list permissions (OR logic)
    """
    def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        roles = set(current_user.get("roles") or [])
        permissions = set(current_user.get("permissions") or [])
        
        # Admin có toàn quyền
        if "Admin" in roles:
            return current_user
        
        # Kiểm tra permission
        if isinstance(permission_code, list):
            # OR logic: có ít nhất 1 permission trong list
            if any(perm in permissions for perm in permission_code):
                return current_user
        else:
            # Single permission
            if permission_code in permissions:
                return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission_code} is required",
        )

    return dependency


class RoleChecker:
    """
    Dependency class để kiểm tra role của user
    Sử dụng: dependencies=[Depends(RoleChecker(["Admin", "Developer"]))]
    """
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: dict = Depends(get_current_user)) -> dict:
        user_roles = set(current_user.get("roles") or [])
        
        # Kiểm tra xem user có ít nhất 1 role trong allowed_roles
        if not user_roles.intersection(self.allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(self.allowed_roles)}",
            )
        
        return current_user

