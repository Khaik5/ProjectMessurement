from app.schemas.prediction_schema import PredictionRunRequest, PredictionSingleRequest
from app.services import prediction_service


def run(payload: PredictionRunRequest):
    return prediction_service.predict_batch(payload)


def single(payload: PredictionSingleRequest):
    return prediction_service.predict_single(payload)


def list_predictions():
    return prediction_service.list_predictions()


def project_predictions(project_id: int):
    return prediction_service.project_predictions(project_id)


def dataset_predictions(dataset_id: int):
    return prediction_service.dataset_predictions(dataset_id)


def top_risk(project_id: int = 1):
    return prediction_service.top_risk(project_id)


def recent():
    return prediction_service.recent()
