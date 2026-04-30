IF DB_ID(N'DefectAI_P7_DB') IS NULL
BEGIN
    CREATE DATABASE DefectAI_P7_DB;
END
GO

USE DefectAI_P7_DB;
GO

IF OBJECT_ID(N'dbo.Users', N'U') IS NULL
CREATE TABLE dbo.Users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    username NVARCHAR(100) NOT NULL UNIQUE,
    email NVARCHAR(255) NOT NULL UNIQUE,
    password_hash NVARCHAR(255) NOT NULL,
    role NVARCHAR(50) NOT NULL,
    is_active BIT NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT GETDATE()
);

IF OBJECT_ID(N'dbo.RiskLevels', N'U') IS NULL
CREATE TABLE dbo.RiskLevels (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(50) NOT NULL UNIQUE,
    min_probability FLOAT NOT NULL,
    max_probability FLOAT NOT NULL,
    color NVARCHAR(50) NOT NULL,
    suggested_action NVARCHAR(MAX) NOT NULL
);

IF OBJECT_ID(N'dbo.Projects', N'U') IS NULL
CREATE TABLE dbo.Projects (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    description NVARCHAR(MAX) NULL,
    owner_id INT NULL,
    is_active BIT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_Projects_Users FOREIGN KEY (owner_id) REFERENCES dbo.Users(id)
);

IF OBJECT_ID(N'dbo.CodeModules', N'U') IS NULL
CREATE TABLE dbo.CodeModules (
    id INT IDENTITY(1,1) PRIMARY KEY,
    project_id INT NOT NULL,
    module_name NVARCHAR(255) NOT NULL,
    module_path NVARCHAR(500) NULL,
    language NVARCHAR(50) NULL,
    created_at DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_CodeModules_Projects FOREIGN KEY (project_id) REFERENCES dbo.Projects(id)
);

IF OBJECT_ID(N'dbo.ProjectState', N'U') IS NULL
CREATE TABLE dbo.ProjectState (
    id INT IDENTITY(1,1) PRIMARY KEY,
    project_id INT NOT NULL UNIQUE,
    current_dataset_id INT NULL,
    current_model_id INT NULL,
    current_analysis_dataset_id INT NULL,
    updated_at DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_ProjectState_Projects FOREIGN KEY (project_id) REFERENCES dbo.Projects(id)
);

IF OBJECT_ID(N'dbo.MetricsDatasets', N'U') IS NULL
CREATE TABLE dbo.MetricsDatasets (
    id INT IDENTITY(1,1) PRIMARY KEY,
    project_id INT NOT NULL,
    name NVARCHAR(255) NOT NULL,
    file_name NVARCHAR(255) NOT NULL,
    file_type NVARCHAR(50) NOT NULL,
    row_count INT NOT NULL DEFAULT 0,
    uploaded_by_id INT NULL,
    status NVARCHAR(50) NOT NULL DEFAULT 'UPLOADED',
    validation_errors NVARCHAR(MAX) NULL,
    metadata_json NVARCHAR(MAX) NULL,
    has_label BIT NOT NULL DEFAULT 0,
    analysis_started_at DATETIME NULL,
    analysis_completed_at DATETIME NULL,
    uploaded_at DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_MetricsDatasets_Projects FOREIGN KEY (project_id) REFERENCES dbo.Projects(id),
    CONSTRAINT FK_MetricsDatasets_Users FOREIGN KEY (uploaded_by_id) REFERENCES dbo.Users(id)
);

IF OBJECT_ID(N'dbo.MetricRecords', N'U') IS NULL
CREATE TABLE dbo.MetricRecords (
    id INT IDENTITY(1,1) PRIMARY KEY,
    dataset_id INT NOT NULL,
    project_id INT NOT NULL,
    module_id INT NULL,
    module_name NVARCHAR(255) NOT NULL,
    loc INT NOT NULL,
    ncloc INT NULL,
    cloc INT NULL,
    complexity FLOAT NOT NULL,
    cyclomatic_complexity FLOAT NULL,
    depth_of_nesting FLOAT NULL,
    coupling FLOAT NOT NULL,
    cohesion FLOAT NULL,
    information_flow_complexity FLOAT NULL,
    code_churn FLOAT NOT NULL,
    change_request_backlog FLOAT NULL,
    pending_effort_hours FLOAT NULL,
    percent_reused FLOAT NULL,
    defect_count FLOAT NULL,
    defect_label INT NULL,
    kloc FLOAT NULL,
    comment_ratio FLOAT NULL,
    defect_density FLOAT NULL,
    size_score FLOAT NULL,
    complexity_score FLOAT NULL,
    coupling_score FLOAT NULL,
    churn_score FLOAT NULL,
    defect_density_score FLOAT NULL,
    cohesion_score FLOAT NULL,
    reuse_score FLOAT NULL,
    risk_score FLOAT NULL,
    recorded_at DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_MetricRecords_Datasets FOREIGN KEY (dataset_id) REFERENCES dbo.MetricsDatasets(id),
    CONSTRAINT FK_MetricRecords_Projects FOREIGN KEY (project_id) REFERENCES dbo.Projects(id),
    CONSTRAINT FK_MetricRecords_Modules FOREIGN KEY (module_id) REFERENCES dbo.CodeModules(id)
);

