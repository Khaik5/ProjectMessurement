from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response

from app.auth.auth_dependencies import require_permission
from app.controllers import dataset_controller
from app.utils.response_utils import api_success

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("/upload")
async def upload_dataset(project_id: int = Form(default=1), file: UploadFile = File(...), current_user: dict = Depends(require_permission("DATASET_UPLOAD"))):
    return api_success(await dataset_controller.upload_dataset(file, project_id), "Dataset uploaded")


@router.get("")
def list_datasets():
    return api_success(dataset_controller.list_datasets())


@router.get("/history")
def history(project_id: int = 1):
    return api_success(dataset_controller.history(project_id))


@router.get("/{dataset_id}")
def get_dataset(dataset_id: int):
    return api_success(dataset_controller.get_dataset(dataset_id))


@router.get("/{dataset_id}/preview")
def preview(dataset_id: int):
    data = dataset_controller.preview(dataset_id)
    return api_success(data, data.get("message", "OK"))


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: int, current_user: dict = Depends(require_permission("DATASET_DELETE"))):
    return api_success(dataset_controller.delete_dataset(dataset_id), "Dataset deleted")


@router.post("/{dataset_id}/set-current")
def set_current(dataset_id: int):
    return api_success(dataset_controller.set_current(dataset_id), "Current analysis dataset updated")


@router.get("/{dataset_id}/analysis-summary")
def analysis_summary(dataset_id: int):
    return api_success(dataset_controller.analysis_summary(dataset_id))


@router.get("/{dataset_id}/export/csv")
def export_csv(dataset_id: int, current_user: dict = Depends(require_permission("REPORT_EXPORT"))):
    return Response(dataset_controller.export_csv(dataset_id), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=dataset_{dataset_id}.csv"})


@router.get("/{dataset_id}/export/xlsx")
def export_xlsx(dataset_id: int, current_user: dict = Depends(require_permission("REPORT_EXPORT"))):
    return Response(dataset_controller.export_xlsx(dataset_id), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename=dataset_{dataset_id}.xlsx"})
