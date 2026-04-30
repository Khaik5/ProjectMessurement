USE DefectAI_P7_DB;
GO

DELETE FROM dbo.AuditLogs;
DELETE FROM dbo.Reports;
DELETE FROM dbo.Predictions;
DELETE FROM dbo.TrainingRuns;
DELETE FROM dbo.MLModels;
DELETE FROM dbo.MetricRecords;
DELETE FROM dbo.MetricsDatasets;
DELETE FROM dbo.CodeModules;
DELETE FROM dbo.ProjectState;
DELETE FROM dbo.Projects;
DELETE FROM dbo.RiskLevels;
DELETE FROM dbo.Users;
GO

DBCC CHECKIDENT ('dbo.Users', RESEED, 0);
DBCC CHECKIDENT ('dbo.RiskLevels', RESEED, 0);
DBCC CHECKIDENT ('dbo.Projects', RESEED, 0);
DBCC CHECKIDENT ('dbo.CodeModules', RESEED, 0);
DBCC CHECKIDENT ('dbo.ProjectState', RESEED, 0);
DBCC CHECKIDENT ('dbo.MetricsDatasets', RESEED, 0);
DBCC CHECKIDENT ('dbo.MetricRecords', RESEED, 0);
DBCC CHECKIDENT ('dbo.MLModels', RESEED, 0);
DBCC CHECKIDENT ('dbo.TrainingRuns', RESEED, 0);
DBCC CHECKIDENT ('dbo.Predictions', RESEED, 0);
DBCC CHECKIDENT ('dbo.Reports', RESEED, 0);
DBCC CHECKIDENT ('dbo.AuditLogs', RESEED, 0);
GO

INSERT INTO dbo.RiskLevels (name, min_probability, max_probability, color, suggested_action)
VALUES
('LOW', 0.00, 0.30, '#22c55e', 'Continue monitoring'),
('MEDIUM', 0.30, 0.60, '#f59e0b', 'Review module and add targeted tests.'),
('HIGH', 0.60, 0.80, '#f97316', 'Require code review and increase test coverage.'),
('CRITICAL', 0.80, 1.00, '#dc2626', 'Immediate QA inspection and refactoring recommended.');

INSERT INTO dbo.Users (username, email, password_hash, role, is_active)
VALUES ('admin', 'admin@defectai.local', 'demo-password-hash', 'admin', 1);

INSERT INTO dbo.Projects (name, description, owner_id, is_active)
VALUES ('Apollo_Backend_v2.4', 'Software quality assurance project for P7 defect prediction.', 1, 1);

INSERT INTO dbo.CodeModules (project_id, module_name, module_path, language)
VALUES
(1, 'auth_service.main', '/core/auth/auth_service.main', 'Python'),
(1, 'PaymentProcessor.py', '/services/payment/PaymentProcessor.py', 'Python'),
(1, 'DatabaseMigrationTask.kt', '/jobs/db/DatabaseMigrationTask.kt', 'Kotlin'),
(1, 'QueryEngine.cpp', '/core/query/QueryEngine.cpp', 'C++'),
(1, 'StorageInterface.go', '/storage/StorageInterface.go', 'Go'),
(1, 'api_gateway_router', '/gateway/api_gateway_router', 'TypeScript'),
(1, 'config_loader.v2', '/config/config_loader.v2', 'Python'),
(1, 'billing_service.py', '/services/billing/billing_service.py', 'Python'),
(1, 'report_exporter.ts', '/reports/report_exporter.ts', 'TypeScript'),
(1, 'cache_client.go', '/infra/cache_client.go', 'Go'),
(1, 'notification_worker.py', '/workers/notification_worker.py', 'Python'),
(1, 'profile_validator.ts', '/profile/profile_validator.ts', 'TypeScript'),
(1, 'search_indexer.py', '/search/search_indexer.py', 'Python'),
(1, 'audit_logger.py', '/audit/audit_logger.py', 'Python'),
(1, 'session_manager.py', '/core/session_manager.py', 'Python'),
(1, 'email_template_renderer.ts', '/ui/email_template_renderer.ts', 'TypeScript'),
(1, 'inventory_sync_worker.py', '/jobs/inventory_sync_worker.py', 'Python'),
(1, 'feature_flag_client.go', '/infra/feature_flag_client.go', 'Go'),
(1, 'legacy_parser.java', '/legacy/legacy_parser.java', 'Java'),
(1, 'security_policy_engine.py', '/security/security_policy_engine.py', 'Python'),
(1, 'refund_workflow.py', '/services/payment/refund_workflow.py', 'Python'),
(1, 'analytics_aggregator.py', '/analytics/analytics_aggregator.py', 'Python'),
(1, 'token_rotation_job.kt', '/jobs/security/token_rotation_job.kt', 'Kotlin'),
(1, 'db_connector.proxy', '/infra/db_connector.proxy', 'Python'),
(1, 'checkout_orchestrator.ts', '/checkout/checkout_orchestrator.ts', 'TypeScript');