IF OBJECT_ID(N'dbo.MLModels', N'U') IS NULL
CREATE TABLE dbo.MLModels (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    model_type NVARCHAR(100) NOT NULL,
    version NVARCHAR(50) NOT NULL,
    artifact_path NVARCHAR(500) NOT NULL,
    is_active BIT NOT NULL DEFAULT 0,
    accuracy FLOAT NULL,
    precision FLOAT NULL,
    recall FLOAT NULL,
    f1_score FLOAT NULL,
    roc_auc FLOAT NULL,
    latency_ms FLOAT NULL,
    hyperparameters_json NVARCHAR(MAX) NULL,
    feature_list_json NVARCHAR(MAX) NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    deleted_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT GETDATE()
);

IF OBJECT_ID(N'dbo.TrainingRuns', N'U') IS NULL
CREATE TABLE dbo.TrainingRuns (
    id INT IDENTITY(1,1) PRIMARY KEY,
    model_id INT NULL,
    dataset_id INT NULL,
    model_type NVARCHAR(100) NOT NULL,
    model_version NVARCHAR(50) NOT NULL,
    status NVARCHAR(50) NOT NULL,
    train_size INT NOT NULL,
    test_size INT NOT NULL,
    accuracy FLOAT NULL,
    precision FLOAT NULL,
    recall FLOAT NULL,
    f1_score FLOAT NULL,
    roc_auc FLOAT NULL,
    confusion_matrix_json NVARCHAR(MAX) NULL,
    training_time_seconds FLOAT NULL,
    parameters_json NVARCHAR(MAX) NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    deleted_at DATETIME NULL,
    started_at DATETIME NOT NULL DEFAULT GETDATE(),
    completed_at DATETIME NULL,
    CONSTRAINT FK_TrainingRuns_MLModels FOREIGN KEY (model_id) REFERENCES dbo.MLModels(id),
    CONSTRAINT FK_TrainingRuns_Datasets FOREIGN KEY (dataset_id) REFERENCES dbo.MetricsDatasets(id)
);

IF OBJECT_ID(N'dbo.Predictions', N'U') IS NULL
CREATE TABLE dbo.Predictions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    project_id INT NOT NULL,
    dataset_id INT NULL,
    model_id INT NULL,
    module_name NVARCHAR(255) NOT NULL,
    loc INT NOT NULL,
    complexity FLOAT NOT NULL,
    coupling FLOAT NOT NULL,
    code_churn FLOAT NOT NULL,
    defect_probability FLOAT NOT NULL,
    prediction INT NOT NULL,
    prediction_label NVARCHAR(50) NULL,
    risk_score FLOAT NULL,
    defect_density FLOAT NULL,
    size_score FLOAT NULL,
    complexity_score FLOAT NULL,
    coupling_score FLOAT NULL,
    churn_score FLOAT NULL,
    risk_level_id INT NOT NULL,
    suggested_action NVARCHAR(MAX) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_Predictions_Projects FOREIGN KEY (project_id) REFERENCES dbo.Projects(id),
    CONSTRAINT FK_Predictions_Datasets FOREIGN KEY (dataset_id) REFERENCES dbo.MetricsDatasets(id),
    CONSTRAINT FK_Predictions_MLModels FOREIGN KEY (model_id) REFERENCES dbo.MLModels(id),
    CONSTRAINT FK_Predictions_RiskLevels FOREIGN KEY (risk_level_id) REFERENCES dbo.RiskLevels(id)
);

IF OBJECT_ID(N'dbo.Reports', N'U') IS NULL
CREATE TABLE dbo.Reports (
    id INT IDENTITY(1,1) PRIMARY KEY,
    project_id INT NOT NULL,
    generated_by_id INT NULL,
    title NVARCHAR(255) NOT NULL,
    filters_json NVARCHAR(MAX) NULL,
    summary_json NVARCHAR(MAX) NULL,
    file_path NVARCHAR(500) NULL,
    created_at DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_Reports_Projects FOREIGN KEY (project_id) REFERENCES dbo.Projects(id),
    CONSTRAINT FK_Reports_Users FOREIGN KEY (generated_by_id) REFERENCES dbo.Users(id)
);

IF OBJECT_ID(N'dbo.AuditLogs', N'U') IS NULL
CREATE TABLE dbo.AuditLogs (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NULL,
    project_id INT NULL,
    action NVARCHAR(255) NOT NULL,
    entity_type NVARCHAR(100) NULL,
    entity_id INT NULL,
    details_json NVARCHAR(MAX) NULL,
    ip_address NVARCHAR(100) NULL,
    created_at DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_AuditLogs_Users FOREIGN KEY (user_id) REFERENCES dbo.Users(id),
    CONSTRAINT FK_AuditLogs_Projects FOREIGN KEY (project_id) REFERENCES dbo.Projects(id)
);
GO
