USE DefectAI_P7_DB;
GO

/* ==================================================
   DefectAI P7 - Schema update (non-destructive)
   - Add missing columns for current dataset/model state
   - Add dataset lifecycle fields
   - Add prediction enrichment fields
   - Add soft-delete for TrainingRuns and MLModels
   ================================================== */

/* 1) Projects: current dataset/model pointers (requested) */
IF COL_LENGTH('dbo.Projects', 'current_dataset_id') IS NULL
    ALTER TABLE dbo.Projects ADD current_dataset_id INT NULL;
IF COL_LENGTH('dbo.Projects', 'current_analysis_dataset_id') IS NULL
    ALTER TABLE dbo.Projects ADD current_analysis_dataset_id INT NULL;
IF COL_LENGTH('dbo.Projects', 'current_model_id') IS NULL
    ALTER TABLE dbo.Projects ADD current_model_id INT NULL;
GO

/* 2) MetricsDatasets: status + flags + analysis timestamps */
IF COL_LENGTH('dbo.MetricsDatasets', 'status') IS NULL
    ALTER TABLE dbo.MetricsDatasets ADD status NVARCHAR(50) NOT NULL CONSTRAINT DF_MetricsDatasets_status DEFAULT 'UPLOADED';
ELSE
BEGIN
    /* Normalize legacy lowercase values to uppercase (idempotent) */
    UPDATE dbo.MetricsDatasets
    SET status = UPPER(status)
    WHERE status IS NOT NULL AND status <> UPPER(status);
END

IF COL_LENGTH('dbo.MetricsDatasets', 'has_label') IS NULL
    ALTER TABLE dbo.MetricsDatasets ADD has_label BIT NOT NULL CONSTRAINT DF_MetricsDatasets_has_label DEFAULT 0;

IF COL_LENGTH('dbo.MetricsDatasets', 'analysis_started_at') IS NULL
    ALTER TABLE dbo.MetricsDatasets ADD analysis_started_at DATETIME NULL;
IF COL_LENGTH('dbo.MetricsDatasets', 'analysis_completed_at') IS NULL
    ALTER TABLE dbo.MetricsDatasets ADD analysis_completed_at DATETIME NULL;
GO

/* 3) Predictions: richer outputs for dashboard/history/export */
IF COL_LENGTH('dbo.Predictions', 'prediction_label') IS NULL
    ALTER TABLE dbo.Predictions ADD prediction_label NVARCHAR(50) NULL;
IF COL_LENGTH('dbo.Predictions', 'risk_score') IS NULL
    ALTER TABLE dbo.Predictions ADD risk_score FLOAT NULL;

IF COL_LENGTH('dbo.Predictions', 'defect_density') IS NULL
    ALTER TABLE dbo.Predictions ADD defect_density FLOAT NULL;
IF COL_LENGTH('dbo.Predictions', 'size_score') IS NULL
    ALTER TABLE dbo.Predictions ADD size_score FLOAT NULL;
IF COL_LENGTH('dbo.Predictions', 'complexity_score') IS NULL
    ALTER TABLE dbo.Predictions ADD complexity_score FLOAT NULL;
IF COL_LENGTH('dbo.Predictions', 'coupling_score') IS NULL
    ALTER TABLE dbo.Predictions ADD coupling_score FLOAT NULL;
IF COL_LENGTH('dbo.Predictions', 'churn_score') IS NULL
    ALTER TABLE dbo.Predictions ADD churn_score FLOAT NULL;
GO

/* 4) TrainingRuns: soft delete */
IF COL_LENGTH('dbo.TrainingRuns', 'is_deleted') IS NULL
    ALTER TABLE dbo.TrainingRuns ADD is_deleted BIT NOT NULL CONSTRAINT DF_TrainingRuns_is_deleted DEFAULT 0;
IF COL_LENGTH('dbo.TrainingRuns', 'deleted_at') IS NULL
    ALTER TABLE dbo.TrainingRuns ADD deleted_at DATETIME NULL;
GO

/* 5) MLModels: soft delete */
IF COL_LENGTH('dbo.MLModels', 'is_deleted') IS NULL
    ALTER TABLE dbo.MLModels ADD is_deleted BIT NOT NULL CONSTRAINT DF_MLModels_is_deleted DEFAULT 0;
IF COL_LENGTH('dbo.MLModels', 'deleted_at') IS NULL
    ALTER TABLE dbo.MLModels ADD deleted_at DATETIME NULL;
IF COL_LENGTH('dbo.MLModels', 'feature_list_json') IS NULL
    ALTER TABLE dbo.MLModels ADD feature_list_json NVARCHAR(MAX) NULL;
GO

