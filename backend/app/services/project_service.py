from app.repositories import project_repository
from app.schemas.project_schema import ProjectCreate, ProjectStateUpdate, ProjectUpdate
from app.services.audit_service import log_action


def list_projects():
    return project_repository.list_projects()


def get_project(project_id: int):
    return project_repository.get_project(project_id)


def create_project(payload: ProjectCreate):
    project_id = project_repository.create_project(payload.name, payload.description, payload.owner_id)
    log_action("project.created", "Project", project_id, project_id, details=payload.model_dump())
    return get_project(project_id)


def update_project(project_id: int, payload: ProjectUpdate):
    project_repository.update_project(project_id, payload.name, payload.description, payload.is_active)
    log_action("project.updated", "Project", project_id, project_id, details=payload.model_dump(exclude_unset=True))
    return get_project(project_id)


def delete_project(project_id: int):
    affected = project_repository.delete_project(project_id)
    log_action("project.deleted", "Project", project_id, project_id)
    return {"deleted": affected > 0}


def get_state(project_id: int):
    return project_repository.get_project_state(project_id)


def update_state(project_id: int, payload: ProjectStateUpdate):
    state = project_repository.update_project_state(project_id, payload.model_dump(exclude_unset=True))
    log_action("project.state.updated", "ProjectState", state["id"], project_id, details=payload.model_dump(exclude_unset=True))
    return state
