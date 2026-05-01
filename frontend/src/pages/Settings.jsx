import { Activity, Database, RefreshCw, Server } from 'lucide-react';
import { useEffect, useState } from 'react';

import axiosClient from '../api/axiosClient.js';
import Button from '../components/common/Button.jsx';
import Card from '../components/common/Card.jsx';
import SectionHeader from '../components/common/SectionHeader.jsx';
import StatusBanner from '../components/common/StatusBanner.jsx';
import KpiCard from '../components/dashboard/KpiCard.jsx';
import { checkBackendHealth } from '../services/backendService.js';
import { dashboardService } from '../services/dashboardService.js';
import { projectService } from '../services/projectService.js';

const projectId = Number(import.meta.env.VITE_DEFAULT_PROJECT_ID || 1);

export default function Settings() {
  const [health, setHealth] = useState(null);
  const [project, setProject] = useState(null);
  const [summary, setSummary] = useState(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    setMessage('');
    try {
      const [healthData, projectData, summaryData] = await Promise.all([
        checkBackendHealth(),
        projectService.get(projectId),
        dashboardService.summary(projectId)
      ]);
      setHealth(healthData);
      setProject(projectData);
      setSummary(summaryData);
    } catch (err) {
      setMessage(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function seed() {
    setLoading(true);
    try {
      await axiosClient.post('/seed');
      setMessage('Seed completed.');
      await load();
    } catch (err) {
      setMessage(err.message);
    } finally {
      setLoading(false);
    }
  }

  const db = health?.database || health;

  return (
    <div className="page-stack">
      <SectionHeader
        eyebrow="System"
        title="Settings"
        description="Backend, database, and project state."
        actions={<Button variant="secondary" onClick={load} loading={loading}><RefreshCw size={18} />Refresh</Button>}
      />

      {message ? <StatusBanner type={message.includes('completed') ? 'success' : 'warning'} title="System status">{message}</StatusBanner> : null}

      <div className="kpi-grid">
        <KpiCard label="Backend" value={health?.backend || (health?.connected ? 'ok' : '-')} icon={Server} tone="teal" />
        <KpiCard label="Database" value={db?.connected === false ? 'offline' : 'online'} icon={Database} tone={db?.connected === false ? 'danger' : 'success'} />
        <KpiCard label="Project" value={`#${project?.id || projectId}`} icon={Activity} />
        <KpiCard label="Active Model" value={summary?.active_model_name ? 'ready' : 'none'} icon={Activity} />
      </div>

      <div className="grid-2">
        <Card>
          <SectionHeader compact title="Connection" />
          <div className="insight-row">
            <div className="metric-panel"><strong>{db?.server_name || '-'}</strong><span>SQL Server</span></div>
            <div className="metric-panel"><strong>{db?.database_name || '-'}</strong><span>Database</span></div>
            <div className="metric-panel">
              <strong>{db?.connected === false ? 'Offline' : 'Online'}</strong>
              <span className={`badge ${db?.connected === false ? 'badge-danger' : 'badge-success'}`}>Connection</span>
            </div>
          </div>
        </Card>
        <Card>
          <SectionHeader compact title="Seed Data" description="Use only for local demo reset." />
          <div className="command-actions" style={{ gridTemplateColumns: '1fr auto' }}>
            <span className="badge badge-info">SQL Server</span>
            <Button onClick={seed} loading={loading}>Seed SQL Server</Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
