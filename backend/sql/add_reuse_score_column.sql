-- Add missing reuse_score column to MetricRecords table
USE DefectAI_P7_DB;
GO

-- Check if column exists, if not add it
IF NOT EXISTS (
    SELECT 1 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'MetricRecords' 
    AND COLUMN_NAME = 'reuse_score'
)
BEGIN
    ALTER TABLE dbo.MetricRecords
    ADD reuse_score FLOAT NULL;
    
    PRINT 'Column reuse_score added successfully';
END
ELSE
BEGIN
    PRINT 'Column reuse_score already exists';
END
GO
