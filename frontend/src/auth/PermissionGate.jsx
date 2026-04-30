import { useAuth } from './AuthContext.jsx';

export default function PermissionGate({ permission, children, fallback = null }) {
  const { hasPermission } = useAuth();
  return hasPermission(permission) ? children : fallback;
}

