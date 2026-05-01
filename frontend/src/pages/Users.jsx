import { Trash2, UserPlus } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import Button from '../components/common/Button.jsx';
import Card from '../components/common/Card.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import Loading from '../components/common/Loading.jsx';
import SectionHeader from '../components/common/SectionHeader.jsx';
import StatusBanner from '../components/common/StatusBanner.jsx';
import { authService } from '../auth/authService.js';
import { notify } from '../services/apiUtils.js';

export default function Users() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [updatingUserId, setUpdatingUserId] = useState(null);

  async function load() {
    setLoading(true);
    setMessage('');
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
    setUpdatingUserId(id);
    try {
      await authService.deleteUser(id);
      notify('User deleted', 'success');
      await load();
    } catch (err) {
      notify(err.message || 'Failed to delete user', 'error');
    } finally {
      setUpdatingUserId(null);
    }
  }

  async function changeRole(userId, newRole) {
    setUpdatingUserId(userId);
    try {
      await authService.updateUserRole(userId, newRole);
      notify(`Role updated to ${newRole}`, 'success');
      await load();
    } catch (err) {
      notify(err.message || 'Failed to update role', 'error');
    } finally {
      setUpdatingUserId(null);
    }
  }

  return (
    <div className="page-stack">
      <SectionHeader
        eyebrow="Access"
        title="Users"
        description={`${users.length} accounts`}
        actions={<Link className="btn btn-primary" to="/register"><UserPlus size={18} />Create</Link>}
      />
      {message ? <StatusBanner type="error" title="Users unavailable">{message}</StatusBanner> : null}
      {loading ? <Loading /> : (
        <Card>
          {!users.length ? <EmptyState title="No users" /> : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Email</th>
                    <th>Role</th>
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
                          {user.full_name ? <span className="table-kicker">{user.full_name}</span> : null}
                        </td>
                        <td>{user.email}</td>
                        <td><span className={`badge badge-${currentRole.toLowerCase()}`}>{currentRole}</span></td>
                        <td>
                          <select value={currentRole} onChange={(e) => changeRole(user.user_id, e.target.value)} disabled={isUpdating}>
                            <option value="Admin">Admin</option>
                            <option value="Developer">Developer</option>
                            <option value="Viewer">Viewer</option>
                          </select>
                          {isUpdating ? <span className="table-kicker">Updating...</span> : null}
                        </td>
                        <td><span className={`badge ${user.is_active ? 'badge-success' : 'badge-danger'}`}>{user.is_active ? 'Active' : 'Inactive'}</span></td>
                        <td>
                          <Button variant="danger" onClick={() => remove(user.user_id)} loading={isUpdating}>
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
