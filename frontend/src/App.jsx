import { Navigate, Route, Routes } from 'react-router-dom';

import ProtectedRoute from './auth/ProtectedRoute.jsx';
import MainLayout from './layouts/MainLayout.jsx';
import Dashboard from './pages/Dashboard.jsx';
import MetricsExplorer from './pages/MetricsExplorer.jsx';
import AIModels from './pages/AIModels.jsx';
import Reports from './pages/Reports.jsx';
import Settings from './pages/Settings.jsx';
import History from './pages/History.jsx';
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import PublicRegister from './pages/PublicRegister.jsx';
import Forbidden from './pages/Forbidden.jsx';
import Users from './pages/Users.jsx';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/public-register" element={<PublicRegister />} />
      <Route path="/forbidden" element={<ProtectedRoute><Forbidden /></ProtectedRoute>} />
      <Route element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<ProtectedRoute permission="DASHBOARD_VIEW"><Dashboard /></ProtectedRoute>} />
        
        {/* Metrics Explorer - Viewer không được xem */}
        <Route path="/metrics" element={<ProtectedRoute allowedRoles={['Admin', 'Developer']} permission={['DATASET_UPLOAD', 'DASHBOARD_VIEW']}><MetricsExplorer /></ProtectedRoute>} />
        
        {/* AI Models / Training - Viewer không được xem */}
        <Route path="/models" element={<ProtectedRoute allowedRoles={['Admin', 'Developer']} permission={['MODEL_TRAIN', 'MODEL_COMPARISON_VIEW']}><AIModels /></ProtectedRoute>} />
        
        <Route path="/reports" element={<ProtectedRoute permission="REPORT_VIEW"><Reports /></ProtectedRoute>} />
        <Route path="/history" element={<ProtectedRoute permission="HISTORY_VIEW"><History /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute permission="SYSTEM_SETTING"><Settings /></ProtectedRoute>} />
        
        {/* Users - Chỉ Admin mới được xem */}
        <Route path="/users" element={<ProtectedRoute allowedRoles={['Admin']} permission="USER_MANAGE"><Users /></ProtectedRoute>} />
        
        {/* Register (Admin tạo user) - Chỉ Admin */}
        <Route path="/register" element={<ProtectedRoute allowedRoles={['Admin']} permission="USER_MANAGE"><Register /></ProtectedRoute>} />
      </Route>
    </Routes>
  );
}
