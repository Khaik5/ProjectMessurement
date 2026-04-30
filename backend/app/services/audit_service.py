import json

from app.repositories import audit_repository


def log_action(action: str, entity_type: str | None = None, entity_id: int | None = None, project_id: int | None = None, user_id: int | None = 1, details: dict | None = None, ip_address: str | None = None):
    return audit_repository.create_audit_log(
        user_id=user_id,
        project_id=project_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details_json=json.dumps(details or {}, ensure_ascii=False),
        ip_address=ip_address,
    )


def list_logs(limit: int = 100):
    return audit_repository.list_audit_logs(limit)


def project_logs(project_id: int, limit: int = 100):
    return audit_repository.by_project(project_id, limit)
