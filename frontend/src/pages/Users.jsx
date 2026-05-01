import { Trash2, UserPlus } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import Button from '../components/common/Button.jsx';
import Card from '../components/common/Card.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import Loading from '../components/common/Loading.jsx';
import { authService } from '../auth/authService.js';

function showToast(message, type = 'success') {
  window.dispatchEvent(new CustomEvent('defectai:toast', { detail: { message, type } }));
}

export default function Users() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [updatingUserId, setUpdatingUserId] = useState(null);

  async function load() {
    setLoading(true);
    try {
      setUsers(await authService.users());
    } catch (err) {
      setMessage(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function remove(id) {
    if (!window.confirm(`Delete user #${id}?`)) return;
    try {
      await authService.deleteUser(id);
      showToast('User deleted successfully', 'success');
      await load();
    } catch (err) {
      showToast(err.message || 'Failed to delete user', 'error');
    }
  }

  /**
   * Thay đổi role của user
   * Gọi API PATCH /users/{user_id}/role
   */
  async function changeRole(userId, newRole) {
    setUpdatingUserId(userId);
    try {
      await authService.updateUserRole(userId, newRole);
      showToast(`Role updated to ${newRole} successfully`, 'success');
      await load();
    } catch (err) {
      showToast(err.message || 'Failed to update role', 'error');
    } finally {
      setUpdatingUserId(null);
    }
  }

  return (
    <div className="page-stack">
      <div className="section-header">
        <h2>Users Management</h2>
        <Link className="btn btn-primary" to="/register"><UserPlus size={18} />Create User</Link>
      </div>
      {message ? <div className="warning-panel">{message}</div> : null}
      {loading ? <Loading /> : (
        <Card>
          {!users.length ? <EmptyState title="No users" /> : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Email</th>
                    <th>Current Role</th>
                    <th>Change Role</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => {
                    const currentRole = user.roles?.[0] || 'Viewer';
                    const isUpdating = updatingUserId === user.user_id;
                    
                    return (
                      <tr key={user.user_id}>
                        <td>
                          <strong>{user.username}</strong>
                          {user.full_name && <><br /><span style={{ color: '#64748b', fontSize: '14px' }}>{user.full_name}</span></>}
                        </td>
                        <td>{user.email}</td>
                        <td>
                          <span className={`badge badge-${currentRole.toLowerCase()}`}>
                            {currentRole}
                          </span>
                        </td>
                        <td>
                          <select
                            value={currentRole}
                            onChange={(e) => changeRole(user.user_id, e.target.value)}
                            disabled={isUpdating}
                            style={{
                              padding: '6px 12px',
                              borderRadius: '6px',
                              border: '1px solid #cbd5e1',
                              fontSize: '14px',
                              cursor: isUpdating ? 'wait' : 'pointer',
                              opacity: isUpdating ? 0.6 : 1
                            }}
                          >
                            <option value="Admin">Admin</option>
                            <option value="Developer">Developer</option>
                            <option value="Viewer">Viewer</option>
                          </select>
                          {isUpdating && <span style={{ marginLeft: '8px', fontSize: '12px', color: '#6366f1' }}>Updating...</span>}
                        </td>
                        <td>
                          <span className={`badge ${user.is_active ? 'badge-success' : 'badge-danger'}`}>
                            {user.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td>
                          <Button variant="danger" onClick={() => remove(user.user_id)} disabled={isUpdating}>
                            <Trash2 size={16} />Delete
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

