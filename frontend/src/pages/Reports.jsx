import { Download, FileSpreadsheet, FileText, Flame, SlidersHorizontal, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';

import Button from '../components/common/Button.jsx';
import Card from '../components/common/Card.jsx';
import Loading from '../components/common/Loading.jsx';
import SectionHeader from '../components/common/SectionHeader.jsx';
import StatusBanner from '../components/common/StatusBanner.jsx';
import AuditLogTable from '../components/tables/AuditLogTable.jsx';
import ReportsTable from '../components/tables/ReportsTable.jsx';
import KpiCard from '../components/dashboard/KpiCard.jsx';
import { reportService } from '../services/reportService.js';
import axiosClient from '../api/axiosClient.js';
import { datasetService } from '../services/datasetService.js';
import { useAuth } from '../auth/AuthContext.jsx';
import { unwrapApi } from '../services/apiUtils.js';

const projectId = Number(import.meta.env.VITE_DEFAULT_PROJECT_ID || 1);

export default function Reports() {
  const { hasPermission } = useAuth();
  const [reports, setReports] = useState([]);
  const [logs, setLogs] = useState([]);
  const [datasets, setDatasets] = useState([]);
  const [datasetId, setDatasetId] = useState('');
  const [selected, setSelected] = useState([]);
  const [loading, setLoading] = useState(false);
  const [exportLoading, setExportLoading] = useState('');
  const [exportOptions, setExportOptions] = useState({
    include_full_modules: true,
    include_heatmap: true,
    include_charts: true,
    top_n: 20
  });
  const [message, setMessage] = useState('');

  async function load() {
    setLoading(true);
    try {
      const [reportData, logData, historyData] = await Promise.all([
        reportService.list(projectId),
        axiosClient.get(`/audit-logs/project/${projectId}`).then(unwrapApi),
        datasetService.history(projectId)
      ]);
      setReports(reportData);
      setLogs(logData);
      setDatasets(historyData || []);
      if (!datasetId && historyData?.length) setDatasetId(String(historyData[0].id));
    } catch (err) {
      setMessage(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function generate() {
    setLoading(true);
    try {
      await reportService.generate({ project_id: projectId, dataset_id: datasetId ? Number(datasetId) : undefined, title: 'DefectAI Analysis Report', days: 30 });
      await load();
    } catch (err) {
      setMessage(err.message);
    } finally {
      setLoading(false);
    }
  }

  const canExport = hasPermission('REPORT_EXPORT');
  const canDelete = hasPermission('REPORT_DELETE');
  const selectedDataset = datasets.find((item) => String(item.id) === String(datasetId));
  const selectedHasAnalysis = Number(selectedDataset?.prediction_count || 0) > 0;
  const selectedFileName = selectedDataset?.file_name || selectedDataset?.name || `dataset_${datasetId}`;

  function setExportOption(name, value) {
    setExportOptions((prev) => ({ ...prev, [name]: value }));
  }

  async function download(type) {
    if (!datasetId) return setMessage('Select a dataset first.');
    if (!selectedHasAnalysis && type !== 'csv') return setMessage('Analyze the selected dataset before exporting PDF or Excel.');
    setExportLoading(type);
    try {
      const blob = await reportService.exportDataset(datasetId, type, exportOptions);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `DefectAI_Report_${selectedFileName.replace(/[^a-z0-9._-]+/gi, '_')}.${type}`;
      link.click();
      URL.revokeObjectURL(url);
      setMessage(`${type.toUpperCase()} export generated.`);
    } catch (err) {
      setMessage(err.message);
    } finally {
      setExportLoading('');
    }
  }

  async function deleteSelected() {
    if (!selected.length || !window.confirm('Are you sure you want to delete selected reports?')) return;
    await Promise.all(selected.map((id) => reportService.remove(id)));
    setSelected([]);
    await load();
  }

  return (
    <div className="page-stack">
      <SectionHeader
        eyebrow="Reports"
        title="Exports"
        description="Reports, audit events, and dataset exports."
      />
      {message ? <StatusBanner type="info" title="Report status">{message}</StatusBanner> : null}
      {loading ? <Loading /> : null}
      <Card className="command-card">
        <div className="command-main">
          <span className="eyebrow">Export Control</span>
          <h3>Generate Report</h3>
          <p>{datasetId ? `${selectedFileName} selected` : 'Select a dataset to scope exports.'}</p>
        </div>
        <div className="command-actions">
          <select value={datasetId} onChange={(e) => setDatasetId(e.target.value)} aria-label="Dataset">
            <option value="">Select dataset...</option>
            {datasets.map((item) => <option key={item.id} value={item.id}>#{item.id} - {item.file_name || item.name}</option>)}
          </select>
          <Button onClick={generate} loading={loading}><FileText size={18} />Generate</Button>
          {canDelete ? <Button variant="danger" onClick={deleteSelected} disabled={!selected.length}><Trash2 size={18} />Delete</Button> : null}
        </div>
      </Card>
      <div className="kpi-grid">
        <KpiCard label="Reports" value={reports.length} />
        <KpiCard label="Datasets" value={datasets.length} />
        <KpiCard label="Prediction Events" value={logs.filter((log) => log.action?.includes('prediction')).length} />
        <KpiCard label="Selected Dataset" value={datasetId || '-'} />
      </div>
      <div className="grid-2">
        <Card><SectionHeader compact title="Generated Reports" /><ReportsTable rows={reports} selected={selected} onSelect={setSelected} selectable={canDelete} /></Card>
        <Card>
          <SectionHeader compact title="Dataset Export" description="Professional PDF, Excel workbook, or raw CSV." />
          {!selectedHasAnalysis && datasetId ? (
            <StatusBanner type="warning" title="Analysis required">PDF and Excel exports need prediction records for this dataset.</StatusBanner>
          ) : null}
          <div className="export-options">
            <div className="export-options-title"><SlidersHorizontal size={18} /><strong>Report Options</strong></div>
            <label>
              <input
                type="checkbox"
                checked={exportOptions.include_full_modules}
                onChange={(event) => setExportOption('include_full_modules', event.target.checked)}
              />
              Full module appendix
            </label>
            <label>
              <input
                type="checkbox"
                checked={exportOptions.include_heatmap}
                onChange={(event) => setExportOption('include_heatmap', event.target.checked)}
              />
              Heatmap
            </label>
            <label>
              <input
                type="checkbox"
                checked={exportOptions.include_charts}
                onChange={(event) => setExportOption('include_charts', event.target.checked)}
              />
              Charts
            </label>
            <label className="topn-field">
              Top modules
              <input
                type="number"
                min="5"
                max="100"
                value={exportOptions.top_n}
                onChange={(event) => setExportOption('top_n', Number(event.target.value || 20))}
              />
            </label>
          </div>
          <div className="export-grid">
            {[
              { type: 'pdf', label: 'PDF Report', icon: FileText, detail: 'Summary, charts, heatmap' },
              { type: 'xlsx', label: 'Excel Workbook', icon: FileSpreadsheet, detail: '7 sheets with charts' },
              { type: 'csv', label: 'CSV Data', icon: Flame, detail: 'Module prediction rows' }
            ].map((item) => {
              const Icon = item.icon;
              const disabled = !datasetId || Boolean(exportLoading) || (!selectedHasAnalysis && item.type !== 'csv');
              return (
              canExport ? (
                <button key={item.type} className={`action-card ${exportLoading === item.type ? 'is-loading' : ''}`} onClick={() => download(item.type)} disabled={disabled}>
                  <Icon size={20} />
                  <strong>{exportLoading === item.type ? 'Preparing...' : item.label}</strong>
                  <span>{item.detail}</span>
                  <small><Download size={14} /> Download</small>
                </button>
              ) : null
            );})}
          </div>
        </Card>
      </div>
      <Card><SectionHeader compact title="Audit Log" /><AuditLogTable rows={logs} /></Card>
    </div>
  );
}
