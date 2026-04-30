from app.database import execute_query, fetch_all, fetch_one, insert_and_get_id
from app.repositories import project_state_repository


def list_projects():
    return fetch_all("SELECT * FROM Projects ORDER BY is_active DESC, created_at DESC")


def get_project(project_id: int):
    return fetch_one("SELECT * FROM Projects WHERE id = ?", [project_id])


def get_project_state(project_id: int):
    return project_state_repository.get_state(project_id)


def update_project_state(project_id: int, payload: dict):
    return project_state_repository.update_state(
        project_id,
        current_dataset_id=payload.get("current_dataset_id"),
        current_model_id=payload.get("current_model_id"),
        current_analysis_dataset_id=payload.get("current_analysis_dataset_id"),
    )


def create_project(name: str, description: str | None, owner_id: int | None):
    return insert_and_get_id(
        """
        INSERT INTO Projects (name, description, owner_id, is_active, created_at, updated_at)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, 0, GETDATE(), GETDATE())
        """,
        [name, description, owner_id],
    )


def update_project(project_id: int, name: str | None, description: str | None, is_active: bool | None):
    current = get_project(project_id)
    if not current:
        return 0
    return execute_query(
        """
        UPDATE Projects
        SET name = ?, description = ?, is_active = ?, updated_at = GETDATE()
        WHERE id = ?
        """,
        [
            name if name is not None else current["name"],
            description if description is not None else current["description"],
            int(is_active) if is_active is not None else int(current["is_active"]),
            project_id,
        ],
    )


def delete_project(project_id: int):
    return execute_query("DELETE FROM Projects WHERE id = ?", [project_id])
