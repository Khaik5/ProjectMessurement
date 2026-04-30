from fastapi import HTTPException

from app.repositories import dataset_repository, project_state_repository
from app.schemas.prediction_schema import PredictionRunRequest
from app.services import prediction_service
from app.services.audit_service import log_action


def list_history(project_id: int = 1):
    return dataset_repository.history(project_id)


def get_history_item(dataset_id: int):
    summary = dataset_repository.analysis_summary(dataset_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return summary


def set_current(dataset_id: int):
    dataset = dataset_repository.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    state = project_state_repository.update_state(dataset["project_id"], current_analysis_dataset_id=dataset_id, current_dataset_id=dataset_id)
    log_action("history.set_current", "MetricsDataset", dataset_id, dataset["project_id"])
    return state


def reanalyze(project_id: int, dataset_id: int, model_id: int | None = None):
    payload = PredictionRunRequest(project_id=project_id, dataset_id=dataset_id, model_id=model_id)
    return prediction_service.predict_batch(payload)


def archive(dataset_id: int):
    affected = dataset_repository.delete_dataset(dataset_id)
    log_action("history.archived", "MetricsDataset", dataset_id)
    return {"archived": affected > 0}

