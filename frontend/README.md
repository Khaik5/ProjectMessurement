# DefectAI P7 Frontend

React + Vite UI for DefectAI. All operational data is loaded from FastAPI services in `src/services`; there is no mock data fallback.

## Run

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Environment

```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_NAME=DefectAI
VITE_DEFAULT_PROJECT_ID=1
```

## Main Workflow

1. Metrics Explorer: upload CSV/JSON.
2. Validate required columns and inspect measurement metrics.
3. Train Production Model if `defect_label` exists.
4. Analyze Dataset.
5. Dashboard opens with the selected `datasetId`.
6. History lets users reopen old analyses without mixing datasets.
