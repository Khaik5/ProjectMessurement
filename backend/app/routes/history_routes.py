from fastapi import APIRouter, Depends, Query

from app.auth.auth_dependencies import require_permission
from app.controllers import history_controller
from app.utils.response_utils import api_success

router = APIRouter(prefix="/history", tags=["History"])


@router.get("")
def history(project_id: int = Query(default=1), current_user: dict = Depends(require_permission("HISTORY_VIEW"))):
    return api_success(history_controller.list_history(project_id))


@router.get("/{dataset_id}")
def history_item(dataset_id: int, current_user: dict = Depends(require_permission("HISTORY_VIEW"))):
    return api_success(history_controller.get_history_item(dataset_id))


@router.post("/{dataset_id}/set-current")
def set_current(dataset_id: int, current_user: dict = Depends(require_permission("HISTORY_VIEW"))):
    return api_success(history_controller.set_current(dataset_id), "Current dataset updated")


@router.post("/{dataset_id}/reanalyze")
def reanalyze(dataset_id: int, project_id: int = Query(default=1), model_id: int | None = Query(default=None), current_user: dict = Depends(require_permission("MODEL_TEST"))):
    return api_success(history_controller.reanalyze(project_id, dataset_id, model_id), "Dataset re-analyzed")


@router.delete("/{dataset_id}")
def archive(dataset_id: int, current_user: dict = Depends(require_permission("HISTORY_DELETE"))):
    return api_success(history_controller.archive(dataset_id), "Dataset archived")
