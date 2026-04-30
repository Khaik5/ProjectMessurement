from fastapi import APIRouter, Depends, Query

from app.auth.auth_dependencies import require_permission
from app.controllers import prediction_controller
from app.schemas.prediction_schema import PredictionRunRequest, PredictionSingleRequest
from app.utils.response_utils import api_success

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.post("/run")
def run(payload: PredictionRunRequest, current_user: dict = Depends(require_permission("MODEL_TEST"))):
    return api_success(prediction_controller.run(payload), "Dataset analyzed successfully")


@router.post("/single")
def single(payload: PredictionSingleRequest, current_user: dict = Depends(require_permission("MODEL_TEST"))):
    return api_success(prediction_controller.single(payload), "Prediction completed")


@router.get("")
def list_predictions():
    return api_success(prediction_controller.list_predictions())


@router.get("/project/{project_id}")
def project_predictions(project_id: int):
    return api_success(prediction_controller.project_predictions(project_id))


@router.get("/dataset/{dataset_id}")
def dataset_predictions(dataset_id: int):
    data = prediction_controller.dataset_predictions(dataset_id)
    return api_success(data, data.get("message", "OK"))


@router.get("/top-risk")
def top_risk(project_id: int = Query(default=1)):
    return api_success(prediction_controller.top_risk(project_id))


@router.get("/recent")
def recent():
    return api_success(prediction_controller.recent())
