import { Download, Eye, FileBarChart2, RefreshCw, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import Button from '../components/common/Button.jsx';
import Card from '../components/common/Card.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import Loading from '../components/common/Loading.jsx';
import { historyService } from '../services/historyService.js';
import { fmtNumber, fmtPercent } from '../utils/formatters.js';

const projectId = Number(import.meta.env.VITE_DEFAULT_PROJECT_ID || 1);

export default function History() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
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
    await historyService.reanalyze(datasetId, projectId);
    await viewDashboard(datasetId);
  }

  async function archive(datasetId) {
    const ok = window.confirm(`Archive dataset #${datasetId}? (MetricRecords/Predictions will be kept)`);
    if (!ok) return;
    await historyService.archive(datasetId);
    await load();
  }

  if (loading) return <Loading label="Loading dataset history..." />;

  return (
    <div className="page-stack">
      <div className="section-header">
        <div>
          <h2>History</h2>
          <p className="muted">All uploaded/analyzed datasets. Actions are applied per dataset to avoid mixing results.</p>
        </div>
        <Button onClick={load} variant="secondary"><RefreshCw size={18} />Refresh</Button>
      </div>

      {error ? <EmptyState title="Backend or SQL Server unavailable" description={error} /> : null}

      {!items.length ? (
        <EmptyState title="No datasets yet" description="Upload a CSV in Metrics Explorer to start." />
      ) : (
        <Card>
          <div style={{ overflowX: 'auto' }}>
            <table className="table">
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
                    <td>{d.status}</td>
                    <td>{d.model_used || '-'}</td>
                    <td>{fmtPercent(d.avg_defect_probability)}</td>
                    <td>{fmtNumber(d.high_risk_count)}</td>
                    <td>{fmtNumber(d.critical_count)}</td>
                    <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                      <Button variant="secondary" onClick={() => viewDashboard(d.id)}><Eye size={18} />View Dashboard</Button>{' '}
                      <Button variant="secondary" onClick={() => viewMetrics(d.id)}><FileBarChart2 size={18} />View Metrics</Button>{' '}
                      <Button variant="secondary" onClick={() => reanalyze(d.id)}><RefreshCw size={18} />Re-analyze</Button>{' '}
                      <a className="btn btn-secondary" href={`${import.meta.env.VITE_API_BASE_URL}/datasets/${d.id}/export/xlsx`}><Download size={18} />Export Excel</a>{' '}
                      <Button variant="danger" onClick={() => archive(d.id)}><Trash2 size={18} />Archive</Button>
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

