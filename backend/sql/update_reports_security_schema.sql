USE DefectAI_P7_DB;
GO

IF COL_LENGTH('dbo.Reports', 'IsDeleted') IS NULL
    ALTER TABLE dbo.Reports ADD IsDeleted BIT NOT NULL CONSTRAINT DF_Reports_IsDeleted DEFAULT 0;
GO

IF COL_LENGTH('dbo.Reports', 'DeletedAt') IS NULL
    ALTER TABLE dbo.Reports ADD DeletedAt DATETIME NULL;
GO

IF COL_LENGTH('dbo.Reports', 'DeletedBy') IS NULL
    ALTER TABLE dbo.Reports ADD DeletedBy INT NULL;
GO
