"""
Check database schema for MetricRecords table
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import fetch_all

def main():
    print("🔍 Checking MetricRecords table schema...")
    
    try:
        # Get column information
        columns = fetch_all("""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'MetricRecords'
            ORDER BY ORDINAL_POSITION
        """)
        
        print(f"\n✅ Found {len(columns)} columns in MetricRecords table:\n")
        
        for col in columns:
            print(f"   - {col['COLUMN_NAME']:<30} {col['DATA_TYPE']:<15} {'NULL' if col['IS_NULLABLE'] == 'YES' else 'NOT NULL'}")
        
        # Check if reuse_score exists
        reuse_score_exists = any(col['COLUMN_NAME'] == 'reuse_score' for col in columns)
        
        if reuse_score_exists:
            print("\n✅ Column 'reuse_score' EXISTS")
        else:
            print("\n❌ Column 'reuse_score' MISSING!")
            print("   Run: backend/sql/create_database.sql to update schema")
        
        # Check sample data
        print("\n🔍 Checking sample data...")
        sample = fetch_all("SELECT TOP 1 * FROM MetricRecords")
        
        if sample:
            print(f"✅ Found {len(sample)} record(s)")
            print(f"   Columns in data: {list(sample[0].keys())}")
        else:
            print("⚠️  No data in MetricRecords table")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
