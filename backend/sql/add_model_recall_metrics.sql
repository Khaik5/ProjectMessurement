IF COL_LENGTH('dbo.MLModels', 'pr_auc') IS NULL
    ALTER TABLE dbo.MLModels ADD pr_auc FLOAT NULL;
IF COL_LENGTH('dbo.MLModels', 'dataset_id') IS NULL
    ALTER TABLE dbo.MLModels ADD dataset_id INT NULL;
IF COL_LENGTH('dbo.MLModels', 'training_profile') IS NULL
    ALTER TABLE dbo.MLModels ADD training_profile NVARCHAR(80) NULL;
IF COL_LENGTH('dbo.MLModels', 'metadata_path') IS NULL
    ALTER TABLE dbo.MLModels ADD metadata_path NVARCHAR(500) NULL;
IF COL_LENGTH('dbo.MLModels', 'metrics_json') IS NULL
    ALTER TABLE dbo.MLModels ADD metrics_json NVARCHAR(MAX) NULL;
IF COL_LENGTH('dbo.MLModels', 'is_best') IS NULL
    ALTER TABLE dbo.MLModels ADD is_best BIT NOT NULL DEFAULT 0;
IF COL_LENGTH('dbo.MLModels', 'status') IS NULL
    ALTER TABLE dbo.MLModels ADD status NVARCHAR(30) NULL;
IF COL_LENGTH('dbo.MLModels', 'error_message') IS NULL
    ALTER TABLE dbo.MLModels ADD error_message NVARCHAR(MAX) NULL;
IF COL_LENGTH('dbo.MLModels', 'updated_at') IS NULL
    ALTER TABLE dbo.MLModels ADD updated_at DATETIME NULL;
IF COL_LENGTH('dbo.MLModels', 'threshold') IS NULL
    ALTER TABLE dbo.MLModels ADD threshold FLOAT NULL;
IF COL_LENGTH('dbo.MLModels', 'selection_strategy') IS NULL
    ALTER TABLE dbo.MLModels ADD selection_strategy NVARCHAR(50) NULL;
IF COL_LENGTH('dbo.MLModels', 'selection_score') IS NULL
    ALTER TABLE dbo.MLModels ADD selection_score FLOAT NULL;

IF COL_LENGTH('dbo.TrainingRuns', 'pr_auc') IS NULL
    ALTER TABLE dbo.TrainingRuns ADD pr_auc FLOAT NULL;
IF COL_LENGTH('dbo.TrainingRuns', 'selected_models_json') IS NULL
    ALTER TABLE dbo.TrainingRuns ADD selected_models_json NVARCHAR(MAX) NULL;
IF COL_LENGTH('dbo.TrainingRuns', 'training_profile') IS NULL
    ALTER TABLE dbo.TrainingRuns ADD training_profile NVARCHAR(80) NULL;
IF COL_LENGTH('dbo.TrainingRuns', 'threshold_config_json') IS NULL
    ALTER TABLE dbo.TrainingRuns ADD threshold_config_json NVARCHAR(MAX) NULL;
IF COL_LENGTH('dbo.TrainingRuns', 'best_model_id') IS NULL
    ALTER TABLE dbo.TrainingRuns ADD best_model_id INT NULL;
IF COL_LENGTH('dbo.TrainingRuns', 'results_json') IS NULL
    ALTER TABLE dbo.TrainingRuns ADD results_json NVARCHAR(MAX) NULL;
IF COL_LENGTH('dbo.TrainingRuns', 'error_message') IS NULL
    ALTER TABLE dbo.TrainingRuns ADD error_message NVARCHAR(MAX) NULL;
IF COL_LENGTH('dbo.TrainingRuns', 'threshold') IS NULL
    ALTER TABLE dbo.TrainingRuns ADD threshold FLOAT NULL;
IF COL_LENGTH('dbo.TrainingRuns', 'selection_strategy') IS NULL
    ALTER TABLE dbo.TrainingRuns ADD selection_strategy NVARCHAR(50) NULL;
IF COL_LENGTH('dbo.TrainingRuns', 'selection_score') IS NULL
    ALTER TABLE dbo.TrainingRuns ADD selection_score FLOAT NULL;
