USE PermissionDB;
GO

MERGE dbo.Roles AS target
USING (VALUES
    ('Admin', 'Admin', 'Full system administrator'),
    ('Developer', 'Developer', 'AI model and dataset operator'),
    ('Viewer', 'Viewer', 'Read-only analyst')
) AS source (RoleCode, RoleName, Description)
ON target.RoleCode = source.RoleCode
WHEN NOT MATCHED THEN
    INSERT (RoleCode, RoleName, Description) VALUES (source.RoleCode, source.RoleName, source.Description);
GO

MERGE dbo.Permissions AS target
USING (VALUES
    ('USER_MANAGE', 'Manage users'),
    ('PROJECT_MANAGE', 'Manage projects'),
    ('DATASET_UPLOAD', 'Upload datasets'),
    ('DATASET_DELETE', 'Delete datasets'),
    ('MODEL_TRAIN', 'Train models'),
    ('MODEL_DEPLOY', 'Deploy active models'),
    ('MODEL_DELETE', 'Delete models'),
    ('MODEL_TEST', 'Test models'),
    ('MODEL_COMPARISON_VIEW', 'View model comparison'),
    ('CONFUSION_MATRIX_VIEW', 'View confusion matrix'),
    ('DASHBOARD_VIEW', 'View dashboard'),
    ('REPORT_VIEW', 'View reports'),
    ('REPORT_EXPORT', 'Export reports'),
    ('REPORT_DELETE', 'Delete reports'),
    ('HISTORY_VIEW', 'View history'),
    ('HISTORY_DELETE', 'Delete history'),
    ('SYSTEM_SETTING', 'System settings')
) AS source (PermissionCode, PermissionName)
ON target.PermissionCode = source.PermissionCode
WHEN NOT MATCHED THEN
    INSERT (PermissionCode, PermissionName) VALUES (source.PermissionCode, source.PermissionName);
GO

MERGE dbo.Modules AS target
USING (VALUES
    ('DASHBOARD', 'Dashboard'),
    ('METRICS', 'Metrics Explorer'),
    ('MODELS', 'AI Models'),
    ('HISTORY', 'History'),
    ('REPORTS', 'Reports'),
    ('SETTINGS', 'Settings'),
    ('USERS', 'Users')
) AS source (ModuleCode, ModuleName)
ON target.ModuleCode = source.ModuleCode
WHEN NOT MATCHED THEN
    INSERT (ModuleCode, ModuleName) VALUES (source.ModuleCode, source.ModuleName);
GO

INSERT INTO dbo.RolePermissions (RoleID, PermissionID)
SELECT r.RoleID, p.PermissionID
FROM dbo.Roles r
CROSS JOIN dbo.Permissions p
WHERE r.RoleCode = 'Admin'
  AND NOT EXISTS (SELECT 1 FROM dbo.RolePermissions rp WHERE rp.RoleID = r.RoleID AND rp.PermissionID = p.PermissionID);
GO

INSERT INTO dbo.RolePermissions (RoleID, PermissionID)
SELECT r.RoleID, p.PermissionID
FROM dbo.Roles r
JOIN dbo.Permissions p ON p.PermissionCode IN (
    'DATASET_UPLOAD', 'MODEL_TRAIN', 'MODEL_TEST', 'DASHBOARD_VIEW',
    'REPORT_VIEW', 'REPORT_EXPORT', 'HISTORY_VIEW',
    'MODEL_COMPARISON_VIEW', 'CONFUSION_MATRIX_VIEW'
)
WHERE r.RoleCode = 'Developer'
  AND NOT EXISTS (SELECT 1 FROM dbo.RolePermissions rp WHERE rp.RoleID = r.RoleID AND rp.PermissionID = p.PermissionID);
GO

INSERT INTO dbo.RolePermissions (RoleID, PermissionID)
SELECT r.RoleID, p.PermissionID
FROM dbo.Roles r
JOIN dbo.Permissions p ON p.PermissionCode IN (
    'DASHBOARD_VIEW', 'REPORT_VIEW', 'HISTORY_VIEW',
    'MODEL_COMPARISON_VIEW', 'CONFUSION_MATRIX_VIEW'
)
WHERE r.RoleCode = 'Viewer'
  AND NOT EXISTS (SELECT 1 FROM dbo.RolePermissions rp WHERE rp.RoleID = r.RoleID AND rp.PermissionID = p.PermissionID);
GO

PRINT 'Permission roles and permissions seeded. Run backend/scripts/seed_permission_users.py to create bcrypt users.';
GO
