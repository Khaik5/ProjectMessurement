from __future__ import annotations

from app.auth.auth_schemas import RegisterRequest, UserUpdateRequest
from app.auth.auth_utils import create_access_token, hash_password, verify_password
from app.permission_database import execute_query, fetch_all, fetch_one, insert_and_get_id


def _roles_for_user(user_id: int) -> list[str]:
    rows = fetch_all(
        """
        SELECT r.RoleCode
        FROM Roles r
        JOIN UserRoles ur ON ur.RoleID = r.RoleID
        WHERE ur.UserID = ? AND r.IsActive = 1
        ORDER BY r.RoleCode
        """,
        [user_id],
    )
    return [row["RoleCode"] for row in rows]


def _permissions_for_user(user_id: int) -> list[str]:
    rows = fetch_all(
        """
        SELECT DISTINCT p.PermissionCode
        FROM Permissions p
        JOIN RolePermissions rp ON rp.PermissionID = p.PermissionID
        JOIN UserRoles ur ON ur.RoleID = rp.RoleID
        JOIN Roles r ON r.RoleID = ur.RoleID
        WHERE ur.UserID = ? AND r.IsActive = 1
        ORDER BY p.PermissionCode
        """,
        [user_id],
    )
    return [row["PermissionCode"] for row in rows]


def _public_user(user: dict) -> dict:
    user_id = int(user["UserID"])
    return {
        "user_id": user_id,
        "username": user["Username"],
        "full_name": user.get("FullName"),
        "email": user.get("Email"),
        "is_active": bool(user.get("IsActive")),
        "created_at": user.get("CreatedAt"),
        "roles": _roles_for_user(user_id),
        "permissions": _permissions_for_user(user_id),
    }


def get_user_by_id(user_id: int) -> dict | None:
    user = fetch_one("SELECT * FROM Users WHERE UserID = ? AND IsActive = 1", [user_id])
    return _public_user(user) if user else None


def get_user_by_username(username: str, include_hash: bool = False) -> dict | None:
    user = fetch_one("SELECT * FROM Users WHERE Username = ? AND IsActive = 1", [username])
    if not user:
        return None
    public = _public_user(user)
    if include_hash:
        public["password_hash"] = user["PasswordHash"]
    return public


def authenticate(username: str, password: str) -> dict | None:
    user = get_user_by_username(username, include_hash=True)
    if not user or not verify_password(password, user["password_hash"]):
        return None
    user.pop("password_hash", None)
    return user


def login(username: str, password: str) -> dict:
    user = authenticate(username, password)
    if not user:
        raise ValueError("Invalid username or password")
    token = create_access_token(
        {
            "sub": str(user["user_id"]),
            "user_id": user["user_id"],
            "username": user["username"],
            "roles": user["roles"],
            "permissions": user["permissions"],
        }
    )
    return {"access_token": token, "token_type": "bearer", "user": user}


def role_id(role_code: str) -> int:
    row = fetch_one("SELECT RoleID FROM Roles WHERE RoleCode = ? AND IsActive = 1", [role_code])
    if not row:
        raise ValueError(f"Role not found: {role_code}")
    return int(row["RoleID"])


def create_user(payload: RegisterRequest) -> dict:
    existing = fetch_one("SELECT UserID FROM Users WHERE Username = ? OR Email = ?", [payload.username, payload.email])
    if existing:
        raise ValueError("Username or email already exists")
    new_id = insert_and_get_id(
        """
        INSERT INTO Users (Username, FullName, Email, PasswordHash, IsActive, CreatedAt)
        OUTPUT INSERTED.UserID
        VALUES (?, ?, ?, ?, 1, GETDATE())
        """,
        [payload.username, payload.full_name, payload.email, hash_password(payload.password)],
    )
    execute_query(
        "INSERT INTO UserRoles (UserID, RoleID) VALUES (?, ?)",
        [new_id, role_id(payload.role)],
    )
    user = get_user_by_id(new_id)
    if not user:
        raise ValueError("User was created but could not be loaded")
    return user


def list_users() -> list[dict]:
    users = fetch_all("SELECT * FROM Users ORDER BY CreatedAt DESC")
    return [_public_user(user) for user in users]


def list_roles() -> list[dict]:
    return fetch_all("SELECT * FROM Roles WHERE IsActive = 1 ORDER BY RoleCode")


def update_user(user_id: int, payload: UserUpdateRequest) -> dict:
    user = fetch_one("SELECT UserID FROM Users WHERE UserID = ?", [user_id])
    if not user:
        raise ValueError("User not found")
    assignments = []
    params = []
    if payload.full_name is not None:
        assignments.append("FullName = ?")
        params.append(payload.full_name)
    if payload.email is not None:
        assignments.append("Email = ?")
        params.append(payload.email)
    if payload.password is not None:
        assignments.append("PasswordHash = ?")
        params.append(hash_password(payload.password))
    if payload.is_active is not None:
        assignments.append("IsActive = ?")
        params.append(int(payload.is_active))
    if assignments:
        execute_query(f"UPDATE Users SET {', '.join(assignments)} WHERE UserID = ?", [*params, user_id])
    if payload.role:
        execute_query("DELETE FROM UserRoles WHERE UserID = ?", [user_id])
        execute_query("INSERT INTO UserRoles (UserID, RoleID) VALUES (?, ?)", [user_id, role_id(payload.role)])
    updated = get_user_by_id(user_id)
    if not updated:
        inactive = fetch_one("SELECT * FROM Users WHERE UserID = ?", [user_id])
        return _public_user(inactive) if inactive else {}
    return updated


def soft_delete_user(user_id: int) -> dict:
    affected = execute_query("UPDATE Users SET IsActive = 0 WHERE UserID = ?", [user_id])
    return {"deleted": affected > 0}

