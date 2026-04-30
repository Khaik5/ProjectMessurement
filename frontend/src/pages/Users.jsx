import { Trash2, UserPlus } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import Button from '../components/common/Button.jsx';
import Card from '../components/common/Card.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import Loading from '../components/common/Loading.jsx';
import { authService } from '../auth/authService.js';

export default function Users() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

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
    await authService.deleteUser(id);
    await load();
  }

  return (
    <div className="page-stack">
      <div className="section-header">
        <h2>Users</h2>
        <Link className="btn btn-primary" to="/register"><UserPlus size={18} />Create User</Link>
      </div>
      {message ? <div className="warning-panel">{message}</div> : null}
      {loading ? <Loading /> : (
        <Card>
          {!users.length ? <EmptyState title="No users" /> : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>User</th><th>Email</th><th>Roles</th><th>Status</th><th>Action</th></tr></thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.user_id}>
                      <td><strong>{user.username}</strong><br />{user.full_name}</td>
                      <td>{user.email}</td>
                      <td>{user.roles?.join(', ')}</td>
                      <td>{user.is_active ? 'Active' : 'Inactive'}</td>
                      <td><Button variant="danger" onClick={() => remove(user.user_id)}><Trash2 size={16} />Delete</Button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

