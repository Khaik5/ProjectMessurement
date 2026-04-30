import { CheckCircle2, Download, Eye, PlayCircle, RefreshCw, Rocket, ShieldAlert } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import Button from '../components/common/Button.jsx';
import Card from '../components/common/Card.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import Loading from '../components/common/Loading.jsx';
import SearchBox from '../components/common/SearchBox.jsx';
import MetricsTable from '../components/tables/MetricsTable.jsx';
import DatasetUploader from '../components/upload/DatasetUploader.jsx';
import { datasetService } from '../services/datasetService.js';
import { mlService } from '../services/mlService.js';
import { predictionService } from '../services/predictionService.js';
import { fmtNumber } from '../utils/formatters.js';
import { useAuth } from '../auth/AuthContext.jsx';

const projectId = Number(import.meta.env.VITE_DEFAULT_PROJECT_ID || 1);

function parseMetadata(dataset) {
  try {
    return dataset?.metadata_json ? JSON.parse(dataset.metadata_json) : {};
  } catch {
    return {};
  }
}

function ValidationPanel({ dataset, validation }) {
  if (!dataset) return <EmptyState title="No dataset selected" description="Upload or choose a dataset from history." />;
  const metadata = validation || parseMetadata(dataset);
  const dataQuality = metadata.data_quality || {};
  const missingValues = dataQuality.missing_values || {};
  return (
    <div className="page-stack" style={{ gap: 12 }}>
      <div className="dataset-card">
        <strong>{dataset.file_name || dataset.name}</strong>
        <span>{fmtNumber(dataset.row_count)} rows - {dataset.status}</span>
      </div>
      <div className={dataset.has_label ? 'success-panel' : 'warning-panel'}>
        {dataset.has_label ? 'Has defect_label: can train production model and analyze.' : 'No defect_label: prediction will use the active production model or measurement fallback.'}
      </div>
      <div className="step-grid">
        <div className="step-card"><strong>Required columns</strong><span>{(metadata.required_columns || []).join(', ') || 'module_name, loc, complexity, coupling, code_churn'}</span></div>
        <div className="step-card"><strong>Optional detected</strong><span>{(metadata.optional_columns_detected || []).join(', ') || 'None'}</span></div>
        <div className="step-card"><strong>Missing columns</strong><span>{(metadata.missing_columns || []).join(', ') || 'None'}</span></div>
        <div className="step-card"><strong>Duplicated modules</strong><span>{fmtNumber(dataQuality.duplicated_modules || 0)}</span></div>
      </div>
      <div className="step-card">
        <strong>Data quality</strong>
        <span>Missing values: {Object.entries(missingValues).map(([key, value]) => `${key}=${value}`).join(', ') || '0'}</span>
        <span style={{ display: 'block', marginTop: 4 }}>Label distribution: {JSON.stringify(dataQuality.label_distribution || {})}</span>
      </div>
    </div>
  );
}

function rowsFromApi(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.rows)) return payload.rows;
  if (Array.isArray(payload?.data?.rows)) return payload.data.rows;
  return [];
}

function mergeMetricPredictionRows(previewRows, predictionRows) {
  const predictionByModule = new Map(
    predictionRows.map((row) => [String(row.module_name || '').toLowerCase(), row])
  );

  const merged = previewRows.map((row) => {
    const prediction = predictionByModule.get(String(row.module_name || '').toLowerCase());
    return prediction ? { ...row, ...prediction } : row;
  });

  const previewKeys = new Set(previewRows.map((row) => String(row.module_name || '').toLowerCase()));
  predictionRows.forEach((row) => {
    const key = String(row.module_name || '').toLowerCase();
    if (!previewKeys.has(key)) merged.push(row);
  });

  return merged;
}

