from pathlib import Path

import pyodbc
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import API_PREFIX, APP_NAME, FRONTEND_URL, get_sqlserver_connection
from app.database import fetch_all, fetch_one, get_connection
from app.auth import auth_routes
from app.routes import audit_routes, dashboard_routes, dataset_routes, history_routes, metric_routes, ml_routes, prediction_routes, project_routes, report_routes
from app.utils.response_utils import api_error, api_success

app = FastAPI(
    title=APP_NAME,
    version="1.0.0",
    description="P7 AI Tool for Software Defect Prediction using FastAPI, SQL Server, pyodbc and scikit-learn.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _database_error(exc: pyodbc.Error) -> tuple[int, str]:
    if isinstance(exc, (pyodbc.InterfaceError, pyodbc.OperationalError)):
        return 503, "SQL Server unavailable"
    return 500, f"Database query failed: {str(exc)}"


@app.middleware("http")
async def json_safe_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content=api_error(str(exc.detail)))
    except pyodbc.Error as exc:
        status_code, message = _database_error(exc)
        return JSONResponse(status_code=status_code, content=api_error(message))
    except ValueError as exc:
        return JSONResponse(status_code=400, content=api_error(str(exc)))
    except Exception as exc:
        return JSONResponse(status_code=503, content=api_error(str(exc)))


@app.exception_handler(Exception)
async def global_exception_handler(_: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content=api_error(str(exc.detail)))
    if isinstance(exc, pyodbc.Error):
        status_code, message = _database_error(exc)
        return JSONResponse(status_code=status_code, content=api_error(message))
    if isinstance(exc, ValueError):
        return JSONResponse(status_code=400, content=api_error(str(exc)))
    return JSONResponse(status_code=503, content=api_error(str(exc)))


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content=api_error(str(exc.detail)))


@app.get("/api/health")
def health_check():
    try:
        conn = get_sqlserver_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        return {
            "success": True,
            "message": "Backend and SQL Server connected",
            "data": {"backend": "ok", "database": "ok"},
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"SQL Server connection failed: {str(e)}",
            "data": {"backend": "ok", "database": "failed"},
        }


@app.post(f"{API_PREFIX}/seed")
def seed_database():
    sql_path = Path(__file__).resolve().parents[1] / "sql" / "seed_data.sql"
    if not sql_path.exists():
        raise HTTPException(status_code=404, detail="seed_data.sql not found")
    script = sql_path.read_text(encoding="utf-8")
    batches = [batch.strip() for batch in script.replace("\r\n", "\n").split("\nGO") if batch.strip()]
    with get_connection() as conn:
        cursor = conn.cursor()
        for batch in batches:
            cursor.execute(batch)
        conn.commit()
    return api_success({"seeded": True}, "Seed data executed")


@app.get("/api/debug/routes")
def debug_routes():
    routes = []
    for route in app.routes:
        routes.append(
            {
                "path": getattr(route, "path", None),
                "name": getattr(route, "name", None),
                "methods": sorted(list(getattr(route, "methods", []) or [])),
            }
        )
    return api_success(routes)


@app.get("/api/debug/database")
def debug_database():
    tables = ["MetricsDatasets", "MetricRecords", "Predictions", "MLModels", "TrainingRuns"]
    counts = {}
    for table in tables:
        row = fetch_one(f"SELECT COUNT(*) AS count FROM {table}") or {}
        counts[table] = int(row.get("count") or 0)
    return api_success({"connection": health_check()["data"], "counts": counts})


@app.get("/api/debug/dataset/{dataset_id}")
def debug_dataset(dataset_id: int):
    dataset = fetch_one("SELECT * FROM MetricsDatasets WHERE id = ?", [dataset_id])
    metric_count = fetch_one("SELECT COUNT(*) AS count FROM MetricRecords WHERE dataset_id = ?", [dataset_id]) or {}
    prediction_count = fetch_one("SELECT COUNT(*) AS count FROM Predictions WHERE dataset_id = ?", [dataset_id]) or {}
    sample_metric = fetch_one("SELECT TOP 1 * FROM MetricRecords WHERE dataset_id = ? ORDER BY id", [dataset_id])
    sample_prediction = fetch_one("SELECT TOP 1 * FROM Predictions WHERE dataset_id = ? ORDER BY defect_probability DESC", [dataset_id])
    return api_success(
        {
            "dataset_exists": bool(dataset),
            "dataset": dataset,
            "metric_records_count": int(metric_count.get("count") or 0),
            "predictions_count": int(prediction_count.get("count") or 0),
            "sample_metric_record": sample_metric,
            "sample_prediction": sample_prediction,
        }
    )


app.include_router(project_routes.router, prefix=API_PREFIX)
app.include_router(auth_routes.router, prefix=API_PREFIX)
app.include_router(dataset_routes.router, prefix=API_PREFIX)
app.include_router(metric_routes.router, prefix=API_PREFIX)
app.include_router(ml_routes.router, prefix=API_PREFIX)
app.include_router(prediction_routes.router, prefix=API_PREFIX)
app.include_router(dashboard_routes.router, prefix=API_PREFIX)
app.include_router(report_routes.router, prefix=API_PREFIX)
app.include_router(audit_routes.router, prefix=API_PREFIX)
app.include_router(history_routes.router, prefix=API_PREFIX)
