from app.database import execute_query, fetch_one


def get_state(project_id: int):
    state = fetch_one("SELECT * FROM ProjectState WHERE project_id = ?", [project_id])
    if state:
        return state
    execute_query(
        "INSERT INTO ProjectState (project_id, current_dataset_id, current_model_id, current_analysis_dataset_id, updated_at) VALUES (?, NULL, NULL, NULL, GETDATE())",
        [project_id],
    )
    return fetch_one("SELECT * FROM ProjectState WHERE project_id = ?", [project_id])


def update_state(project_id: int, current_dataset_id=None, current_model_id=None, current_analysis_dataset_id=None):
    get_state(project_id)
    current = get_state(project_id)
    execute_query(
        """
        UPDATE ProjectState
        SET current_dataset_id = ?, current_model_id = ?, current_analysis_dataset_id = ?, updated_at = GETDATE()
        WHERE project_id = ?
        """,
        [
            current_dataset_id if current_dataset_id is not None else current.get("current_dataset_id"),
            current_model_id if current_model_id is not None else current.get("current_model_id"),
            current_analysis_dataset_id if current_analysis_dataset_id is not None else current.get("current_analysis_dataset_id"),
            project_id,
        ],
    )
    return get_state(project_id)
