from fastapi import HTTPException

from app.schemas.report_schema import ReportGenerateRequest
from app.services import export_service, report_service


def list_reports(project_id: int | None = None):
    return report_service.list_reports(project_id)


def get_report(report_id: int):
    report = report_service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


def generate(payload: ReportGenerateRequest):
    return report_service.generate(payload)


def export_pdf(report_id: int):
    return export_service.report_pdf(report_id)


def export_csv(report_id: int):
    return export_service.report_csv(report_id)


def export_xlsx(report_id: int):
    return export_service.report_xlsx(report_id)


def delete(report_id: int, user_id: int | None = None):
    return report_service.delete(report_id, user_id)


def export_dataset_pdf(dataset_id: int):
    return export_service.dataset_pdf(dataset_id)


def export_dataset_csv(dataset_id: int):
    return export_service.dataset_csv(dataset_id)


def export_dataset_xlsx(dataset_id: int):
    return export_service.dataset_xlsx(dataset_id)
