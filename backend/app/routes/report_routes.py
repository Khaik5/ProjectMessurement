from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.auth.auth_dependencies import require_permission, RoleChecker
from app.controllers import report_controller
from app.schemas.report_schema import ExportMultipleReportsRequest, ReportExportRequest, ReportGenerateRequest
from app.utils.response_utils import api_success

router = APIRouter(prefix="/reports", tags=["Reports"])


def _attachment(filename: str):
    return {"Content-Disposition": f'attachment; filename="{filename}"'}


def _query_export_payload(
    dataset_id: int,
    include_full_modules: bool = True,
    include_heatmap: bool = True,
    include_charts: bool = True,
    top_n: int = 20,
) -> ReportExportRequest:
    return ReportExportRequest(
        dataset_id=dataset_id,
        include_full_modules=include_full_modules,
        include_heatmap=include_heatmap,
        include_charts=include_charts,
        top_n=top_n,
    )


@router.get("")
def list_reports(project_id: int | None = Query(default=None), current_user: dict = Depends(require_permission("REPORT_VIEW"))):
    return api_success(report_controller.list_reports(project_id))


@router.post("/generate")
def generate(payload: ReportGenerateRequest, current_user: dict = Depends(require_permission("REPORT_VIEW"))):
    payload.generated_by_id = current_user.get("user_id")
    return api_success(report_controller.generate(payload), "Report generated")


@router.get("/export/pdf")
def export_dataset_pdf_query(
    dataset_id: int = Query(...),
    include_full_modules: bool = Query(default=True),
    include_heatmap: bool = Query(default=True),
    include_charts: bool = Query(default=True),
    top_n: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(require_permission("REPORT_EXPORT")),
):
    payload = _query_export_payload(dataset_id, include_full_modules, include_heatmap, include_charts, top_n)
    options = report_controller.export_options(payload)
    filename = report_controller.export_dataset_filename(dataset_id, "pdf")
    return Response(report_controller.export_dataset_pdf(dataset_id, options), media_type="application/pdf", headers=_attachment(filename))


@router.post("/export/pdf")
def export_dataset_pdf_post(payload: ReportExportRequest, current_user: dict = Depends(require_permission("REPORT_EXPORT"))):
    options = report_controller.export_options(payload)
    filename = report_controller.export_dataset_filename(payload.dataset_id, "pdf")
    return Response(report_controller.export_dataset_pdf(payload.dataset_id, options), media_type="application/pdf", headers=_attachment(filename))


@router.get("/export/excel")
def export_dataset_excel_query(
    dataset_id: int = Query(...),
    include_full_modules: bool = Query(default=True),
    include_heatmap: bool = Query(default=True),
    include_charts: bool = Query(default=True),
    top_n: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(require_permission("REPORT_EXPORT")),
):
    payload = _query_export_payload(dataset_id, include_full_modules, include_heatmap, include_charts, top_n)
    options = report_controller.export_options(payload)
    filename = report_controller.export_dataset_filename(dataset_id, "xlsx")
    return Response(
        report_controller.export_dataset_xlsx(dataset_id, options),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=_attachment(filename),
    )


@router.post("/export/excel")
def export_dataset_excel_post(payload: ReportExportRequest, current_user: dict = Depends(require_permission("REPORT_EXPORT"))):
    options = report_controller.export_options(payload)
    filename = report_controller.export_dataset_filename(payload.dataset_id, "xlsx")
    return Response(
        report_controller.export_dataset_xlsx(payload.dataset_id, options),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=_attachment(filename),
    )


@router.get("/{report_id}")
def get_report(report_id: int, current_user: dict = Depends(require_permission("REPORT_VIEW"))):
    return api_success(report_controller.get_report(report_id))


@router.get("/{report_id}/export/pdf")
def export_pdf(report_id: int, current_user: dict = Depends(require_permission("REPORT_EXPORT"))):
    return Response(report_controller.export_pdf(report_id), media_type="application/pdf", headers=_attachment(f"DefectAI_Report_{report_id}.pdf"))


@router.get("/{report_id}/export/csv")
def export_csv(report_id: int, current_user: dict = Depends(require_permission("REPORT_EXPORT"))):
    return Response(report_controller.export_csv(report_id), media_type="text/csv", headers=_attachment(f"DefectAI_Report_{report_id}.csv"))


@router.get("/{report_id}/export/xlsx")
def export_xlsx(report_id: int, current_user: dict = Depends(require_permission("REPORT_EXPORT"))):
    return Response(report_controller.export_xlsx(report_id), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=_attachment(f"DefectAI_Report_{report_id}.xlsx"))


@router.get("/dataset/{dataset_id}/export/pdf")
def export_dataset_pdf(dataset_id: int, current_user: dict = Depends(require_permission("REPORT_EXPORT"))):
    filename = report_controller.export_dataset_filename(dataset_id, "pdf")
    return Response(report_controller.export_dataset_pdf(dataset_id), media_type="application/pdf", headers=_attachment(filename))


@router.get("/dataset/{dataset_id}/export/csv")
def export_dataset_csv(dataset_id: int, current_user: dict = Depends(require_permission("REPORT_EXPORT"))):
    filename = report_controller.export_dataset_filename(dataset_id, "csv")
    return Response(report_controller.export_dataset_csv(dataset_id), media_type="text/csv", headers=_attachment(filename))


@router.get("/dataset/{dataset_id}/export/xlsx")
def export_dataset_xlsx(dataset_id: int, current_user: dict = Depends(require_permission("REPORT_EXPORT"))):
    filename = report_controller.export_dataset_filename(dataset_id, "xlsx")
    return Response(report_controller.export_dataset_xlsx(dataset_id), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=_attachment(filename))


@router.delete("/{report_id}")
def delete_report(report_id: int, current_user: dict = Depends(RoleChecker(["Admin"]))):
    """
    Chỉ ADMIN mới được xóa report (Developer và Viewer không được phép)
    """
    return api_success(report_controller.delete(report_id, current_user.get("user_id")), "Report deleted")


@router.post("/export-multiple")
def export_multiple_reports(payload: ExportMultipleReportsRequest, current_user: dict = Depends(RoleChecker(["Admin", "Developer"]))):
    """
    Export nhiều reports cùng lúc (CSV format)
    Chỉ Admin và Developer được phép (Viewer không được)
    """
    return Response(
        report_controller.export_multiple(payload.report_ids, payload.format),
        media_type="application/zip" if len(payload.report_ids) > 1 else "text/csv",
        headers={"Content-Disposition": f"attachment; filename=reports_export.{'zip' if len(payload.report_ids) > 1 else 'csv'}"}
    )
