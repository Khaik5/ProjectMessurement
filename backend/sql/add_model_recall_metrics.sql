IF COL_LENGTH('dbo.MLModels', 'pr_auc') IS NULL
    ALTER TABLE dbo.MLModels ADD pr_auc FLOAT NULL;
IF COL_LENGTH('dbo.MLModels', 'threshold') IS NULL
    ALTER TABLE dbo.MLModels ADD threshold FLOAT NULL;
IF COL_LENGTH('dbo.MLModels', 'selection_strategy') IS NULL
    ALTER TABLE dbo.MLModels ADD selection_strategy NVARCHAR(50) NULL;
IF COL_LENGTH('dbo.MLModels', 'selection_score') IS NULL
    ALTER TABLE dbo.MLModels ADD selection_score FLOAT NULL;

IF COL_LENGTH('dbo.TrainingRuns', 'pr_auc') IS NULL
    ALTER TABLE dbo.TrainingRuns ADD pr_auc FLOAT NULL;
IF COL_LENGTH('dbo.TrainingRuns', 'threshold') IS NULL
    ALTER TABLE dbo.TrainingRuns ADD threshold FLOAT NULL;
IF COL_LENGTH('dbo.TrainingRuns', 'selection_strategy') IS NULL
    ALTER TABLE dbo.TrainingRuns ADD selection_strategy NVARCHAR(50) NULL;
IF COL_LENGTH('dbo.TrainingRuns', 'selection_score') IS NULL
    ALTER TABLE dbo.TrainingRuns ADD selection_score FLOAT NULL;
