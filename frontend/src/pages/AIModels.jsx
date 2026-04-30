import { BrainCircuit, Database, RefreshCw, Rocket, ShieldCheck, Trash2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import Button from '../components/common/Button.jsx';
import Card from '../components/common/Card.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import Loading from '../components/common/Loading.jsx';
import ConfusionMatrixChart from '../components/charts/ConfusionMatrixChart.jsx';
import ModelComparisonChart from '../components/charts/ModelComparisonChart.jsx';
import TrainingGuide from '../components/dashboard/TrainingGuide.jsx';
import KpiCard from '../components/dashboard/KpiCard.jsx';
import { mlService } from '../services/mlService.js';
import { fmtPercent } from '../utils/formatters.js';
import { useAuth } from '../auth/AuthContext.jsx';

const projectId = Number(import.meta.env.VITE_DEFAULT_PROJECT_ID || 1);

function parseJson(value, fallback = null) {
  try {
    return value ? JSON.parse(value) : fallback;
  } catch {
    return fallback;
  }
}

export default function AIModels() {
  const { hasPermission } = useAuth();
  const [models, setModels] = useState([]);
  const [runs, setRuns] = useState([]);
  const [comparison, setComparison] = useState([]);
  const [datasets, setDatasets] = useState([]);
  const [guide, setGuide] = useState(null);
  const [form, setForm] = useState({ dataset_id: '', test_size: 0.2, random_state: 42 });
  const [loading, setLoading] = useState(false);
  const [training, setTraining] = useState(false);
  const [message, setMessage] = useState('');
  const [warnings, setWarnings] = useState([]);
  const [error, setError] = useState('');

  async function load() {
    setLoading(true);
    setError('');
    try {
      const [trainable, modelData, runData, cmp, guideData] = await Promise.all([
        mlService.trainableDatasets(projectId),
        mlService.models(projectId),
        mlService.trainingRuns(projectId),
        mlService.comparison(projectId),
        mlService.trainingGuide()
      ]);
      setDatasets(trainable || []);
      setModels(modelData || []);
      setRuns(runData || []);
      setComparison(cmp || []);
      setGuide(guideData);
      if (!form.dataset_id && trainable?.length) {
        setForm((current) => ({ ...current, dataset_id: String(trainable[0].id) }));
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function trainProduction() {
    if (!hasPermission('MODEL_TRAIN')) {
      setError('Permission denied: MODEL_TRAIN is required');
      return;
    }
    if (!form.dataset_id) {
      setError('Select a trainable dataset first. Training requires defect_label: 0 = No Defect, 1 = Defect.');
      return;
    }
    setTraining(true);
    setError('');
    setMessage('');
    setWarnings([]);
    try {
      const result = await mlService.trainProduction({
        project_id: projectId,
        dataset_id: Number(form.dataset_id),
        test_size: Number(form.test_size),
        random_state: Number(form.random_state),
        auto_activate_best: true
      });
      setWarnings(result.warnings || []);
      setMessage(`Production model updated. Best algorithm: ${result.best_model_type}.`);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setTraining(false);
    }
  }

  async function activate(id) {
    if (!hasPermission('MODEL_DEPLOY')) {
      setError('Permission denied: MODEL_DEPLOY is required');
      return;
    }
    await mlService.activate(id);
    await load();
  }

  async function deleteModel(id) {
    if (!hasPermission('MODEL_DELETE')) {
      setError('Permission denied: MODEL_DELETE is required');
      return;
    }
    if (!window.confirm(`Delete model #${id}? (soft delete)`)) return;
    await mlService.deleteModel(id);
    await load();
  }

  async function deleteRun(id) {
    if (!hasPermission('MODEL_DELETE')) {
      setError('Permission denied: MODEL_DELETE is required');
      return;
    }
    if (!window.confirm(`Delete training run #${id}? (soft delete)`)) return;
    await mlService.deleteTrainingRun(id);
    await load();
  }

  const productionModel = models.find((item) => item.name === 'DefectAI P7 Production Model');
  const latestRun = runs[0];
  const latestMatrix = useMemo(() => parseJson(latestRun?.confusion_matrix_json), [latestRun]);
  const featureList = parseJson(productionModel?.feature_list_json, []);
  const canTrain = hasPermission('MODEL_TRAIN');
  const canDeploy = hasPermission('MODEL_DEPLOY');
  const canDelete = hasPermission('MODEL_DELETE');

  return (
    <div className="page-stack">
      <div className="section-header">
        <div>
          <h2>AI Model Management</h2>
          <p className="muted">Production training uses the fixed P7 feature engineering pipeline for all algorithms.</p>
        </div>
        <div className="button-row">
          <Button variant="secondary" onClick={load} disabled={loading || training}><RefreshCw size={20} />Refresh</Button>
          {canTrain ? <Button onClick={trainProduction} disabled={loading || training}><Rocket size={20} />Train Production Model</Button> : null}
        </div>
      </div>

      {loading ? <Loading label="Loading models from SQL Server..." /> : null}
      {training ? <Card><strong>Training production model...</strong><div className="progress-bar" style={{ marginTop: 12 }}><div /></div></Card> : null}
      {message ? <div className="success-panel">{message}</div> : null}
      {warnings.map((warning) => <div className="warning-panel" key={warning}>{warning}</div>)}
      {error ? <div className="warning-panel">{error}</div> : null}

      <Card>
        <div className="section-header">
          <div>
            <h3>Active Production Model</h3>
            <p className="muted">Only one production artifact is active: backend/app/ml/artifacts/defectai_p7_production.joblib.</p>
          </div>
          {productionModel?.is_active ? <span className="active-pill">Active</span> : null}
        </div>
        {!productionModel ? (
          <EmptyState title="No production model" description="Choose a labeled dataset and train the production model." />
        ) : (
          <div className="grid-3">
            <div className="step-card"><ShieldCheck size={22} /><strong>{productionModel.name}</strong><span>{productionModel.model_type} - {productionModel.version}</span></div>
            <div className="step-card"><Database size={22} /><strong>Feature Count</strong><span>{featureList?.length || 23} fixed P7 features</span></div>
            <div className="step-card"><BrainCircuit size={22} /><strong>Artifact</strong><span>{productionModel.artifact_path}</span></div>
          </div>
        )}
      </Card>

      <div className="kpi-grid">
        <KpiCard label="Accuracy" value={fmtPercent(productionModel?.accuracy)} />
        <KpiCard label="Precision" value={fmtPercent(productionModel?.precision)} />
        <KpiCard label="Recall" value={fmtPercent(productionModel?.recall)} />
        <KpiCard label="F1-score" value={fmtPercent(productionModel?.f1_score)} />
      </div>

      <div className="grid-2">
        <Card>
          <h3>Training Panel</h3>
          <p className="muted">Select a dataset with defect_label. The backend will train Logistic Regression, Random Forest, and Neural Network, then activate the best model by F1-score and ROC-AUC.</p>
          <div className="form-grid" style={{ marginTop: 14 }}>
            <label>Trainable Dataset
              <select value={form.dataset_id} onChange={(e) => setForm({ ...form, dataset_id: e.target.value })}>
                <option value="">Select dataset...</option>
                {datasets.map((d) => (
                  <option key={d.id} value={d.id}>#{d.id} - {d.file_name || d.name} ({d.row_count} rows)</option>
                ))}
              </select>
            </label>
            <label>Test Size<input value={form.test_size} onChange={(e) => setForm({ ...form, test_size: e.target.value })} /></label>
            <label>Random State<input value={form.random_state} onChange={(e) => setForm({ ...form, random_state: e.target.value })} /></label>
            <label>Status<input value="auto_activate_best = true" readOnly /></label>
          </div>
          <div className="button-row" style={{ marginTop: 14 }}>
            {canTrain ? <Button onClick={trainProduction} disabled={training}><Rocket size={18} />Train Production Model</Button> : null}
          </div>
        </Card>
        <Card>
          <h3>How Training Works</h3>
          <TrainingGuide guide={guide} />
        </Card>
      </div>

      <div className="grid-2">
        <Card>
          <h3>Model Comparison</h3>
          <ModelComparisonChart data={comparison} />
        </Card>
        <Card>
          <h3>Confusion Matrix</h3>
          <ConfusionMatrixChart matrix={latestMatrix} />
          <p className="muted">FP means false alarm. FN means a defective module was missed.</p>
        </Card>
      </div>

      <Card>
        <h3>Model Cards</h3>
        {!models.length ? <EmptyState title="No models in SQL Server" /> : (
          <div className="model-list">
            {models.map((model) => (
              <div className={`model-card ${model.is_active ? 'active-model' : ''}`} key={model.id}>
                <BrainCircuit />
                <div>
                  <strong>{model.name}</strong>
                  <span>{model.model_type} - {model.version} - ROC-AUC {fmtPercent(model.roc_auc)}</span>
                </div>
                <div className="button-row">
                  {!model.is_active && canDeploy ? <Button variant="secondary" onClick={() => activate(model.id)}>Apply Active Model</Button> : model.is_active ? <span className="active-pill">Active</span> : null}
                  {canDelete ? <Button variant="danger" onClick={() => deleteModel(model.id)}><Trash2 size={18} />Delete</Button> : null}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card>
        <h3>Training Runs</h3>
        {!runs.length ? <EmptyState title="No training runs" /> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Run ID</th>
                  <th>Dataset</th>
                  <th>Model Type</th>
                  <th>Accuracy</th>
                  <th>Precision</th>
                  <th>Recall</th>
                  <th>F1</th>
                  <th>ROC-AUC</th>
                  <th>Started</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr key={r.id}>
                    <td>{r.id}</td>
                    <td>{r.dataset_id || '-'}</td>
                    <td>{r.model_type}</td>
                    <td>{fmtPercent(r.accuracy)}</td>
                    <td>{fmtPercent(r.precision)}</td>
                    <td>{fmtPercent(r.recall)}</td>
                    <td>{fmtPercent(r.f1_score)}</td>
                    <td>{fmtPercent(r.roc_auc)}</td>
                    <td>{r.started_at ? new Date(r.started_at).toLocaleString() : '-'}</td>
                    <td>{canDelete ? <Button variant="danger" onClick={() => deleteRun(r.id)}><Trash2 size={18} />Delete Run</Button> : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
