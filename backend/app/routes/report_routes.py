from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.auth.auth_dependencies import require_permission
from app.controllers import report_controller
from app.schemas.report_schema import ReportGenerateRequest
from app.utils.response_utils import api_success

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("")
def list_reports(project_id: int | None = Query(default=None), current_user: dict = Depends(require_permission("REPORT_VIEW"))):
    return api_success(report_controller.list_reports(project_id))


@router.post("/generate")
def generate(payload: ReportGenerateRequest, current_user: dict = Depends(require_permission("REPORT_VIEW"))):
    payload.generated_by_id = current_user.get("user_id")
    return api_success(report_controller.generate(payload), "Report generated")


@router.get("/{report_id}")
def get_report(report_id: int, current_user: dict = Depends(require_permission("REPORT_VIEW"))):
    return api_success(report_controller.get_report(report_id))


@router.get("/{report_id}/export/pdf")
def export_pdf(report_id: int, current_user: dict = Depends(require_permission("REPORT_EXPORT"))):
    return Response(report_controller.export_pdf(report_id), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=report_{report_id}.pdf"})


@router.get("/{report_id}/export/csv")
def export_csv(report_id: int, current_user: dict = Depends(require_permission("REPORT_EXPORT"))):
    return Response(report_controller.export_csv(report_id), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=report_{report_id}.csv"})


@router.get("/{report_id}/export/xlsx")
def export_xlsx(report_id: int, current_user: dict = Depends(require_permission("REPORT_EXPORT"))):
    return Response(report_controller.export_xlsx(report_id), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename=report_{report_id}.xlsx"})


@router.get("/dataset/{dataset_id}/export/pdf")
def export_dataset_pdf(dataset_id: int, current_user: dict = Depends(require_permission("REPORT_EXPORT"))):
    return Response(report_controller.export_dataset_pdf(dataset_id), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=dataset_{dataset_id}_report.pdf"})


@router.get("/dataset/{dataset_id}/export/csv")
def export_dataset_csv(dataset_id: int, current_user: dict = Depends(require_permission("REPORT_EXPORT"))):
    return Response(report_controller.export_dataset_csv(dataset_id), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=dataset_{dataset_id}_predictions.csv"})


@router.get("/dataset/{dataset_id}/export/xlsx")
def export_dataset_xlsx(dataset_id: int, current_user: dict = Depends(require_permission("REPORT_EXPORT"))):
    return Response(report_controller.export_dataset_xlsx(dataset_id), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename=dataset_{dataset_id}_report.xlsx"})


@router.delete("/{report_id}")
def delete_report(report_id: int, current_user: dict = Depends(require_permission("REPORT_DELETE"))):
    return api_success(report_controller.delete(report_id, current_user.get("user_id")), "Report deleted")
