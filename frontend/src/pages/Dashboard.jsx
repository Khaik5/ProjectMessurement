import { AlertTriangle, BrainCircuit, Layers3, Play, TrendingUp } from 'lucide-react';
import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import Button from '../components/common/Button.jsx';
import Card from '../components/common/Card.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import Loading from '../components/common/Loading.jsx';
import AlertPanel from '../components/dashboard/AlertPanel.jsx';
import KpiCard from '../components/dashboard/KpiCard.jsx';
import RiskSummary from '../components/dashboard/RiskSummary.jsx';
import ChurnProbabilityChart from '../components/charts/ChurnProbabilityChart.jsx';
import CouplingDistributionChart from '../components/charts/CouplingDistributionChart.jsx';
import ConfusionMatrixChart from '../components/charts/ConfusionMatrixChart.jsx';
import DefectProbabilityTrend from '../components/charts/DefectProbabilityTrend.jsx';
import LocComplexityScatter from '../components/charts/LocComplexityScatter.jsx';
import ModelComparisonChart from '../components/charts/ModelComparisonChart.jsx';
import QualityRadarChart from '../components/charts/QualityRadarChart.jsx';
import RiskDistributionPie from '../components/charts/RiskDistributionPie.jsx';
import RiskHeatmap from '../components/charts/RiskHeatmap.jsx';
import TopRiskModulesBar from '../components/charts/TopRiskModulesBar.jsx';
import { dashboardService } from '../services/dashboardService.js';
import { datasetService } from '../services/datasetService.js';
import { predictionService } from '../services/predictionService.js';
import { projectService } from '../services/projectService.js';
import { fmtNumber, fmtPercent } from '../utils/formatters.js';