INSERT INTO dbo.MetricsDatasets (project_id, name, file_name, file_type, row_count, uploaded_by_id, status, has_label, validation_errors, metadata_json)
VALUES (1, 'defect_metrics_dataset_seed', 'defect_metrics_dataset.csv', 'csv', 500, 1, 'VALIDATED', 1, NULL, '{"source":"seed_data.sql","rows":500}');

DECLARE @i INT = 1;
DECLARE @module_id INT;
DECLARE @module_name NVARCHAR(255);
DECLARE @loc INT;
DECLARE @complexity FLOAT;
DECLARE @coupling FLOAT;
DECLARE @churn FLOAT;
DECLARE @prob FLOAT;
DECLARE @label INT;
DECLARE @risk_id INT;
DECLARE @action NVARCHAR(MAX);

WHILE @i <= 500
BEGIN
    SET @module_id = ((@i - 1) % 25) + 1;
    SELECT @module_name = module_name FROM dbo.CodeModules WHERE id = @module_id;

    SET @loc = 120 + ((@i * 37) % 620);
    SET @complexity = 5 + ((@i * 11) % 32);
    SET @coupling = 2 + ((@i * 7) % 15);
    SET @churn = 10 + ((@i * 19) % 150);

    IF @module_name IN ('auth_service.main','PaymentProcessor.py','DatabaseMigrationTask.kt','QueryEngine.cpp','StorageInterface.go','api_gateway_router','config_loader.v2')
    BEGIN
        SET @loc = @loc + 520 + ((@i * 13) % 420);
        SET @complexity = @complexity + 18 + ((@i * 5) % 18);
        SET @coupling = @coupling + 8 + ((@i * 3) % 10);
        SET @churn = @churn + 120 + ((@i * 17) % 180);
    END
    ELSE IF @i % 9 = 0
    BEGIN
        SET @loc = @loc + 260;
        SET @complexity = @complexity + 11;
        SET @coupling = @coupling + 5;
        SET @churn = @churn + 80;
    END

    SET @prob =
        (CASE WHEN @loc / 1500.0 > 1 THEN 1 ELSE @loc / 1500.0 END) * 0.25 +
        (CASE WHEN @complexity / 80.0 > 1 THEN 1 ELSE @complexity / 80.0 END) * 0.30 +
        (CASE WHEN @coupling / 35.0 > 1 THEN 1 ELSE @coupling / 35.0 END) * 0.20 +
        (CASE WHEN @churn / 420.0 > 1 THEN 1 ELSE @churn / 420.0 END) * 0.25;

    SET @prob = CASE WHEN @prob > 0.98 THEN 0.98 WHEN @prob < 0.02 THEN 0.02 ELSE @prob END;
    SET @label = CASE WHEN @prob >= 0.50 THEN 1 ELSE 0 END;

    INSERT INTO dbo.MetricRecords (dataset_id, project_id, module_id, module_name, loc, complexity, coupling, code_churn, defect_label, recorded_at)
    VALUES (1, 1, @module_id, @module_name, @loc, @complexity, @coupling, @churn, @label, DATEADD(DAY, -(@i % 30), GETDATE()));

    SET @risk_id = CASE WHEN @prob < 0.30 THEN 1 WHEN @prob < 0.60 THEN 2 WHEN @prob < 0.80 THEN 3 ELSE 4 END;
    SELECT @action = suggested_action FROM dbo.RiskLevels WHERE id = @risk_id;

    INSERT INTO dbo.Predictions (project_id, dataset_id, model_id, module_name, loc, complexity, coupling, code_churn, defect_probability, prediction, risk_level_id, suggested_action, created_at)
    VALUES (1, 1, NULL, @module_name, @loc, @complexity, @coupling, @churn, @prob, @label, @risk_id, @action, DATEADD(DAY, -(@i % 30), GETDATE()));

    SET @i = @i + 1;
