from fastapi import APIRouter

from app.controllers import metric_controller
from app.utils.response_utils import api_success

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("")
def list_metrics():
    return api_success(metric_controller.list_metrics())


@router.get("/project/{project_id}")
def project_metrics(project_id: int):
    return api_success(metric_controller.project_metrics(project_id))


@router.get("/dataset/{dataset_id}")
def dataset_metrics(dataset_id: int):
    return api_success(metric_controller.dataset_metrics(dataset_id))


@router.get("/statistics/{project_id}")
def statistics(project_id: int):
    return api_success(metric_controller.statistics(project_id))


@router.get("/{record_id}")
def get_metric(record_id: int):
    return api_success(metric_controller.get_metric(record_id))
