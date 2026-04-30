from fastapi import HTTPException

from app.services import metric_service


def list_metrics():
    return metric_service.list_metrics()


def get_metric(record_id: int):
    metric = metric_service.get_metric(record_id)
    if not metric:
        raise HTTPException(status_code=404, detail="Metric record not found")
    return metric


def project_metrics(project_id: int):
    return metric_service.project_metrics(project_id)


def dataset_metrics(dataset_id: int):
    return metric_service.dataset_metrics(dataset_id)


def statistics(project_id: int):
    return metric_service.statistics(project_id)
