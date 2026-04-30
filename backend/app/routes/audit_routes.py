from fastapi import APIRouter

from app.database import test_connection
from app.services import audit_service
from app.utils.response_utils import api_success

router = APIRouter(prefix="/audit-logs", tags=["Audit"])


@router.get("")
def list_audit_logs():
    return api_success(audit_service.list_logs())


@router.get("/project/{project_id}")
def project_audit_logs(project_id: int):
    return api_success(audit_service.project_logs(project_id))


@router.get("/database-status")
def database_status():
    return api_success(test_connection())
