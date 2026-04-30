from app.services import dashboard_service


def summary(project_id: int, dataset_id: int | None = None):
    return dashboard_service.summary(project_id, dataset_id)


def charts(project_id: int, dataset_id: int | None = None):
    return dashboard_service.charts(project_id, dataset_id)


def risk_distribution(project_id: int, dataset_id: int | None = None):
    return dashboard_service.risk_distribution(project_id, dataset_id)


def top_risk_modules(project_id: int, dataset_id: int | None = None):
    return dashboard_service.top_risk_modules(project_id, dataset_id)


def probability_trend(project_id: int, dataset_id: int | None = None):
    return dashboard_service.probability_trend(project_id, dataset_id)


def risk_heatmap(project_id: int, dataset_id: int | None = None):
    return dashboard_service.risk_heatmap(project_id, dataset_id)


def model_performance(project_id: int):
    return dashboard_service.model_performance(project_id)
