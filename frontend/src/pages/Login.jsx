import { Lock, User } from 'lucide-react';
import { motion } from 'framer-motion';
import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '../auth/AuthContext.jsx';

export default function Login() {
  const { login, user } = useAuth();
  const [form, setForm] = useState({ username: '', password: '', remember: true });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  if (user) return <Navigate to="/dashboard" replace />;

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(form.username, form.password);
      navigate(location.state?.from?.pathname || '/dashboard', { replace: true });
    } catch (err) {
      setError(err.message || 'Invalid username or password');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <motion.form
        className="auth-card"
        onSubmit={submit}
        initial={{ opacity: 0, scale: 0.94, y: 18 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.38 }}
      >
        <h1>Login</h1>
        <label>
          <span>Username</span>
          <div className="auth-input"><User size={18} /><input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} placeholder="Type your username" autoFocus /></div>
        </label>
        <label>
          <span>Password</span>
          <div className="auth-input"><Lock size={18} /><input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="Type your password" /></div>
        </label>
        <div className="auth-row">
          <label className="auth-check"><input type="checkbox" checked={form.remember} onChange={(e) => setForm({ ...form, remember: e.target.checked })} />Remember me</label>
          <span>Forgot password?</span>
        </div>
        {error ? <div className="auth-error">{error}</div> : null}
        <button className="auth-button" disabled={loading}>{loading ? 'Signing in...' : 'LOGIN'}</button>
        <div style={{ textAlign: 'center', fontSize: '14px', color: '#64748b', marginTop: '12px' }}>
          Chưa có tài khoản? <Link to="/public-register" style={{ color: '#6366f1', fontWeight: '600', textDecoration: 'none' }}>Đăng ký ngay</Link>
        </div>
      </motion.form>
    </div>
  );
}

