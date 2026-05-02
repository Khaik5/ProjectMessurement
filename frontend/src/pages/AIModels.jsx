import {
  Activity,
  BarChart3,
  BrainCircuit,
  Database,
  Eye,
  GitCompare,
  RefreshCw,
  Rocket,
  ShieldCheck,
  SlidersHorizontal,
  Target,
  Trash2
} from 'lucide-react';
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

const MODEL_OPTIONS = [
  { key: 'logistic_regression', label: 'Logistic Regression', icon: BarChart3, helper: 'Linear classifier' },
  { key: 'random_forest', label: 'Random Forest', icon: ShieldCheck, helper: 'Tree ensemble' },
  { key: 'neural_network', label: 'Neural Network', icon: BrainCircuit, helper: 'MLP classifier' }
];

const PROFILE_OPTIONS = [
  { key: 'balanced_production', label: 'Balanced Production', helper: 'F1 with recall floor', tone: 'badge-info' },
  { key: 'high_recall', label: 'High Recall', helper: 'Safety first', tone: 'badge-warning' },
  { key: 'high_precision', label: 'High Precision', helper: 'Low noise', tone: 'badge-success' },
  { key: 'best_roc_auc', label: 'Best ROC-AUC', helper: 'Class separation', tone: 'badge-info' },
  { key: 'best_pr_auc', label: 'Best PR-AUC', helper: 'Imbalance aware', tone: 'badge-info' },
  { key: 'custom', label: 'Custom', helper: 'Advanced controls', tone: 'badge-muted' }
];

const PROFILE_DEFAULTS = {
  balanced_production: { recall_floor: 0.8, precision_floor: 0.7, beta: 1.3, threshold_min: 0.2, threshold_max: 0.8, threshold_step: 0.01, best_model_metric: 'f1' },
  high_recall: { recall_floor: 0.9, precision_floor: 0.6, beta: 2, threshold_min: 0.2, threshold_max: 0.8, threshold_step: 0.01, best_model_metric: 'fbeta' },
  high_precision: { recall_floor: 0.6, precision_floor: 0.8, beta: 1, threshold_min: 0.2, threshold_max: 0.8, threshold_step: 0.01, best_model_metric: 'precision' },
  best_roc_auc: { recall_floor: 0.75, precision_floor: 0.65, beta: 1, threshold_min: 0.2, threshold_max: 0.8, threshold_step: 0.01, best_model_metric: 'roc_auc' },
  best_pr_auc: { recall_floor: 0.75, precision_floor: 0.65, beta: 1, threshold_min: 0.2, threshold_max: 0.8, threshold_step: 0.01, best_model_metric: 'pr_auc' },
  custom: { recall_floor: 0.8, precision_floor: 0.7, beta: 1, threshold_min: 0.2, threshold_max: 0.8, threshold_step: 0.01, best_model_metric: 'f1' }
};

function parseJson(value, fallback = null) {
  try {
    return value ? JSON.parse(value) : fallback;
  } catch {
    return fallback;
  }
}

function profileLabel(key) {
  return PROFILE_OPTIONS.find((profile) => profile.key === key)?.label || key || 'Balanced Production';
}

function modelLabel(key) {
  return MODEL_OPTIONS.find((model) => model.key === key)?.label || key || '-';
}

function modelMetrics(model) {
  return parseJson(model?.metrics_json, {}) || {};
}

function riskWarnings(model) {
  const metrics = modelMetrics(model);
  const warnings = [];
  if ((metrics.false_positive_rate || 0) > 0.55) warnings.push('High FP');
  if ((metrics.false_negative_rate || 0) > 0.30) warnings.push('High FN');
  if ((model?.roc_auc || 0) > 0 && model.roc_auc < 0.65) warnings.push('Low ROC');
  return warnings;
}

