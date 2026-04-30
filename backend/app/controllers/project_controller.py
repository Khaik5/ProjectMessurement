from fastapi import HTTPException

from app.schemas.project_schema import ProjectCreate, ProjectStateUpdate, ProjectUpdate
from app.services import project_service


def list_projects():
    return project_service.list_projects()


def get_project(project_id: int):
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def create_project(payload: ProjectCreate):
    return project_service.create_project(payload)


def update_project(project_id: int, payload: ProjectUpdate):
    return project_service.update_project(project_id, payload)


def delete_project(project_id: int):
    return project_service.delete_project(project_id)


def get_state(project_id: int):
    return project_service.get_state(project_id)


def update_state(project_id: int, payload: ProjectStateUpdate):
    return project_service.update_state(project_id, payload)
