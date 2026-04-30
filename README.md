<<<<<<< HEAD
# ProjectMessurement
=======
# DefectAI P7 - AI Tool for Software Defect Prediction

DefectAI P7 is a Software Measurement & Analysis project for predicting defect-prone software modules from code metrics. It supports a practical QA workflow: upload metrics, validate measurement data, train a production ML model, predict defect probability, inspect dataset-scoped dashboards/heatmaps, and export reports.

## Problem Motivation

Large, complex, tightly coupled, frequently changed modules usually carry higher maintenance and defect risk. DefectAI helps QA teams prioritize code review, test coverage, refactoring, and inspection effort instead of treating every module equally.

## Measurement Model

Required input columns:

- `module_name` or `module_path`
- `loc`
- `complexity`
- `coupling`
- `code_churn`
- optional `defect_label` for training

Fixed P7 feature engineering is implemented in `backend/app/ml/feature_engineering.py`.

```text
risk_score =
  0.25 * size_score +
  0.30 * complexity_score +
  0.20 * coupling_score +
  0.20 * churn_score +
  0.05 * normalize(defect_density) -
  0.05 * cohesion_score -
  0.03 * reuse_score
```

Production prediction uses:

```text
final_probability = 0.75 * ML_probability + 0.25 * measurement_risk_score
```

If no active production model exists, DefectAI uses measurement fallback only and marks the response as fallback.

Risk levels:

- LOW: `< 0.30`
- MEDIUM: `0.30 - 0.60`
- HIGH: `0.60 - 0.80`
- CRITICAL: `>= 0.80`

Prediction labels:

- LOW: `No Defect`
- MEDIUM: `Possible Defect`
- HIGH/CRITICAL: `Defect`

## Architecture

```text
backend/   FastAPI + pyodbc + SQL Server + scikit-learn + openpyxl/reportlab
frontend/  React + Vite + Recharts + Axios
```

Dashboard, charts, reports, models, history, and predictions are loaded from Backend API only. The frontend does not use mock data.

## A. Setup

1. Start SQL Server.
2. Open SQL Server Management Studio.
3. Login:
   - Server: `localhost`
   - User: `sa`
   - Password: `123456`
4. Run `backend/sql/create_database.sql`.
5. Run `backend/sql/update_schema_p7.sql`.
6. Run `backend/sql/update_reports_security_schema.sql`.
7. Run `backend/sql/create_permission_db.sql`.
8. Run `backend/sql/seed_permission_data.sql`.
9. Seed bcrypt users:

```powershell
cd backend
python scripts\seed_permission_users.py
```

10. Optional: run `backend/sql/seed_data.sql`.

Backend:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check: `http://localhost:8000/api/health`

Do not run `uvicorn main:app` from the project root. If you are already inside `backend`, `main.py` exists only as a compatibility entrypoint; the canonical ASGI target remains `app.main:app`.

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open: `http://localhost:5173`

## Fix Frontend Cannot Reach Backend

Use this exact startup flow when the frontend shows `Cannot reach backend API at http://localhost:8000/api`.

Backend:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Check these URLs:

- `http://localhost:8000/api/health`
- `http://localhost:5173`

`frontend/.env` must contain:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

Do not use `/api/api/health`, `http://localhost:8000/health`, or a base URL with a trailing slash.

You can test SQL Server directly with:

```powershell
cd backend
python test_connection.py
```

Dataset-scoped API checks:

- `http://localhost:8000/api/datasets/history?project_id=1`
- `http://localhost:8000/api/datasets/7/preview`
- `http://localhost:8000/api/predictions/dataset/7`
- `http://localhost:8000/api/dashboard/summary?project_id=1&dataset_id=7`
- `http://localhost:8000/api/dashboard/charts?project_id=1&dataset_id=7`
- `http://localhost:8000/api/debug/database`
- `http://localhost:8000/api/debug/dataset/7`

If `debug/dataset/{id}` shows `metric_records_count = 0`, that dataset only has metadata in `MetricsDatasets`. Re-upload the CSV so SQL Server can rebuild `MetricRecords`, then run Analyze Dataset.

