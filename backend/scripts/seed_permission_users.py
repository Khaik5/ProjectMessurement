from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.auth.auth_utils import hash_password
from app.permission_database import execute_query, fetch_one


USERS = [
    ("admin", "System Administrator", "admin@defectai.local", "Admin@123", "Admin"),
    *[(f"dev{i:02d}", f"Developer {i:02d}", f"dev{i:02d}@defectai.local", "Dev@123", "Developer") for i in range(1, 5)],
    *[(f"viewer{i:02d}", f"Viewer {i:02d}", f"viewer{i:02d}@defectai.local", "Viewer@123", "Viewer") for i in range(1, 11)],
]


def role_id(role_code: str) -> int:
    row = fetch_one("SELECT RoleID FROM Roles WHERE RoleCode = ?", [role_code])
    if not row:
        raise RuntimeError(f"Role not found. Run seed_permission_data.sql first: {role_code}")
    return int(row["RoleID"])


def upsert_user(username: str, full_name: str, email: str, password: str, role: str) -> None:
    existing = fetch_one("SELECT UserID FROM Users WHERE Username = ?", [username])
    password_hash = hash_password(password)
    if existing:
        user_id = int(existing["UserID"])
        execute_query(
            "UPDATE Users SET FullName = ?, Email = ?, PasswordHash = ?, IsActive = 1 WHERE UserID = ?",
            [full_name, email, password_hash, user_id],
        )
    else:
        execute_query(
            """
            INSERT INTO Users (Username, FullName, Email, PasswordHash, IsActive, CreatedAt)
            VALUES (?, ?, ?, ?, 1, GETDATE())
            """,
            [username, full_name, email, password_hash],
        )
        user_id = int(fetch_one("SELECT UserID FROM Users WHERE Username = ?", [username])["UserID"])
    rid = role_id(role)
    execute_query("DELETE FROM UserRoles WHERE UserID = ?", [user_id])
    execute_query("INSERT INTO UserRoles (UserID, RoleID) VALUES (?, ?)", [user_id, rid])


def main() -> None:
    for user in USERS:
        upsert_user(*user)
    print(f"Seeded {len(USERS)} PermissionDB users with bcrypt password hashes.")


if __name__ == "__main__":
    main()

