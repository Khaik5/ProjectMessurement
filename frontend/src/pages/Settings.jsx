import { Database, RefreshCw, Server } from 'lucide-react';
import { useEffect, useState } from 'react';

import axiosClient from '../api/axiosClient.js';
import Button from '../components/common/Button.jsx';
import Card from '../components/common/Card.jsx';
import { checkBackendHealth } from '../services/backendService.js';
import { dashboardService } from '../services/dashboardService.js';
import { projectService } from '../services/projectService.js';

const projectId = Number(import.meta.env.VITE_DEFAULT_PROJECT_ID || 1);

export default function Settings() {
  const [health, setHealth] = useState(null);
  const [project, setProject] = useState(null);
  const [summary, setSummary] = useState(null);
  const [message, setMessage] = useState('');

  async function load() {
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
    }
  }

  useEffect(() => { load(); }, []);

  async function seed() {
    try {
      await axiosClient.post('/seed');
      setMessage('Seed data executed successfully.');
      await load();
    } catch (err) {
      setMessage(err.message);
    }
  }

  return (
    <div className="grid-3">
      <Card><Database /><h3>Database connection status</h3><pre>{JSON.stringify(health || {}, null, 2)}</pre></Card>
      <Card><Server /><h3>Current project</h3><pre>{JSON.stringify(project || {}, null, 2)}</pre></Card>
      <Card><RefreshCw /><h3>Seed data</h3><p className="muted">Runs backend/sql/seed_data.sql through the API.</p><Button onClick={seed}>Seed SQL Server</Button>{message ? <p className="notice">{message}</p> : null}</Card>
      <Card className="span-3"><h3>Active model</h3><pre>{JSON.stringify(summary?.active_model || {}, null, 2)}</pre></Card>
    </div>
  );
}
