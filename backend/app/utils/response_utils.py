from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi.responses import JSONResponse


def json_safe(value: Any) -> Any:
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def api_success(data: Any = None, message: str = "OK") -> dict[str, Any]:
    return {"success": True, "message": message, "data": json_safe(data)}


def api_error(message: str, errors: list[Any] | None = None) -> dict[str, Any]:
    return {"success": False, "message": message, "data": None, "errors": errors or []}


def success_response(data: Any = None, message: str = "OK") -> dict[str, Any]:
    return api_success(data, message)


def error_response(message: str = "Error", errors: list[Any] | None = None, status_code: int = 500) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=api_error(message, errors))
