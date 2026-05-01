import { Lock, Mail, User } from 'lucide-react';
import { motion } from 'framer-motion';
import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';

import { useAuth } from '../auth/AuthContext.jsx';
import axiosClient from '../api/axiosClient.js';

export default function PublicRegister() {
  const { user } = useAuth();
  const [form, setForm] = useState({ 
    username: '', 
    email: '', 
    password: '', 
    confirm_password: '' 
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  // Nếu đã đăng nhập, chuyển về dashboard
  if (user) return <Navigate to="/dashboard" replace />;

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError('');
    
    // Validation
    if (form.username.length < 3) {
      setError('Username phải có ít nhất 3 ký tự');
      setLoading(false);
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      setError('Email không hợp lệ');
      setLoading(false);
      return;
    }

    if (form.password.length < 6) {
      setError('Mật khẩu phải có ít nhất 6 ký tự');
      setLoading(false);
      return;
    }

    if (form.password !== form.confirm_password) {
      setError('Mật khẩu xác nhận không khớp');
      setLoading(false);
      return;
    }
    
    try {
      // Gọi API public-register
      await axiosClient.post('/auth/public-register', {
        username: form.username,
        email: form.email,
        password: form.password,
        confirm_password: form.confirm_password
      });
      
      setSuccess(true);
      // Chuyển về trang login sau 2 giây
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Đăng ký thất bại. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  }

  // Hiển thị màn hình thành công
  if (success) {
    return (
      <div className="auth-page">
        <motion.div
          className="auth-card"
          initial={{ opacity: 0, scale: 0.94, y: 18 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.38 }}
        >
          <h1>Thành công!</h1>
          <p style={{ textAlign: 'center', color: '#64748b', marginBottom: '24px' }}>
            Tài khoản của bạn đã được tạo thành công. Đang chuyển đến trang đăng nhập...
          </p>
          <Link to="/login">
            <button className="auth-button">ĐI ĐẾN TRANG ĐĂNG NHẬP</button>
          </Link>
        </motion.div>
      </div>
    );
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
        <h1>Register</h1>
        
        <label>
          <span>Username</span>
          <div className="auth-input">
            <User size={18} />
            <input 
              value={form.username} 
              onChange={(e) => setForm({ ...form, username: e.target.value })} 
              placeholder="Type your username" 
              required 
              autoFocus 
            />
          </div>
        </label>

        <label>
          <span>Email</span>
          <div className="auth-input">
            <Mail size={18} />
            <input 
              type="email"
              value={form.email} 
              onChange={(e) => setForm({ ...form, email: e.target.value })} 
              placeholder="Type your email" 
              required 
            />
          </div>
        </label>

        <label>
          <span>Password</span>
          <div className="auth-input">
            <Lock size={18} />
            <input 
              type="password" 
              value={form.password} 
              onChange={(e) => setForm({ ...form, password: e.target.value })} 
              placeholder="Type your password" 
              required 
            />
          </div>
        </label>

        <label>
          <span>Confirm Password</span>
          <div className="auth-input">
            <Lock size={18} />
            <input 
              type="password" 
              value={form.confirm_password} 
              onChange={(e) => setForm({ ...form, confirm_password: e.target.value })} 
              placeholder="Confirm your password" 
              required 
            />
          </div>
        </label>

        <div style={{ textAlign: 'center', fontSize: '14px', color: '#64748b', marginTop: '8px' }}>
          Already have an account? <Link to="/login" style={{ color: '#6366f1', fontWeight: '600', textDecoration: 'none' }}>Sign in</Link>
        </div>

        {error ? <div className="auth-error">{error}</div> : null}
        
        <button className="auth-button" disabled={loading}>
          {loading ? 'CREATING ACCOUNT...' : 'CREATE ACCOUNT'}
        </button>
      </motion.form>
    </div>
  );
}
