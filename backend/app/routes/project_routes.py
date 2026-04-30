from fastapi import APIRouter

from app.controllers import project_controller
from app.schemas.project_schema import ProjectCreate, ProjectStateUpdate, ProjectUpdate
from app.utils.response_utils import api_success

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("")
def list_projects():
    return api_success(project_controller.list_projects())


@router.get("/{project_id}")
def get_project(project_id: int):
    return api_success(project_controller.get_project(project_id))


@router.get("/{project_id}/state")
def get_state(project_id: int):
    return api_success(project_controller.get_state(project_id))


@router.post("")
def create_project(payload: ProjectCreate):
    return api_success(project_controller.create_project(payload), "Project created")


@router.put("/{project_id}")
def update_project(project_id: int, payload: ProjectUpdate):
    return api_success(project_controller.update_project(project_id, payload), "Project updated")


@router.put("/{project_id}/state")
def update_state(project_id: int, payload: ProjectStateUpdate):
    return api_success(project_controller.update_state(project_id, payload), "Project state updated")


@router.delete("/{project_id}")
def delete_project(project_id: int):
    return api_success(project_controller.delete_project(project_id), "Project deleted")
