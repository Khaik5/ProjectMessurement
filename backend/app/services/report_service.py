from __future__ import annotations

import json

from app.repositories import prediction_repository, report_repository
from app.repositories import project_state_repository
from app.schemas.report_schema import ReportGenerateRequest
from app.services.audit_service import log_action
from app.services.dashboard_service import summary


def list_reports(project_id: int | None = None):
    return report_repository.list_reports(project_id)


def get_report(report_id: int):
    return report_repository.get_report(report_id)


def generate(payload: ReportGenerateRequest):
    dataset_id = payload.dataset_id
    if not dataset_id:
        state = project_state_repository.get_state(payload.project_id)
        dataset_id = state.get("current_analysis_dataset_id") if state else None
    if not dataset_id:
        raise ValueError("No analysis selected. Analyze a dataset before generating a report.")
    predictions = prediction_repository.by_dataset(dataset_id)
    if payload.risk_level:
        predictions = [row for row in predictions if row.get("risk_level") == payload.risk_level]
    if payload.model_id:
        predictions = [row for row in predictions if row.get("model_id") == payload.model_id]
    risk_counts = {}
    for row in predictions:
        risk_counts[row["risk_level"]] = risk_counts.get(row["risk_level"], 0) + 1
    report_summary = {
        "dashboard": summary(payload.project_id, dataset_id),
        "dataset_id": dataset_id,
        "risk_counts": risk_counts,
        "prediction_rows": len(predictions),
        "critical_modules": [row["module_name"] for row in predictions if row["risk_level"] == "CRITICAL"][:10],
    }
    report_id = report_repository.create_report(
        payload.project_id,
        payload.generated_by_id,
        payload.title,
        payload.model_copy(update={"dataset_id": dataset_id}).model_dump_json(),
        json.dumps(report_summary, ensure_ascii=False, default=str),
    )
    log_action("report.generated", "Report", report_id, payload.project_id, payload.generated_by_id, {"prediction_rows": len(predictions)})
    return report_repository.get_report(report_id)


def delete(report_id: int, user_id: int | None = None):
    report = report_repository.get_report(report_id)
    if not report:
        raise ValueError("Report not found")
    affected = report_repository.soft_delete(report_id, user_id)
    log_action("report.deleted", "Report", report_id, report.get("project_id"), user_id, {"soft_delete": True})
    return {"deleted": affected > 0}