const projectId = Number(import.meta.env.VITE_DEFAULT_PROJECT_ID || 1);

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [charts, setCharts] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchParams, setSearchParams] = useSearchParams();

  async function load() {
    setLoading(true);
    setError('');
    try {
      let datasetId = searchParams.get('datasetId');
      if (!datasetId) {
        const state = await projectService.state(projectId);
        if (state?.current_analysis_dataset_id) {
          datasetId = String(state.current_analysis_dataset_id);
          setSearchParams({ datasetId });
        }
      }
      const [summaryData, chartData, historyData] = await Promise.all([
        dashboardService.summary(projectId, datasetId ? Number(datasetId) : undefined),
        dashboardService.charts(projectId, datasetId ? Number(datasetId) : undefined),
        datasetService.history(projectId)
      ]);
      setSummary(summaryData);
      setCharts(chartData);
      setHistory(historyData || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function runAnalysisForCurrent() {
    setError('');
    try {
      const datasetId = searchParams.get('datasetId');
      if (!datasetId) throw new Error('No dataset selected. Upload a dataset first.');
      await predictionService.run({ project_id: projectId, dataset_id: Number(datasetId) });
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function switchDataset(datasetId) {
    setSearchParams({ datasetId: String(datasetId) });
    setLoading(true);
    setError('');
    try {
      await datasetService.setCurrent(datasetId);
      const [summaryData, chartData, historyData] = await Promise.all([
        dashboardService.summary(projectId, Number(datasetId)),
        dashboardService.charts(projectId, Number(datasetId)),
        datasetService.history(projectId)
      ]);
      setSummary(summaryData);
      setCharts(chartData);
      setHistory(historyData || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);
  const stats = summary?.metric_statistics || {};
  const radar = [
    { metric: 'LOC', score: Math.min(100, Number(stats.average_loc || 0) / 15) },
    { metric: 'Complexity', score: Math.min(100, Number(stats.average_complexity || 0) * 1.25) },
    { metric: 'Coupling', score: Math.min(100, Number(stats.average_coupling || 0) * 3) },
    { metric: 'Churn', score: Math.min(100, Number(stats.average_churn || 0) / 4.2) },
    { metric: 'Probability', score: Math.min(100, Number(summary?.avg_defect_probability || 0) * 100) }
  ].filter((item) => item.score > 0);

  if (loading) return <Loading label="Loading dashboard from SQL Server..." />;
  const datasetId = searchParams.get('datasetId');
  const hasDataset = Boolean(summary?.dataset?.id || datasetId);
  const needsAnalysis = hasDataset && summary?.analyzed === false;

  if (!error && !hasDataset) {
    return (
      <motion.div className="page-stack" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <section className="hero-card">
          <span>System Measurement & Analysis</span>
          <h2>AI Software Defect Dashboard</h2>
          <p>Upload a CSV in Metrics Explorer, then run analysis to populate this dashboard.</p>
        </section>
        <EmptyState title="No dataset selected" description="Upload a dataset and analyze it, or open a dataset from History." />
      </motion.div>
    );
  }

  return (
    <motion.div className="page-stack" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      <section className="hero-card">
        <span>System Measurement & Analysis</span>
        <h2>AI Software Defect Dashboard</h2>
        <p>Predict defect-prone software modules from LOC, complexity, coupling, and code churn metrics.</p>
      </section>

      <Card>
        <div className="section-header">
          <div>
            <h3>Viewing Analysis: {summary?.dataset_name || `Dataset #${datasetId}`}</h3>
            <p className="muted">
              Model used: {summary?.active_model_name || 'DefectAI P7 Production Model'}
            </p>
          </div>
          <div className="button-row">
            <select value={datasetId || ''} onChange={(event) => switchDataset(event.target.value)}>
              {history.map((item) => <option key={item.id} value={item.id}>#{item.id} - {item.file_name || item.name}</option>)}
            </select>
            <Button variant="secondary" onClick={load}>Refresh</Button>
            <Button onClick={runAnalysisForCurrent}><Play size={18} />Run New Analysis</Button>
          </div>
        </div>
      </Card>

      {error ? (
        <div style={{ marginTop: 16 }}>
          <EmptyState title="Backend or SQL Server unavailable" description={error} />
          <div style={{ marginTop: 12, display: 'flex', gap: 12 }}>
            <Button onClick={load}>Retry</Button>
          </div>
        </div>
      ) : null}

      <div className="kpi-grid">
        <KpiCard
          label="Total Modules"
          value={fmtNumber(summary?.total_modules)}
          helper="Modules in current dataset"
          icon={Layers3}
        />
        <KpiCard label="No Defect" value={fmtNumber(summary?.no_defect_count)} helper="Prediction label: No Defect" icon={Layers3} />
        <KpiCard label="High Risk" value={fmtNumber(summary?.high_risk_count)} helper="HIGH + CRITICAL predictions" icon={AlertTriangle} />
        <KpiCard label="Avg Defect Probability" value={fmtPercent(summary?.avg_defect_probability)} helper="Current analysis average" icon={TrendingUp} />
        <KpiCard label="Active Model Accuracy" value={fmtPercent(summary?.active_model_accuracy)} helper={summary?.active_model_name || 'No active model'} icon={BrainCircuit} />
      </div>

      {needsAnalysis ? (
        <Card>
          <div className="section-header">
            <div>
              <h3>{summary?.message || 'Dataset uploaded but not analyzed yet'}</h3>
              <p className="muted">Run analysis to generate results for this dataset.</p>
            </div>
            <Button onClick={runAnalysisForCurrent}><Play size={18} />Analyze now</Button>
          </div>
        </Card>
      ) : null}

      <div className="grid-2">
        <Card><h3>Risk Distribution</h3><RiskDistributionPie data={charts?.risk_distribution || []} /><RiskSummary distribution={charts?.risk_distribution || []} /></Card>
        <Card><h3>Top 10 Risky Modules</h3><TopRiskModulesBar data={charts?.top_risky_modules || []} /></Card>
      </div>

      <div className="grid-2">
        <Card><h3>Defect Probability Trend</h3><DefectProbabilityTrend data={charts?.probability_trend || []} /></Card>
        <Card><h3>Model Performance</h3><ModelComparisonChart data={charts?.model_performance || []} /></Card>
      </div>

      <div className="grid-2">
        <Card>
          <h3>Confusion Matrix (Active Model)</h3>
          <ConfusionMatrixChart matrix={(() => { try { return charts?.confusion_matrix ? JSON.parse(charts.confusion_matrix) : null; } catch { return null; } })()} />
        </Card>
        <Card><h3>Quality Radar Profile</h3><QualityRadarChart data={radar} /></Card>
      </div>

      <Card>
        <div className="section-header"><h3>Risk Heatmap</h3><Button onClick={runAnalysisForCurrent}><Play size={18} />Analyze now</Button></div>
        <RiskHeatmap data={charts?.risk_heatmap || []} />
      </Card>

      <div className="grid-2">
        <Card><h3>LOC vs Complexity</h3><LocComplexityScatter data={charts?.loc_complexity_scatter || []} /></Card>
        <Card><h3>Churn vs Defect Probability</h3><ChurnProbabilityChart data={charts?.churn_probability || []} /></Card>
      </div>

      <div className="grid-2">
        <Card><h3>Coupling Distribution</h3><CouplingDistributionChart data={charts?.coupling_distribution || []} /></Card>
        <Card>
          <h3>Critical Alerts</h3>
          <AlertPanel items={charts?.critical_alerts || []} />
          {!charts?.critical_alerts?.length ? <EmptyState title="No critical alerts" description="Analyze a dataset to populate critical alerts." /> : null}
        </Card>
      </div>
    </motion.div>
  );
}
