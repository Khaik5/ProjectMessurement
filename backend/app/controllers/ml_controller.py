from fastapi import HTTPException

from app.schemas.model_schema import TrainingRequest
from app.services import ml_training_service


def train(payload: TrainingRequest):
    return ml_training_service.train(payload)


def train_production(payload: TrainingRequest):
    return ml_training_service.train_production(payload)


def list_models():
    return ml_training_service.list_models()


def get_model(model_id: int):
    model = ml_training_service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


def activate(model_id: int):
    return ml_training_service.activate(model_id)


def training_runs():
    return ml_training_service.training_runs()


def training_run(run_id: int):
    run = ml_training_service.training_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Training run not found")
    return run


def comparison(dataset_id: int | None = None):
    return ml_training_service.comparison(dataset_id)


def trainable_datasets(project_id: int):
    return ml_training_service.trainable_datasets(project_id)


def training_guide():
    return ml_training_service.training_guide()


def delete_model(model_id: int):
    return ml_training_service.delete_model(model_id)


def delete_training_run(run_id: int):
    return ml_training_service.delete_training_run(run_id)


def restore_training_run(run_id: int):
    return ml_training_service.restore_training_run(run_id)
