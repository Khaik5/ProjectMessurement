from app.database import fetch_all, insert_and_get_id


def create_audit_log(user_id: int | None, project_id: int | None, action: str, entity_type: str | None, entity_id: int | None, details_json: str | None, ip_address: str | None = None):
    return insert_and_get_id(
        """
        INSERT INTO AuditLogs (user_id, project_id, action, entity_type, entity_id, details_json, ip_address, created_at)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE())
        """,
        [user_id, project_id, action, entity_type, entity_id, details_json, ip_address],
    )


def list_audit_logs(limit: int = 100):
    return fetch_all("SELECT TOP (?) * FROM AuditLogs ORDER BY created_at DESC", [limit])


def by_project(project_id: int, limit: int = 100):
    return fetch_all("SELECT TOP (?) * FROM AuditLogs WHERE project_id = ? ORDER BY created_at DESC", [limit, project_id])