export default function MetricsExplorer() {
  const { hasPermission } = useAuth();
  const [datasets, setDatasets] = useState([]);
  const [activeDataset, setActiveDataset] = useState(null);
  const [validation, setValidation] = useState(null);
  const [previewRows, setPreviewRows] = useState([]);
  const [predictionRows, setPredictionRows] = useState([]);
  const [activeModel, setActiveModel] = useState(null);
  const [query, setQuery] = useState('');
  const [risk, setRisk] = useState('ALL');
  const [status, setStatus] = useState('ALL');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  async function loadDataset(datasetId) {
    if (!datasetId) return;
    const [preview, predictions] = await Promise.all([
      datasetService.preview(datasetId),
      predictionService.byDataset(datasetId)
    ]);
    const previewData = rowsFromApi(preview);
    const predictionData = rowsFromApi(predictions);
    setPreviewRows(previewData);
    setPredictionRows(mergeMetricPredictionRows(previewData, predictionData));
  }

  async function load() {
    setLoading(true);
    setError('');
    try {
      const [history, models] = await Promise.all([
        datasetService.history(projectId),
        mlService.models(projectId)
      ]);
      setDatasets(history || []);
      const active = (models || []).find((model) => model.is_active && model.name === 'DefectAI P7 Production Model') || null;
      setActiveModel(active);

      const datasetIdParam = searchParams.get('datasetId');
      const selected = datasetIdParam ? history.find((d) => String(d.id) === String(datasetIdParam)) : history[0];
      if (selected) {
        setActiveDataset(selected);
        setValidation(parseMetadata(selected));
        await loadDataset(selected.id);
        if (!datasetIdParam) setSearchParams({ datasetId: String(selected.id) });
      } else {
        setActiveDataset(null);
        setPreviewRows([]);
        setPredictionRows([]);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);
  useEffect(() => { setPage(1); }, [query, risk, status, predictionRows.length, previewRows.length]);

  async function selectDataset(id) {
    const selected = datasets.find((item) => String(item.id) === String(id));
    setActiveDataset(selected || null);
    setValidation(parseMetadata(selected));
    setSearchParams({ datasetId: String(id) });
    setLoading(true);
    setError('');
    try {
      await datasetService.setCurrent(id);
      await loadDataset(id);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function upload(file) {
    if (!hasPermission('DATASET_UPLOAD')) return setError('Permission denied: DATASET_UPLOAD is required');
    setLoading(true);
    setMessage('');
    setError('');
    try {
      const result = await datasetService.upload(file, projectId);
      const dataset = result.dataset;
      setActiveDataset(dataset);
      setValidation(result.validation || parseMetadata(dataset));
      setPreviewRows(result.preview || []);
      setPredictionRows([]);
      setSearchParams({ datasetId: String(dataset?.id) });
      const history = await datasetService.history(projectId);
      setDatasets(history || []);
      setMessage(`Uploaded ${dataset.file_name}. Validate the measurement metrics, then train or analyze.`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function trainProduction() {
    if (!hasPermission('MODEL_TRAIN')) return setError('Permission denied: MODEL_TRAIN is required');
    if (!activeDataset) return setError('Select a dataset before training.');
    if (!activeDataset.has_label) return setError('Training requires defect_label: 0 = No Defect, 1 = Defect.');
    setProcessing('Training production model...');
    setMessage('');
    setError('');
    try {
      const result = await mlService.trainProduction({
        project_id: projectId,
        dataset_id: activeDataset.id,
        test_size: 0.2,
        random_state: 42,
        auto_activate_best: true
      });
      setActiveModel(result.production_model);
      setMessage(`Production model trained. Best model: ${result.best_model_type}. ${(result.warnings || []).join(' ')}`);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setProcessing('');
    }
  }

  async function analyze() {
    if (!hasPermission('MODEL_TEST')) return setError('Permission denied: MODEL_TEST is required');
    if (!activeDataset) return setError('No dataset selected.');
    setProcessing('Analyzing dataset...');
    setMessage('');
    setError('');
    try {
      const result = await predictionService.run({
        project_id: projectId,
        dataset_id: activeDataset.id,
        model_id: activeModel?.id || null
      });
      await datasetService.setCurrent(activeDataset.id);
      await loadDataset(activeDataset.id);
      setMessage(`Analyzed ${result.predictions_created || result.total_modules} modules using ${result.used_model}.`);
      navigate(`/dashboard?datasetId=${activeDataset.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setProcessing('');
    }
  }

  const filteredPredictions = useMemo(() => (Array.isArray(predictionRows) ? predictionRows : []).filter((row) => {
    const matchesQuery = (row.module_name || '').toLowerCase().includes(query.toLowerCase());
    const matchesRisk = risk === 'ALL' || row.risk_level === risk;
    const matchesStatus = status === 'ALL' || row.prediction_label === status;
    return matchesQuery && matchesRisk && matchesStatus;
  }), [predictionRows, query, risk, status]);
  const hasPredictionData = predictionRows.some((row) => row.defect_probability !== undefined && row.defect_probability !== null);

  const pageSize = 20;
  const totalPages = Math.max(1, Math.ceil(filteredPredictions.length / pageSize));
  const visiblePredictions = filteredPredictions.slice((page - 1) * pageSize, page * pageSize);
  const preview = previewRows.slice(0, 20);
  const canUpload = hasPermission('DATASET_UPLOAD');
  const canTrain = hasPermission('MODEL_TRAIN');
  const canAnalyze = hasPermission('MODEL_TEST');
  const canExport = hasPermission('REPORT_EXPORT');

  async function download(type) {
    if (!activeDataset) return;
    try {
      const blob = await datasetService.export(activeDataset.id, type);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `dataset_${activeDataset.id}.${type}`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page-stack">
      <div className="step-grid">
        <div className="step-card"><strong>1. Upload Dataset</strong><span>CSV/JSON metrics from SQL Server upload API.</span></div>
        <div className="step-card"><strong>2. Validate</strong><span>Required columns, optional metrics, quality checks.</span></div>
        <div className="step-card"><strong>3. Measurement</strong><span>Fixed P7 risk score from LOC, complexity, coupling, churn.</span></div>
        <div className="step-card"><strong>4. AI Prediction</strong><span>Production model or measurement fallback.</span></div>
      </div>

      <div className="grid-2">
        <Card>
          <h3>Step 1: Upload Dataset</h3>
          <p className="muted">Required: module_name, loc, complexity, coupling, code_churn. Optional: defect_label for training.</p>
          {canUpload ? <DatasetUploader onUpload={upload} disabled={loading || Boolean(processing)} /> : <EmptyState title="Read-only access" description="You can view metrics and predictions for existing analyses." />}
        </Card>
        <Card>
          <div className="section-header">
            <div>
              <h3>Step 2: Dataset Validation</h3>
              <p className="muted">Selected analysis is scoped to one dataset only.</p>
            </div>
            <Button variant="secondary" onClick={load} disabled={loading || Boolean(processing)}><RefreshCw size={18} />Refresh</Button>
          </div>
          <select value={activeDataset?.id || ''} onChange={(event) => selectDataset(event.target.value)}>
            <option value="">Select dataset...</option>
            {datasets.map((dataset) => <option key={dataset.id} value={dataset.id}>#{dataset.id} - {dataset.file_name || dataset.name}</option>)}
          </select>
          <ValidationPanel dataset={activeDataset} validation={validation} />
        </Card>
      </div>

      {processing ? (
        <Card>
          <strong>{processing}</strong>
          <div className="progress-bar" style={{ marginTop: 12 }}><div /></div>
        </Card>
      ) : null}
      {message ? <div className="success-panel">{message}</div> : null}
      {error ? <div className="warning-panel">{error}</div> : null}
      {loading ? <Loading /> : null}

      <Card>
        <div className="section-header">
          <div>
            <h3>Step 3: Measurement Metrics Preview</h3>
            <p className="muted">Preview rows are loaded from /api/datasets/{activeDataset?.id || '{dataset_id}'}/preview.</p>
          </div>
          <div className="button-row">
            {activeDataset?.has_label && canTrain ? <Button variant="secondary" onClick={trainProduction} disabled={Boolean(processing)}><Rocket size={18} />Train Production Model</Button> : null}
            {canAnalyze ? <Button onClick={analyze} disabled={!activeDataset || Boolean(processing)}><PlayCircle size={18} />Analyze Dataset</Button> : null}
          </div>
        </div>
        {!activeDataset ? <EmptyState title="No dataset selected" /> : <MetricsTable rows={preview} />}
      </Card>

      <Card>
        <div className="section-header">
          <div>
            <h3>Step 4: AI Prediction Output</h3>
            <p className="muted">
              Active model: {activeModel?.name || 'No active production model. Analyze will use measurement fallback.'}
            </p>
          </div>
          <div className="button-row">
            {canExport ? <Button variant="secondary" onClick={() => download('csv')}><Download size={16} />CSV</Button> : null}
            {canExport ? <Button variant="secondary" onClick={() => download('xlsx')}><Download size={16} />XLSX</Button> : null}
            <Button variant="secondary" onClick={() => activeDataset && navigate(`/dashboard?datasetId=${activeDataset.id}`)}><Eye size={18} />View Dashboard</Button>
          </div>
        </div>
        <div className="filters">
          <SearchBox value={query} onChange={setQuery} />
          <select value={risk} onChange={(e) => setRisk(e.target.value)}><option value="ALL">All Risk</option><option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>CRITICAL</option></select>
          <select value={status} onChange={(e) => setStatus(e.target.value)}><option value="ALL">All Prediction</option><option>No Defect</option><option>Possible Defect</option><option>Defect</option></select>
        </div>
        {predictionRows.length ? (
          <>
            {hasPredictionData ? (
              <div className="success-panel" style={{ marginBottom: 12 }}>
                <CheckCircle2 size={16} /> {predictionRows.some((row) => row.model_id) ? 'AI production model' : 'Measurement fallback'} - {fmtNumber(predictionRows.length)} predictions loaded from SQL Server.
              </div>
            ) : (
              <div className="warning-panel" style={{ marginBottom: 12 }}>
                Dataset has not been analyzed yet. Click Analyze Dataset to create prediction labels and risk levels.
              </div>
            )}
            <MetricsTable rows={visiblePredictions} />
            <div className="pagination">
              <span>Page {page} / {totalPages}</span>
              <Button variant="secondary" onClick={() => setPage(Math.max(1, page - 1))}>Previous</Button>
              <Button variant="secondary" onClick={() => setPage(Math.min(totalPages, page + 1))}>Next</Button>
            </div>
          </>
        ) : (
          <EmptyState title="No predictions yet" description="Click Analyze Dataset to create defect probability, prediction label, and risk level." />
        )}
      </Card>

      {predictionRows.some((row) => Number(row.defect_probability) >= 0.8) ? (
        <div className="alert-panel">
          <ShieldAlert />
          <div>
            <strong>Critical risk detected</strong>
            <p>At least one module has defect probability &gt;= 80%. Review the prediction table and dashboard heatmap.</p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