END

INSERT INTO dbo.MLModels (name, model_type, version, artifact_path, is_active, accuracy, precision, recall, f1_score, roc_auc, latency_ms, hyperparameters_json)
VALUES
('Logistic Regression', 'logistic_regression', 'seed-v1', 'app/ml/artifacts/logistic_regression_seed.joblib', 0, 0.86, 0.82, 0.80, 0.81, 0.90, 3.2, '{"seed":true}'),
('Random Forest', 'random_forest', 'seed-v1', 'app/ml/artifacts/random_forest_seed.joblib', 1, 0.93, 0.91, 0.89, 0.90, 0.96, 8.4, '{"seed":true}'),
('Neural Networks', 'neural_network', 'seed-v1', 'app/ml/artifacts/neural_network_seed.joblib', 0, 0.90, 0.88, 0.86, 0.87, 0.94, 14.1, '{"seed":true}');

UPDATE dbo.Predictions SET model_id = 2;

INSERT INTO dbo.ProjectState (project_id, current_dataset_id, current_model_id, current_analysis_dataset_id)
VALUES (1, 1, 2, 1);

INSERT INTO dbo.TrainingRuns (model_id, dataset_id, model_type, model_version, status, train_size, test_size, accuracy, precision, recall, f1_score, roc_auc, confusion_matrix_json, training_time_seconds, parameters_json, started_at, completed_at)
VALUES
(1, 1, 'logistic_regression', 'seed-v1', 'completed', 400, 100, 0.86, 0.82, 0.80, 0.81, 0.90, '[[52,8],[6,34]]', 1.42, '{"test_size":0.2}', DATEADD(DAY,-3,GETDATE()), DATEADD(DAY,-3,GETDATE())),
(2, 1, 'random_forest', 'seed-v1', 'completed', 400, 100, 0.93, 0.91, 0.89, 0.90, 0.96, '[[57,3],[4,36]]', 3.90, '{"test_size":0.2,"n_estimators":240}', DATEADD(DAY,-2,GETDATE()), DATEADD(DAY,-2,GETDATE())),
(3, 1, 'neural_network', 'seed-v1', 'completed', 400, 100, 0.90, 0.88, 0.86, 0.87, 0.94, '[[55,5],[5,35]]', 5.20, '{"test_size":0.2,"hidden_layer_size":64}', DATEADD(DAY,-1,GETDATE()), DATEADD(DAY,-1,GETDATE()));

INSERT INTO dbo.Reports (project_id, generated_by_id, title, filters_json, summary_json, file_path)
VALUES
(1, 1, 'Seed Defect Risk Analysis', '{"days":30}', '{"prediction_rows":500,"risk_counts":{"LOW":120,"MEDIUM":210,"HIGH":115,"CRITICAL":55}}', NULL),
(1, 1, 'Critical Modules QA Report', '{"risk_level":"CRITICAL"}', '{"focus":"critical modules","recommended_action":"Immediate QA inspection"}', NULL);

INSERT INTO dbo.AuditLogs (user_id, project_id, action, entity_type, entity_id, details_json, ip_address)
VALUES
(1, 1, 'seed.executed', 'Database', 1, '{"source":"seed_data.sql"}', '127.0.0.1'),
(1, 1, 'ml.training.completed', 'MLModel', 2, '{"best_model":"Random Forest"}', '127.0.0.1'),
(1, 1, 'prediction.batch', 'Prediction', NULL, '{"rows":500}', '127.0.0.1'),
(1, 1, 'report.generated', 'Report', 1, '{"title":"Seed Defect Risk Analysis"}', '127.0.0.1');
GO
