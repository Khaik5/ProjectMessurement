from fastapi import APIRouter, Depends

from app.auth.auth_dependencies import require_permission
from app.controllers import ml_controller
from app.schemas.model_schema import TrainingRequest
from app.utils.response_utils import api_success

router = APIRouter(prefix="/ml", tags=["ML"])


@router.post("/train")
def train(payload: TrainingRequest, current_user: dict = Depends(require_permission("MODEL_TRAIN"))):
    return api_success(ml_controller.train(payload), "Training completed")


@router.post("/train-production")
def train_production(payload: TrainingRequest, current_user: dict = Depends(require_permission("MODEL_TRAIN"))):
    return api_success(ml_controller.train_production(payload), "Production model trained")


@router.get("/models")
def list_models(project_id: int = 1):
    return api_success(ml_controller.list_models())


@router.get("/models/{model_id}")
def get_model(model_id: int):
    return api_success(ml_controller.get_model(model_id))


@router.put("/models/{model_id}/activate")
def activate(model_id: int, current_user: dict = Depends(require_permission("MODEL_DEPLOY"))):
    return api_success(ml_controller.activate(model_id), "Active model updated")


@router.post("/models/{model_id}/activate")
def activate_post(model_id: int, current_user: dict = Depends(require_permission("MODEL_DEPLOY"))):
    return api_success(ml_controller.activate(model_id), "Active model updated")


@router.get("/training-runs")
def training_runs(project_id: int = 1):
    return api_success(ml_controller.training_runs())


@router.get("/training-runs/{run_id}")
def training_run(run_id: int):
    return api_success(ml_controller.training_run(run_id))


@router.get("/comparison")
def comparison(project_id: int = 1, dataset_id: int | None = None):
    return api_success(ml_controller.comparison(dataset_id))


@router.get("/model-comparison")
def model_comparison(project_id: int = 1, dataset_id: int | None = None):
    return api_success(ml_controller.comparison(dataset_id))


@router.delete("/models/{model_id}")
def delete_model(model_id: int, current_user: dict = Depends(require_permission("MODEL_DELETE"))):
    return api_success(ml_controller.delete_model(model_id), "Model deleted")


@router.delete("/training-runs/{run_id}")
def delete_training_run(run_id: int, current_user: dict = Depends(require_permission("MODEL_DELETE"))):
    return api_success(ml_controller.delete_training_run(run_id), "Training run deleted")


@router.post("/training-runs/{run_id}/restore")
def restore_training_run(run_id: int):
    return api_success(ml_controller.restore_training_run(run_id), "Training run restored")


@router.get("/trainable-datasets")
def trainable_datasets(project_id: int = 1):
    return api_success(ml_controller.trainable_datasets(project_id))


@router.get("/training-guide")
def training_guide():
    return api_success(ml_controller.training_guide())
