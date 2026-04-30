import { ShieldAlert } from 'lucide-react';
import { Link } from 'react-router-dom';

import Card from '../components/common/Card.jsx';

export default function Forbidden() {
  return (
    <div className="page-stack">
      <Card>
        <div className="empty-state">
          <ShieldAlert size={44} />
          <strong>Permission denied</strong>
          <p>You do not have access to this page.</p>
          <Link className="btn btn-primary" to="/dashboard">Back to Dashboard</Link>
        </div>
      </Card>
    </div>
  );
}

