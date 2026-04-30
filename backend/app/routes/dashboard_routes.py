from fastapi import APIRouter, Depends, Query

from app.auth.auth_dependencies import require_permission
from app.controllers import dashboard_controller
from app.utils.response_utils import api_success

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def summary(project_id: int = Query(default=1), dataset_id: int | None = Query(default=None), current_user: dict = Depends(require_permission("DASHBOARD_VIEW"))):
    data = dashboard_controller.summary(project_id, dataset_id)
    return api_success(data, data.get("message", "OK") if isinstance(data, dict) else "OK")


@router.get("/charts")
def charts(project_id: int = Query(default=1), dataset_id: int | None = Query(default=None), current_user: dict = Depends(require_permission("DASHBOARD_VIEW"))):
    data = dashboard_controller.charts(project_id, dataset_id)
    return api_success(data, data.get("message", "OK") if isinstance(data, dict) else "OK")


@router.get("/risk-distribution")
def risk_distribution(project_id: int = Query(default=1), dataset_id: int | None = Query(default=None), current_user: dict = Depends(require_permission("DASHBOARD_VIEW"))):
    return api_success(dashboard_controller.risk_distribution(project_id, dataset_id))


@router.get("/top-risk-modules")
def top_risk_modules(project_id: int = Query(default=1), dataset_id: int | None = Query(default=None), current_user: dict = Depends(require_permission("DASHBOARD_VIEW"))):
    return api_success(dashboard_controller.top_risk_modules(project_id, dataset_id))


@router.get("/probability-trend")
def probability_trend(project_id: int = Query(default=1), dataset_id: int | None = Query(default=None), current_user: dict = Depends(require_permission("DASHBOARD_VIEW"))):
    return api_success(dashboard_controller.probability_trend(project_id, dataset_id))


@router.get("/risk-heatmap")
def risk_heatmap(project_id: int = Query(default=1), dataset_id: int | None = Query(default=None), current_user: dict = Depends(require_permission("DASHBOARD_VIEW"))):
    return api_success(dashboard_controller.risk_heatmap(project_id, dataset_id))


@router.get("/model-performance")
def model_performance(project_id: int = Query(default=1), current_user: dict = Depends(require_permission("MODEL_COMPARISON_VIEW"))):
    return api_success(dashboard_controller.model_performance(project_id))
