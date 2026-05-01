-- Add missing feature_list_json column to MLModels table
USE DefectAI_P7_DB;
GO

-- Check if column exists, if not add it
IF NOT EXISTS (
    SELECT 1 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'MLModels' 
    AND COLUMN_NAME = 'feature_list_json'
)
BEGIN
    ALTER TABLE dbo.MLModels
    ADD feature_list_json NVARCHAR(MAX) NULL;
    
    PRINT 'Column feature_list_json added successfully';
END
ELSE
BEGIN
    PRINT 'Column feature_list_json already exists';
END
GO