## Default Accounts

Admin:

- username: `admin`
- password: `Admin@123`

Developer:

- username: `dev01`
- password: `Dev@123`

Viewer:

- username: `viewer01`
- password: `Viewer@123`

## Permission Test Flow

1. Login as `admin`: Users menu is visible; upload, train, export, delete report are allowed.
2. Login as `dev01`: Users menu is hidden; upload, train, view/export reports are allowed.
3. Login as `viewer01`: dashboard, history and reports are read-only; train/upload/delete actions are hidden and protected by 403 API responses.

## Report Export

Dataset-scoped exports:

- `GET /api/reports/dataset/{dataset_id}/export/xlsx`
- `GET /api/reports/dataset/{dataset_id}/export/pdf`
- `GET /api/reports/dataset/{dataset_id}/export/csv`

Legacy report URLs also work when the id maps to a generated report:

- `GET /api/reports/{report_id}/export/xlsx`
- `GET /api/reports/{report_id}/export/pdf`
- `GET /api/reports/{report_id}/export/csv`

## B. Train Production Model

1. Prepare a CSV with:
   `module_name, loc, complexity, coupling, code_churn, defect_label`
2. Upload it in Metrics Explorer.
3. Metrics Explorer will show validation and measurement metrics preview.
4. Click **Train Production Model**, or go to AI Models and select the dataset.
5. Backend calls `POST /api/ml/train-production`.
6. It trains Logistic Regression, Random Forest, and Neural Network with the same P7 feature list.
7. The best model is selected by F1-score, then ROC-AUC.
8. The active artifact is saved to `backend/app/ml/artifacts/defectai_p7_production.joblib`.

If a perfect score is detected, the backend returns a warning that the dataset may be too small, duplicated, or too easy.

## C. Analyze A New File

1. Upload a CSV in Metrics Explorer.
2. If it has no `defect_label`, it can still be analyzed with the active production model.
3. Click **Analyze Dataset**.
4. Frontend sends:

```json
{
  "project_id": 1,
  "dataset_id": 123,
  "model_id": null
}
```

5. Backend calls `POST /api/predictions/run`.
6. Predictions are written to SQL Server for that dataset only.
7. Dashboard opens with `/dashboard?datasetId=123`.

## D. View Old Analyses

1. Open History.
2. Select a previous dataset.
3. Click **View Dashboard** or **View Metrics**.
4. Dashboard and charts load only that `dataset_id`.

Old files are archived in history; they are not mixed into the current dashboard.

## E. Export

Use Metrics Explorer, History, or Reports to export the selected dataset.

XLSX export contains:

- Summary
- Measurement Metrics
- AI Predictions
- Model Performance
- Risk Distribution

Excel colors:

- LOW: green
- MEDIUM: yellow
- HIGH: orange
- CRITICAL: red
- No Defect: teal
- Possible Defect: yellow
- Defect: red

## Key APIs

- `POST /api/datasets/upload`
- `GET /api/datasets/{dataset_id}/preview`
- `POST /api/ml/train-production`
- `GET /api/ml/trainable-datasets?project_id=1`
- `POST /api/predictions/run`
- `GET /api/predictions/dataset/{dataset_id}`
- `GET /api/dashboard/summary?project_id=1&dataset_id={dataset_id}`
- `GET /api/dashboard/charts?project_id=1&dataset_id={dataset_id}`
- `GET /api/datasets/{dataset_id}/export/xlsx`

## Demo Data

- `backend/sample_data/train_defect_dataset.csv`
- `backend/sample_data/defect_metrics_dataset.csv`
- `backend/sample_data/prediction_only_dataset.csv`
- `backend/sample_data/predict_only_dataset.csv`

## Final Report Suggested Structure

1. Introduction
2. Related Work
3. System Architecture
4. Measurement Model
5. AI Methods
6. Implementation
7. Experiments
8. Results
9. Conclusion
>>>>>>> 1cb6359 (Dự án messurement traning AI Model)
