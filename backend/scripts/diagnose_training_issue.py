"""
Script để chẩn đoán vấn đề training với các datasets khác nhau
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import fetch_all
from app.ml.feature_engineering import build_p7_features
import pandas as pd

def main():
    print("🔍 CHẨN ĐOÁN VẤN ĐỀ TRAINING\n")
    print("="*80)
    
    # Lấy tất cả datasets
    datasets = fetch_all("""
        SELECT id, name, file_name, row_count, has_label, status
        FROM MetricsDatasets
        ORDER BY id
    """)
    
    print(f"\n📊 Tìm thấy {len(datasets)} datasets:\n")
    
    for ds in datasets:
        print(f"\n{'='*80}")
        print(f"Dataset #{ds['id']}: {ds['name']}")
        print(f"   File: {ds['file_name']}")
        print(f"   Rows: {ds['row_count']}")
        print(f"   Has Label: {ds['has_label']}")
        print(f"   Status: {ds['status']}")
        
        # Kiểm tra dữ liệu thực tế
        try:
            records = fetch_all("""
                SELECT 
                    module_name,
                    loc, ncloc, cloc,
                    complexity, cyclomatic_complexity, depth_of_nesting,
                    coupling, cohesion, information_flow_complexity,
                    code_churn, change_request_backlog, pending_effort_hours, percent_reused,
                    defect_count,
                    size_score, complexity_score, coupling_score, churn_score,
                    defect_density, kloc, comment_ratio, cohesion_score, reuse_score, risk_score,
                    defect_label
                FROM MetricRecords
                WHERE project_id = 1 AND dataset_id = ? AND defect_label IS NOT NULL
            """, [ds['id']])
            
            print(f"\n   ✅ Records với defect_label: {len(records)}")
            
            if len(records) == 0:
                print(f"   ❌ KHÔNG CÓ DỮ LIỆU với defect_label!")
                print(f"   → Dataset này KHÔNG THỂ train được")
                continue
            
            if len(records) < 20:
                print(f"   ⚠️  CHỈ CÓ {len(records)} records (cần tối thiểu 20)")
                print(f"   → Dataset này KHÔNG ĐỦ dữ liệu để train")
                continue
            
            # Kiểm tra defect_label distribution
            df = pd.DataFrame(records)
            label_counts = df['defect_label'].value_counts()
            
            print(f"\n   📈 Phân bố defect_label:")
            for label, count in label_counts.items():
                print(f"      - Label {label}: {count} records ({count/len(records)*100:.1f}%)")
            
            if df['defect_label'].nunique() < 2:
                print(f"   ❌ CHỈ CÓ 1 LOẠI LABEL!")
                print(f"   → Cần có cả 0 (No Defect) và 1 (Defect)")
                continue
            
            # Kiểm tra P7 features
            print(f"\n   🔧 Kiểm tra P7 features...")
            try:
                df_features = build_p7_features(df, use_label_density=False)
                print(f"   ✅ P7 features OK: {len(df_features.columns)} columns")
                
                # Kiểm tra missing values
                missing = df_features.isnull().sum()
                if missing.sum() > 0:
                    print(f"   ⚠️  Có {missing.sum()} missing values")
                    print(f"      (Sẽ được xử lý bởi SimpleImputer)")
                
                print(f"\n   ✅ Dataset #{ds['id']} CÓ THỂ TRAIN ĐƯỢC!")
                print(f"      - {len(records)} records")
                print(f"      - {label_counts[0]} No Defect, {label_counts[1]} Defect")
                print(f"      - Tất cả P7 features đầy đủ")
                
            except Exception as e:
                print(f"   ❌ LỖI khi build P7 features: {str(e)}")
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            print(f"   ❌ LỖI khi query data: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*80}")
    print("\n📋 TÓM TẮT:")
    print("   - Datasets có thể train: Kiểm tra các dataset có ✅ ở trên")
    print("   - Nếu dataset không train được, cần upload lại với defect_label")
    print("\n")

if __name__ == "__main__":
    main()
