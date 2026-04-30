# DefectAI P7 Backend

FastAPI backend for P7 defect prediction using SQL Server through `pyodbc`.

## Run

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health: `http://localhost:8000/api/health`

The canonical ASGI import path is `app.main:app`. `backend/main.py` only exists to prevent old `uvicorn main:app` commands from failing when run inside the `backend` directory.

SQL Server connection test:

```powershell
python test_connection.py
```

Integration diagnostics:

- `GET /api/debug/routes`
- `GET /api/debug/database`
- `GET /api/debug/dataset/{dataset_id}`

Dataset preview and prediction APIs return JSON even when a dataset has no rows or has not been analyzed yet. If `debug/dataset/{dataset_id}` returns `metric_records_count = 0`, re-upload the source CSV before running prediction for that dataset.

## SQL Server

Run in SSMS:

1. `sql/create_database.sql`
2. `sql/update_schema_p7.sql`
3. `sql/update_reports_security_schema.sql`
4. `sql/create_permission_db.sql`
5. `sql/seed_permission_data.sql`
6. `python scripts\seed_permission_users.py`
7. Optional: `sql/seed_data.sql`

## Authentication

Default accounts after seeding:

- Admin: `admin` / `Admin@123`
- Developer: `dev01` / `Dev@123`
- Viewer: `viewer01` / `Viewer@123`

Auth APIs:

- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/register`
- `GET /api/auth/users`
- `GET /api/auth/roles`

Protected APIs return JSON `401` when no token is supplied and JSON `403` when the token lacks the required permission.

## Production ML Pipeline

`POST /api/ml/train-production`

Body:

```json
{
  "project_id": 1,
  "dataset_id": 123,
  "test_size": 0.2,
  "random_state": 42
}
```

The backend builds fixed P7 features from `MetricRecords`, trains Logistic Regression, Random Forest, and MLPClassifier, selects the best model by F1-score then ROC-AUC, saves:

- `app/ml/artifacts/defectai_p7_production.joblib`
- `app/ml/artifacts/defectai_p7_production_metadata.json`

Prediction uses the production model when available, otherwise measurement fallback.
