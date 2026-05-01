import { Download, Eye, FileBarChart2, RefreshCw, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import Button from '../components/common/Button.jsx';
import Card from '../components/common/Card.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import Loading from '../components/common/Loading.jsx';
import SectionHeader from '../components/common/SectionHeader.jsx';
import StatusBanner from '../components/common/StatusBanner.jsx';
import { historyService } from '../services/historyService.js';
import { fmtNumber, fmtPercent } from '../utils/formatters.js';

const projectId = Number(import.meta.env.VITE_DEFAULT_PROJECT_ID || 1);

function statusBadge(status) {
  const value = String(status || 'UNKNOWN').toUpperCase();
  if (value === 'ANALYZED') return 'badge-success';
  if (value === 'FAILED') return 'badge-danger';
  if (value === 'ARCHIVED') return 'badge-muted';
  return 'badge-info';
}

export default function History() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busyId, setBusyId] = useState(null);
  const navigate = useNavigate();

  async function load() {
    setLoading(true);
    setError('');
    try {
      const data = await historyService.list(projectId);
      setItems(data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function viewDashboard(datasetId) {
    await historyService.setCurrent(datasetId);
    navigate(`/dashboard?datasetId=${datasetId}`);
  }

  async function viewMetrics(datasetId) {
    navigate(`/metrics?datasetId=${datasetId}`);
  }

  async function reanalyze(datasetId) {
    setBusyId(datasetId);
    try {
      await historyService.reanalyze(datasetId, projectId);
      await viewDashboard(datasetId);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyId(null);
    }
  }

  async function archive(datasetId) {
    const ok = window.confirm(`Archive dataset #${datasetId}? (MetricRecords/Predictions will be kept)`);
    if (!ok) return;
    setBusyId(datasetId);
    try {
      await historyService.archive(datasetId);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyId(null);
    }
  }

  if (loading) return <Loading label="Loading dataset history..." />;

  return (
    <div className="page-stack">
      <SectionHeader
        eyebrow="Datasets"
        title="History"
        description={`${fmtNumber(items.length)} datasets tracked`}
        actions={<Button onClick={load} variant="secondary"><RefreshCw size={18} />Refresh</Button>}
      />

      {error ? <StatusBanner type="error" title="History unavailable">{error}</StatusBanner> : null}

      {!items.length ? (
        <EmptyState title="No datasets yet" description="Upload a CSV in Metrics Explorer to start." />
      ) : (
        <Card>
          <div className="table-wrap">
            <table className="table history-table">
              <thead>
                <tr>
                  <th>Dataset ID</th>
                  <th>File Name</th>
                  <th>Uploaded At</th>
                  <th>Row Count</th>
                  <th>Has Label</th>
                  <th>Status</th>
                  <th>Used Model</th>
                  <th>Avg Probability</th>
                  <th>High Risk</th>
                  <th>Critical</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((d) => (
                  <tr key={d.id}>
                    <td>{d.id}</td>
                    <td>{d.file_name || d.name}</td>
                    <td>{d.uploaded_at ? new Date(d.uploaded_at).toLocaleString() : '-'}</td>
                    <td>{fmtNumber(d.row_count)}</td>
                    <td>{d.has_label ? 'Yes' : 'No'}</td>
                    <td><span className={`badge ${statusBadge(d.status)}`}>{d.status || 'UNKNOWN'}</span></td>
                    <td>{d.model_used || '-'}</td>
                    <td>{fmtPercent(d.avg_defect_probability)}</td>
                    <td>{fmtNumber(d.high_risk_count)}</td>
                    <td>{fmtNumber(d.critical_count)}</td>
                    <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                      <div className="row-actions history-actions">
                        <Button size="sm" variant="secondary" onClick={() => viewDashboard(d.id)}><Eye size={15} />Dashboard</Button>
                        <Button size="sm" variant="secondary" onClick={() => viewMetrics(d.id)}><FileBarChart2 size={15} />Metrics</Button>
                        <Button size="sm" variant="secondary" loading={busyId === d.id} onClick={() => reanalyze(d.id)}><RefreshCw size={15} />Analyze</Button>
                        <a className="btn btn-secondary btn-sm" href={`${import.meta.env.VITE_API_BASE_URL}/datasets/${d.id}/export/xlsx`}><Download size={15} />Excel</a>
                        <Button size="sm" variant="danger" onClick={() => archive(d.id)} disabled={busyId === d.id}><Trash2 size={15} />Archive</Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}

