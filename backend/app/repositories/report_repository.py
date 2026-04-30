from app.database import execute_query, fetch_all, fetch_one, insert_and_get_id


def list_reports(project_id: int | None = None):
    base = "SELECT * FROM Reports WHERE ISNULL(IsDeleted, 0) = 0"
    params = []
    if project_id:
        base += " AND project_id = ?"
        params.append(project_id)
    base += " ORDER BY created_at DESC"
    return fetch_all(base, params)


def get_report(report_id: int):
    return fetch_one("SELECT * FROM Reports WHERE id = ? AND ISNULL(IsDeleted, 0) = 0", [report_id])


def create_report(project_id: int, generated_by_id: int | None, title: str, filters_json: str, summary_json: str, file_path: str | None = None):
    return insert_and_get_id(
        """
        INSERT INTO Reports (project_id, generated_by_id, title, filters_json, summary_json, file_path, created_at)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?, ?, GETDATE())
        """,
        [project_id, generated_by_id, title, filters_json, summary_json, file_path],
    )


def soft_delete(report_id: int, user_id: int | None = None):
    return execute_query(
        """
        UPDATE Reports
        SET IsDeleted = 1, DeletedAt = GETDATE(), DeletedBy = ?
        WHERE id = ?
        """,
        [user_id, report_id],
    )
