import { useAuth } from './AuthContext.jsx';

/**
 * Custom Hook để kiểm tra role và permissions của user
 * Sử dụng: const { isAdmin, isDeveloper, isViewer, hasRole, hasPermission } = useRole();
 */
export function useRole() {
  const { user } = useAuth();

  const roles = user?.roles || [];
  const permissions = user?.permissions || [];

  // Kiểm tra role cụ thể
  const isAdmin = roles.includes('Admin');
  const isDeveloper = roles.includes('Developer');
  const isViewer = roles.includes('Viewer');

  /**
   * Kiểm tra xem user có role cụ thể không
   * @param {string|string[]} allowedRoles - Role hoặc mảng roles cần kiểm tra
   * @returns {boolean}
   */
  const hasRole = (allowedRoles) => {
    if (!allowedRoles) return true;
    if (typeof allowedRoles === 'string') {
      return roles.includes(allowedRoles);
    }
    if (Array.isArray(allowedRoles)) {
      return allowedRoles.some(role => roles.includes(role));
    }
    return false;
  };

  /**
   * Kiểm tra xem user có permission cụ thể không
   * @param {string|string[]} requiredPermissions - Permission hoặc mảng permissions cần kiểm tra
   * @returns {boolean}
   */
  const hasPermission = (requiredPermissions) => {
    // Admin có toàn quyền
    if (isAdmin) return true;

    if (!requiredPermissions) return true;
    if (typeof requiredPermissions === 'string') {
      return permissions.includes(requiredPermissions);
    }
    if (Array.isArray(requiredPermissions)) {
      return requiredPermissions.some(perm => permissions.includes(perm));
    }
    return false;
  };

  /**
   * Kiểm tra xem có thể xem module User không
   * Chỉ Admin mới được xem
   */
  const canViewUsers = isAdmin;

  /**
   * Kiểm tra xem có thể xóa không
   * Viewer không được xóa bất cứ thứ gì
   * Developer không được xóa History và Report
   */
  const canDelete = (resource) => {
    if (isViewer) return false;
    if (isAdmin) return true;
    if (isDeveloper) {
      // Developer không được xóa History và Report
      if (resource === 'history' || resource === 'report') return false;
      return true;
    }
    return false;
  };

  /**
   * Kiểm tra xem có thể edit không
   * Viewer không được edit bất cứ thứ gì
   */
  const canEdit = !isViewer;

  /**
   * Kiểm tra xem có thể add/create không
   * Viewer không được add bất cứ thứ gì
   */
  const canAdd = !isViewer;

  /**
   * Kiểm tra xem có thể export không
   * Viewer không được export
   */
  const canExport = !isViewer;

  /**
   * Kiểm tra xem có thể train model không
   * Chỉ Admin và Developer mới được train
   */
  const canTrainModel = isAdmin || isDeveloper;

  /**
   * Kiểm tra xem có thể xem trang Training Model không
   * Viewer không được xem
   */
  const canViewTraining = !isViewer;

  /**
   * Kiểm tra xem có thể xem trang Metrics Explorer không
   * Viewer không được xem
   */
  const canViewMetrics = !isViewer;

  return {
    // Role checks
    isAdmin,
    isDeveloper,
    isViewer,
    hasRole,
    hasPermission,

    // Specific permissions
    canViewUsers,
    canDelete,
    canEdit,
    canAdd,
    canExport,
    canTrainModel,
    canViewTraining,
    canViewMetrics,

    // Raw data
    roles,
    permissions,
  };
}