/* 6) MetricRecords: add optional metrics columns used for measurement + ML features */
IF COL_LENGTH('dbo.MetricRecords', 'ncloc') IS NULL
    ALTER TABLE dbo.MetricRecords ADD ncloc INT NULL;
IF COL_LENGTH('dbo.MetricRecords', 'cloc') IS NULL
    ALTER TABLE dbo.MetricRecords ADD cloc INT NULL;
IF COL_LENGTH('dbo.MetricRecords', 'cyclomatic_complexity') IS NULL
    ALTER TABLE dbo.MetricRecords ADD cyclomatic_complexity FLOAT NULL;
IF COL_LENGTH('dbo.MetricRecords', 'depth_of_nesting') IS NULL
    ALTER TABLE dbo.MetricRecords ADD depth_of_nesting FLOAT NULL;
IF COL_LENGTH('dbo.MetricRecords', 'cohesion') IS NULL
    ALTER TABLE dbo.MetricRecords ADD cohesion FLOAT NULL;
IF COL_LENGTH('dbo.MetricRecords', 'information_flow_complexity') IS NULL
    ALTER TABLE dbo.MetricRecords ADD information_flow_complexity FLOAT NULL;
IF COL_LENGTH('dbo.MetricRecords', 'change_request_backlog') IS NULL
    ALTER TABLE dbo.MetricRecords ADD change_request_backlog FLOAT NULL;
IF COL_LENGTH('dbo.MetricRecords', 'pending_effort_hours') IS NULL
    ALTER TABLE dbo.MetricRecords ADD pending_effort_hours FLOAT NULL;
IF COL_LENGTH('dbo.MetricRecords', 'percent_reused') IS NULL
    ALTER TABLE dbo.MetricRecords ADD percent_reused FLOAT NULL;
IF COL_LENGTH('dbo.MetricRecords', 'defect_count') IS NULL
    ALTER TABLE dbo.MetricRecords ADD defect_count FLOAT NULL;

IF COL_LENGTH('dbo.MetricRecords', 'kloc') IS NULL
    ALTER TABLE dbo.MetricRecords ADD kloc FLOAT NULL;
IF COL_LENGTH('dbo.MetricRecords', 'comment_ratio') IS NULL
    ALTER TABLE dbo.MetricRecords ADD comment_ratio FLOAT NULL;
IF COL_LENGTH('dbo.MetricRecords', 'defect_density') IS NULL
    ALTER TABLE dbo.MetricRecords ADD defect_density FLOAT NULL;

IF COL_LENGTH('dbo.MetricRecords', 'size_score') IS NULL
    ALTER TABLE dbo.MetricRecords ADD size_score FLOAT NULL;
IF COL_LENGTH('dbo.MetricRecords', 'complexity_score') IS NULL
    ALTER TABLE dbo.MetricRecords ADD complexity_score FLOAT NULL;
IF COL_LENGTH('dbo.MetricRecords', 'coupling_score') IS NULL
    ALTER TABLE dbo.MetricRecords ADD coupling_score FLOAT NULL;
IF COL_LENGTH('dbo.MetricRecords', 'churn_score') IS NULL
    ALTER TABLE dbo.MetricRecords ADD churn_score FLOAT NULL;
IF COL_LENGTH('dbo.MetricRecords', 'defect_density_score') IS NULL
    ALTER TABLE dbo.MetricRecords ADD defect_density_score FLOAT NULL;
IF COL_LENGTH('dbo.MetricRecords', 'cohesion_score') IS NULL
    ALTER TABLE dbo.MetricRecords ADD cohesion_score FLOAT NULL;
IF COL_LENGTH('dbo.MetricRecords', 'reuse_score') IS NULL
    ALTER TABLE dbo.MetricRecords ADD reuse_score FLOAT NULL;
IF COL_LENGTH('dbo.MetricRecords', 'risk_score') IS NULL
    ALTER TABLE dbo.MetricRecords ADD risk_score FLOAT NULL;
GO

/* Optional: keep ProjectState in sync with Projects pointers (best-effort, non-breaking) */
IF OBJECT_ID(N'dbo.ProjectState', N'U') IS NOT NULL
BEGIN
    UPDATE p
    SET
        p.current_dataset_id = ps.current_dataset_id,
        p.current_analysis_dataset_id = ps.current_analysis_dataset_id,
        p.current_model_id = ps.current_model_id
    FROM dbo.Projects p
    JOIN dbo.ProjectState ps ON ps.project_id = p.id
    WHERE
        (p.current_dataset_id IS NULL AND ps.current_dataset_id IS NOT NULL)
        OR (p.current_analysis_dataset_id IS NULL AND ps.current_analysis_dataset_id IS NOT NULL)
        OR (p.current_model_id IS NULL AND ps.current_model_id IS NOT NULL);
END
GO