export default function AIModels() {
  const { hasPermission } = useAuth();
  const [models, setModels] = useState([]);
  const [runs, setRuns] = useState([]);
  const [comparison, setComparison] = useState([]);
  const [datasets, setDatasets] = useState([]);
  const [guide, setGuide] = useState(null);
  const [form, setForm] = useState({
    dataset_id: '',
    test_size: 0.2,
    random_state: 42,
    selected_models: MODEL_OPTIONS.map((model) => model.key),
    training_profile: 'balanced_production',
    auto_activate_best: true,
    threshold_config: PROFILE_DEFAULTS.custom
  });
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [selectedModel, setSelectedModel] = useState(null);
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

  function toggleModel(modelKey) {
    setForm((current) => {
      const selected = new Set(current.selected_models);
      if (selected.has(modelKey)) selected.delete(modelKey);
      else selected.add(modelKey);
      return { ...current, selected_models: Array.from(selected) };
    });
  }

  function selectAllModels() {
    setForm((current) => ({ ...current, selected_models: MODEL_OPTIONS.map((model) => model.key) }));
  }

  function updateProfile(profile) {
    setForm((current) => ({
      ...current,
      training_profile: profile,
      threshold_config: { ...(PROFILE_DEFAULTS[profile] || PROFILE_DEFAULTS.custom) }
    }));
  }

  async function trainProduction() {
    if (!hasPermission('MODEL_TRAIN')) {
      setError('Permission denied: MODEL_TRAIN is required');
      return;
    }
    const nextErrors = {};
    const testSize = Number(form.test_size);
    const randomState = Number(form.random_state);
    if (!form.dataset_id) nextErrors.dataset_id = 'Select a labeled dataset';
    if (!form.selected_models.length) nextErrors.selected_models = 'Choose at least one model';
    if (!Number.isFinite(testSize) || testSize < 0.1 || testSize > 0.5) nextErrors.test_size = 'Use 0.1 to 0.5';
    if (!Number.isInteger(randomState) || randomState < 0) nextErrors.random_state = 'Use a non-negative integer';
    setFormErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;

    setTraining(true);
    setError('');
    setMessage('');
    setWarnings([]);
    try {
      const payload = {
        project_id: projectId,
        dataset_id: Number(form.dataset_id),
        selected_models: form.selected_models,
        training_profile: form.training_profile,
        test_size: testSize,
        random_state: randomState,
        auto_activate_best: form.auto_activate_best
      };
      if (form.training_profile === 'custom') payload.threshold_config = form.threshold_config;
      const result = await mlService.trainProduction(payload);
      setWarnings(result.warnings || []);
      setMessage(`Activated ${result.best_model_name} at threshold ${Number(result.threshold || 0).toFixed(2)}.`);
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
    setMessage(`Model #${id} is now active.`);
    await load();
  }

  async function deleteModel(id) {
    if (!hasPermission('MODEL_DELETE')) {
      setError('Permission denied: MODEL_DELETE is required');
      return;
    }
    if (!window.confirm(`Delete model #${id}?`)) return;
    try {
      await mlService.deleteModel(id);
      setMessage(`Model #${id} deleted.`);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function deleteRun(id) {
    if (!hasPermission('MODEL_DELETE')) {
      setError('Permission denied: MODEL_DELETE is required');
      return;
    }
    if (!window.confirm(`Delete training run #${id}?`)) return;
    await mlService.deleteTrainingRun(id);
    await load();
  }

  function retrainWith(model) {
    setForm((current) => ({
      ...current,
      dataset_id: model.dataset_id ? String(model.dataset_id) : current.dataset_id,
      selected_models: [model.model_type],
      training_profile: model.training_profile || 'balanced_production'
    }));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  const activeModel = models.find((item) => item.is_active);
  const bestModel = models.find((item) => item.is_best) || activeModel;
  const latestRun = runs[0];
  const latestMatrix = useMemo(() => parseJson(latestRun?.confusion_matrix_json), [latestRun]);
  const selectedMetrics = modelMetrics(selectedModel);
  const featureList = parseJson(activeModel?.feature_list_json, []);
  const canTrain = hasPermission('MODEL_TRAIN');
  const canDeploy = hasPermission('MODEL_DEPLOY');
  const canDelete = hasPermission('MODEL_DELETE');
  const allModelsSelected = form.selected_models.length === MODEL_OPTIONS.length;

  return (
    <div className="page-stack">
      <SectionHeader
        eyebrow="ML Ops"
        title="Model Training"
        description="Train, compare, and deploy model variants."
        actions={(
          <>
            <Button variant="secondary" onClick={load} disabled={loading || training}><RefreshCw size={20} />Refresh</Button>
            {canTrain ? <Button onClick={trainProduction} loading={training} disabled={loading}><Rocket size={20} />Train Selected</Button> : null}
          </>
        )}
      />

      {loading ? <Loading label="Loading models from SQL Server..." /> : null}
      {training ? <Card><strong>Training selected models...</strong><div className="progress-bar" style={{ marginTop: 12 }}><div /></div></Card> : null}
      {message ? <StatusBanner type="success" title="Done">{message}</StatusBanner> : null}
      {warnings.map((warning) => <StatusBanner type="warning" title="Training warning" key={warning}>{warning}</StatusBanner>)}
      {error ? <StatusBanner type="error" title="Action failed">{error}</StatusBanner> : null}

      <Card>
        <SectionHeader compact title="Training Panel" description="Choose algorithms and objective." />
        <div className="form-grid" style={{ marginTop: 14 }}>
          <FormField label="Dataset" error={formErrors.dataset_id}>
            <select value={form.dataset_id} onChange={(e) => setForm({ ...form, dataset_id: e.target.value })}>
              <option value="">Select dataset...</option>
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  #{d.id} - {d.file_name || d.name} ({d.labeled_records || d.row_count} labeled rows)
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Deployment">
            <select value={form.auto_activate_best ? 'yes' : 'no'} onChange={(e) => setForm({ ...form, auto_activate_best: e.target.value === 'yes' })}>
              <option value="yes">Auto activate best</option>
              <option value="no">Train only</option>
            </select>
          </FormField>
          <FormField label="Test size" error={formErrors.test_size}><input value={form.test_size} onChange={(e) => setForm({ ...form, test_size: e.target.value })} /></FormField>
          <FormField label="Random state" error={formErrors.random_state}><input value={form.random_state} onChange={(e) => setForm({ ...form, random_state: e.target.value })} /></FormField>
        </div>

        <div className="training-selector">
          <div>
            <div className="selector-title">
              <strong>Model Selection</strong>
              <Button size="sm" variant={allModelsSelected ? 'primary' : 'secondary'} onClick={selectAllModels}>Train All</Button>
            </div>
            {formErrors.selected_models ? <small className="field-error">{formErrors.selected_models}</small> : null}
            <div className="selector-grid">
              {MODEL_OPTIONS.map((option) => {
                const Icon = option.icon;
                const checked = form.selected_models.includes(option.key);
                return (
                  <button type="button" key={option.key} className={`choice-card ${checked ? 'is-selected' : ''}`} onClick={() => toggleModel(option.key)}>
                    <Icon size={20} />
                    <strong>{option.label}</strong>
                    <span>{option.helper}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <div className="selector-title">
              <strong>Training Profile</strong>
              <Button size="sm" variant="secondary" onClick={() => setShowAdvanced((value) => !value)}><SlidersHorizontal size={15} />Custom</Button>
            </div>
            <div className="profile-grid">
              {PROFILE_OPTIONS.map((profile) => (
                <button type="button" key={profile.key} className={`profile-card ${form.training_profile === profile.key ? 'is-selected' : ''}`} onClick={() => updateProfile(profile.key)} title={profile.helper}>
                  <span className={`badge ${profile.tone}`}>{profile.label}</span>
                  <small>{profile.helper}</small>
                </button>
              ))}
            </div>
          </div>
        </div>

        {showAdvanced || form.training_profile === 'custom' ? (
          <div className="advanced-panel">
            {['recall_floor', 'precision_floor', 'beta', 'threshold_min', 'threshold_max', 'threshold_step'].map((field) => (
              <FormField label={field.replaceAll('_', ' ')} key={field}>
                <input
                  value={form.threshold_config?.[field] ?? ''}
                  onChange={(e) => setForm({
                    ...form,
                    training_profile: 'custom',
                    threshold_config: { ...form.threshold_config, [field]: Number(e.target.value) }
                  })}
                />
              </FormField>
            ))}
            <FormField label="best model metric">
              <select
                value={form.threshold_config.best_model_metric}
                onChange={(e) => setForm({ ...form, training_profile: 'custom', threshold_config: { ...form.threshold_config, best_model_metric: e.target.value } })}
              >
                <option value="f1">F1</option>
                <option value="fbeta">F-beta</option>
                <option value="roc_auc">ROC-AUC</option>
                <option value="pr_auc">PR-AUC</option>
                <option value="balanced_score">Balanced score</option>
              </select>
            </FormField>
          </div>
        ) : null}

        <div className="button-row" style={{ marginTop: 16 }}>
          {canTrain ? <Button onClick={trainProduction} loading={training}><Rocket size={18} />Train Selected Models</Button> : null}
        </div>
      </Card>

      <div className="kpi-grid">
        <KpiCard label="Active Model" value={activeModel ? modelLabel(activeModel.model_type) : '-'} helper={activeModel?.training_profile || 'No active model'} />
        <KpiCard label="Best Model" value={bestModel ? modelLabel(bestModel.model_type) : '-'} helper={bestModel?.selection_strategy || '-'} />
        <KpiCard label="F1-score" value={fmtPercent(activeModel?.f1_score)} />
        <KpiCard label="PR-AUC" value={fmtPercent(activeModel?.pr_auc)} />
        <KpiCard label="Threshold" value={activeModel?.threshold ? Number(activeModel.threshold).toFixed(2) : '-'} helper="Artifact threshold" />
        <KpiCard label="Features" value={featureList?.length || 0} helper="Safe model columns" />
      </div>

      <Card>
        <SectionHeader compact title="Model Cards" description={`${models.length} trained model variants`} />
        {!models.length ? <EmptyState title="No models in SQL Server" description="Train one or more algorithms to create model cards." /> : (
          <div className="model-card-grid">
            {models.map((model) => {
              const metrics = modelMetrics(model);
              const cardWarnings = riskWarnings(model);
              return (
                <div className={`model-card-rich ${model.is_active ? 'active-model' : ''}`} key={model.id}>
                  <div className="model-card-head">
                    <div className="model-icon"><BrainCircuit size={20} /></div>
                    <div>
                      <strong>{modelLabel(model.model_type)}</strong>
                      <span>#{model.id} - {model.version}</span>
                    </div>
                    <div className="model-badges">
                      {model.is_active ? <span className="active-pill">Active</span> : null}
                      {model.is_best ? <span className="badge badge-success">Best</span> : null}
                      <span className="badge badge-info">{profileLabel(model.training_profile)}</span>
                    </div>
                  </div>

                  <div className="metric-mini-grid">
                    <span><small>F1</small><strong>{fmtPercent(model.f1_score)}</strong></span>
                    <span><small>Precision</small><strong>{fmtPercent(model.precision)}</strong></span>
                    <span><small>Recall</small><strong>{fmtPercent(model.recall)}</strong></span>
                    <span><small>ROC-AUC</small><strong>{fmtPercent(model.roc_auc)}</strong></span>
                    <span><small>PR-AUC</small><strong>{fmtPercent(model.pr_auc)}</strong></span>
                    <span><small>Threshold</small><strong>{model.threshold ? Number(model.threshold).toFixed(2) : '-'}</strong></span>
                  </div>

                  <div className="confusion-mini">
                    <span>TP {metrics?.confusion_matrix?.tp ?? '-'}</span>
                    <span>TN {metrics?.confusion_matrix?.tn ?? '-'}</span>
                    <span>FP {metrics?.confusion_matrix?.fp ?? '-'}</span>
                    <span>FN {metrics?.confusion_matrix?.fn ?? '-'}</span>
                  </div>

                  {cardWarnings.length ? (
                    <div className="model-warning-row">
                      {cardWarnings.map((warning) => <span className="badge badge-warning" key={warning}>{warning}</span>)}
                    </div>
                  ) : null}

                  <div className="button-row">
                    {!model.is_active && canDeploy ? <Button size="sm" variant="secondary" onClick={() => activate(model.id)}><Target size={15} />Activate</Button> : null}
                    <Button size="sm" variant="secondary" onClick={() => setSelectedModel(model)}><Eye size={15} />Metrics</Button>
                    <Button size="sm" variant="secondary" onClick={() => document.getElementById('model-comparison')?.scrollIntoView({ behavior: 'smooth' })}><GitCompare size={15} />Compare</Button>
                    {canTrain ? <Button size="sm" variant="secondary" onClick={() => retrainWith(model)}><Rocket size={15} />Retrain</Button> : null}
                    {canDelete ? <Button size="sm" variant="danger" disabled={model.is_active} onClick={() => deleteModel(model.id)}><Trash2 size={15} />Delete</Button> : null}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      {selectedModel ? (
        <Card>
          <SectionHeader compact title={`${modelLabel(selectedModel.model_type)} Metrics`} actions={<Button size="sm" variant="secondary" onClick={() => setSelectedModel(null)}>Close</Button>} />
          <div className="grid-2">
            <ConfusionMatrixChart
              matrix={selectedMetrics?.confusion_matrix}
              metrics={{
                accuracy: selectedModel.accuracy,
                precision: selectedModel.precision,
                recall: selectedModel.recall,
                f1: selectedModel.f1_score
              }}
            />
            <div className="page-stack">
              <StatusBanner type="info" title="Selection">{selectedModel.selection_strategy || '-'} · score {selectedModel.selection_score ? Number(selectedModel.selection_score).toFixed(3) : '-'}</StatusBanner>
              <pre>{JSON.stringify(selectedMetrics, null, 2)}</pre>
            </div>
          </div>
        </Card>
      ) : null}

      <div className="grid-2" id="model-comparison">
        <Card>
          <SectionHeader compact title="Comparison" />
          <ModelComparisonChart data={comparison} />
        </Card>
        <Card>
          <SectionHeader compact title="Latest Confusion Matrix" />
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

      <div className="grid-2">
        <Card>
          <SectionHeader compact title="Workflow" />
          <TrainingGuide guide={guide} />
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
                    <th>Model</th>
                    <th>Profile</th>
                    <th>Precision</th>
                    <th>Recall</th>
                    <th>F1</th>
                    <th>PR-AUC</th>
                    <th>Threshold</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.slice(0, 10).map((r) => (
                    <tr key={r.id}>
                      <td>{r.id}</td>
                      <td>{r.dataset_id || '-'}</td>
                      <td>{modelLabel(r.model_type)}</td>
                      <td>{profileLabel(r.training_profile)}</td>
                      <td>{fmtPercent(r.precision)}</td>
                      <td>{fmtPercent(r.recall)}</td>
                      <td>{fmtPercent(r.f1_score)}</td>
                      <td>{fmtPercent(r.pr_auc)}</td>
                      <td>{r.threshold ? Number(r.threshold).toFixed(2) : '-'}</td>
                      <td>{canDelete ? <Button size="sm" variant="danger" onClick={() => deleteRun(r.id)}><Trash2 size={15} />Delete</Button> : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
