import { Download, FileText, Trash2 } from 'lucide-react';
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

  async function download(type) {
    if (!datasetId) return setMessage('Select a dataset first.');
    try {
      const blob = await reportService.exportDataset(datasetId, type);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `defectai_dataset_${datasetId}.${type}`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setMessage(err.message);
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
        description="Generate and export analysis artifacts."
        actions={(
          <>
          <select value={datasetId} onChange={(e) => setDatasetId(e.target.value)}>
            <option value="">Select dataset...</option>
            {datasets.map((item) => <option key={item.id} value={item.id}>#{item.id} - {item.file_name || item.name}</option>)}
          </select>
          <Button onClick={generate} loading={loading}><FileText size={18} />Generate</Button>
          {canDelete ? <Button variant="danger" onClick={deleteSelected}><Trash2 size={18} />Delete Selected</Button> : null}
          </>
        )}
      />
      {message ? <StatusBanner type="info" title="Report status">{message}</StatusBanner> : null}
      {loading ? <Loading /> : null}
      <div className="kpi-grid">
        <KpiCard label="Reports" value={reports.length} />
        <KpiCard label="Datasets" value={datasets.length} />
        <KpiCard label="Prediction Events" value={logs.filter((log) => log.action?.includes('prediction')).length} />
        <KpiCard label="Selected Dataset" value={datasetId || '-'} />
      </div>
      <div className="grid-2">
        <Card><SectionHeader compact title="Generated Reports" /><ReportsTable rows={reports} selected={selected} onSelect={setSelected} selectable={canDelete} /></Card>
        <Card>
          <SectionHeader compact title="Dataset Export" description="Selected dataset only." />
          <div className="export-list">
            {['pdf', 'xlsx', 'csv'].map((type) => (
              canExport ? <Button key={type} variant="secondary" onClick={() => download(type)}><Download size={16} />Export {type.toUpperCase()}</Button> : null
            ))}
          </div>
        </Card>
      </div>
      <Card><SectionHeader compact title="Audit Log" /><AuditLogTable rows={logs} /></Card>
    </div>
  );
}
