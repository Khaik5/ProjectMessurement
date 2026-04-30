import { motion } from 'framer-motion';
import { useState } from 'react';

import Button from '../components/common/Button.jsx';
import Card from '../components/common/Card.jsx';
import { authService } from '../auth/authService.js';

export default function Register() {
  const [form, setForm] = useState({ username: '', full_name: '', email: '', password: '', confirm: '', role: 'Developer' });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  async function submit(event) {
    event.preventDefault();
    setMessage('');
    setError('');
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) return setError('Email is invalid');
    if (form.password.length < 6) return setError('Password must be at least 6 characters');
    if (form.password !== form.confirm) return setError('Confirm password does not match');
    try {
      await authService.register({
        username: form.username,
        full_name: form.full_name,
        email: form.email,
        password: form.password,
        role: form.role,
      });
      setMessage('User created successfully');
      setForm({ username: '', full_name: '', email: '', password: '', confirm: '', role: 'Developer' });
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="page-stack">
      <Card>
        <div className="section-header"><h2>Create Account</h2></div>
        {message ? <div className="success-panel">{message}</div> : null}
        {error ? <div className="warning-panel">{error}</div> : null}
        <form className="form-grid" onSubmit={submit}>
          <label>Username<input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required /></label>
          <label>Full name<input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></label>
          <label>Email<input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /></label>
          <label>Role<select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}><option>Admin</option><option>Developer</option><option>Viewer</option></select></label>
          <label>Password<input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required /></label>
          <label>Confirm password<input type="password" value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} required /></label>
          <div><Button>Create Account</Button></div>
        </form>
      </Card>
    </motion.div>
  );
}

