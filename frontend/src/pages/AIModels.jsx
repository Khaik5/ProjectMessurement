import { BrainCircuit, Database, RefreshCw, Rocket, ShieldCheck, Trash2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import Button from '../components/common/Button.jsx';
import Card from '../components/common/Card.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import Loading from '../components/common/Loading.jsx';
import FormField from '../components/common/FormField.jsx';
import SectionHeader from '../components/common/SectionHeader.jsx';
import StatusBanner from '../components/common/StatusBanner.jsx';
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
  const [formErrors, setFormErrors] = useState({});

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
      
      setForm((current) => {
        const stillTrainable = trainable?.some((dataset) => String(dataset.id) === String(current.dataset_id));
        if (stillTrainable) return current;
        return { ...current, dataset_id: trainable?.length ? String(trainable[0].id) : '' };
      });
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
    const nextErrors = {};
    const testSize = Number(form.test_size);
    const randomState = Number(form.random_state);
    if (!Number.isFinite(testSize) || testSize < 0.1 || testSize > 0.5) nextErrors.test_size = 'Use 0.1 to 0.5';
    if (!Number.isInteger(randomState) || randomState < 0) nextErrors.random_state = 'Use a non-negative integer';
    setFormErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;
    setTraining(true);
    setError('');
    setMessage('');
    setWarnings([]);
    try {
      const result = await mlService.trainProduction({
        project_id: projectId,
        dataset_id: Number(form.dataset_id),
        test_size: testSize,
        random_state: randomState,
        auto_activate_best: true
      });
      setWarnings(result.warnings || []);
      setMessage(`Production model activated: ${result.best_model_type}.`);
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
      <SectionHeader
        eyebrow="ML Ops"
        title="Model Training"
        description="Train, compare, and deploy the production classifier."
        actions={(
          <>
          <Button variant="secondary" onClick={load} disabled={loading || training}><RefreshCw size={20} />Refresh</Button>
          {canTrain ? <Button onClick={trainProduction} loading={training} disabled={loading}><Rocket size={20} />Train</Button> : null}
          </>
        )}
      />

      {loading ? <Loading label="Loading models from SQL Server..." /> : null}
      {training ? <Card><strong>Training production model...</strong><div className="progress-bar" style={{ marginTop: 12 }}><div /></div></Card> : null}
      {message ? <StatusBanner type="success" title="Production model activated">{message}</StatusBanner> : null}
      {warnings.map((warning) => <StatusBanner type="warning" title="Training warning" key={warning}>{warning}</StatusBanner>)}
      {error ? <StatusBanner type="error" title="Training failed">{error}</StatusBanner> : null}

      <Card>
        <SectionHeader compact title="Production Model" description={productionModel?.artifact_path || 'No artifact deployed'} actions={productionModel?.is_active ? <span className="active-pill">Active</span> : null} />
        {!productionModel ? (
          <EmptyState title="No production model" description="Choose a labeled dataset and train the production model." />
        ) : (
          <div className="grid-3">
            <div className="metric-panel"><ShieldCheck size={22} /><strong>{productionModel.name}</strong><span>{productionModel.model_type} - {productionModel.version}</span></div>
            <div className="metric-panel"><Database size={22} /><strong>{featureList?.length || 23}</strong><span>Feature contract</span></div>
            <div className="metric-panel"><BrainCircuit size={22} /><strong>{fmtPercent(productionModel.roc_auc)}</strong><span>ROC-AUC</span></div>
          </div>
        )}
      </Card>

      <div className="kpi-grid">
        <KpiCard label="Accuracy" value={fmtPercent(productionModel?.accuracy)} />
        <KpiCard label="Precision" value={fmtPercent(productionModel?.precision)} />
        <KpiCard label="Recall" value={fmtPercent(productionModel?.recall)} />
        <KpiCard label="F1-score" value={fmtPercent(productionModel?.f1_score)} />
        <KpiCard label="ROC-AUC" value={fmtPercent(productionModel?.roc_auc)} />
        <KpiCard label="PR-AUC" value={fmtPercent(productionModel?.pr_auc)} />
        <KpiCard label="Threshold" value={productionModel?.threshold ? Number(productionModel.threshold).toFixed(2) : '-'} helper={productionModel?.selection_strategy || 'balanced_f1_with_recall_floor'} />
      </div>

      <div className="grid-2">
        <Card>
          <SectionHeader compact title="Train" description="Compare all algorithms and activate the best." />
          <div className="form-grid" style={{ marginTop: 14 }}>
            <FormField label="Dataset">
              <select value={form.dataset_id} onChange={(e) => setForm({ ...form, dataset_id: e.target.value })}>
                <option value="">Select dataset...</option>
                {datasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    #{d.id} - {d.file_name || d.name} ({d.labeled_records || d.row_count} labeled rows)
                  </option>
                ))}
              </select>
            </FormField>
            <FormField label="Test size" error={formErrors.test_size}><input value={form.test_size} onChange={(e) => setForm({ ...form, test_size: e.target.value })} /></FormField>
            <FormField label="Random state" error={formErrors.random_state}><input value={form.random_state} onChange={(e) => setForm({ ...form, random_state: e.target.value })} /></FormField>
            <FormField label="Deployment"><input value="Auto activate best" readOnly /></FormField>
          </div>
          <div className="button-row" style={{ marginTop: 14 }}>
            {canTrain ? <Button onClick={trainProduction} loading={training}><Rocket size={18} />Train Model</Button> : null}
          </div>
        </Card>
        <Card>
          <SectionHeader compact title="Workflow" />
          <TrainingGuide guide={guide} />
        </Card>
      </div>

      <div className="grid-2">
        <Card>
          <SectionHeader compact title="Comparison" />
          <ModelComparisonChart data={comparison} />
        </Card>
        <Card>
          <SectionHeader compact title="Confusion Matrix" />
          <ConfusionMatrixChart
            matrix={latestMatrix}
            metrics={{
              accuracy: latestRun?.accuracy,
              precision: latestRun?.precision,
              recall: latestRun?.recall,
              f1: latestRun?.f1_score
            }}
          />
        </Card>
      </div>

      <Card>
        <SectionHeader compact title="Model Cards" />
        {!models.length ? <EmptyState title="No models in SQL Server" /> : (
          <div className="model-list">
            {models.map((model) => (
              <div className={`model-card ${model.is_active ? 'active-model' : ''}`} key={model.id}>
                <BrainCircuit />
                <div>
                  <strong>{model.name}</strong>
                  <span>{model.model_type} - {model.version}</span>
                  <div className="model-score">
                    <span className="badge">ROC-AUC {fmtPercent(model.roc_auc)}</span>
                    <span className="badge">PR-AUC {fmtPercent(model.pr_auc)}</span>
                    <span className="badge">Threshold {model.threshold ? Number(model.threshold).toFixed(2) : '-'}</span>
                    <span className="badge">F1 {fmtPercent(model.f1_score)}</span>
                  </div>
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
        <SectionHeader compact title="Training Runs" />
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
                  <th>PR-AUC</th>
                  <th>Threshold</th>
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
                    <td>{fmtPercent(r.pr_auc)}</td>
                    <td>{r.threshold ? Number(r.threshold).toFixed(2) : '-'}</td>
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
