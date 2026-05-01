"""
Script để đồng bộ file artifacts với database
Sử dụng khi có file .joblib nhưng không có data trong SQL
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.permission_database import fetch_all, execute_query

# Define artifact paths
ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "app" / "ml" / "artifacts"
PRODUCTION_ARTIFACT = ARTIFACT_DIR / "defectai_p7_production.joblib"
PRODUCTION_METADATA = ARTIFACT_DIR / "defectai_p7_production_metadata.json"


def check_artifacts():
    """Kiểm tra file artifacts có tồn tại không"""
    print("🔍 Checking artifacts...")
    print(f"   Artifact directory: {ARTIFACT_DIR}")
    print(f"   Production model: {PRODUCTION_ARTIFACT}")
    print(f"   Metadata: {PRODUCTION_METADATA}")
    
    if PRODUCTION_ARTIFACT.exists():
        print(f"   ✅ Production artifact exists: {PRODUCTION_ARTIFACT}")
        size_mb = PRODUCTION_ARTIFACT.stat().st_size / (1024 * 1024)
        print(f"      Size: {size_mb:.2f} MB")
    else:
        print(f"   ❌ Production artifact NOT found")
    
    if PRODUCTION_METADATA.exists():
        print(f"   ✅ Metadata exists: {PRODUCTION_METADATA}")
        import json
        metadata = json.loads(PRODUCTION_METADATA.read_text())
        print(f"      Version: {metadata.get('version')}")
        print(f"      Model type: {metadata.get('best_model_type')}")
    else:
        print(f"   ❌ Metadata NOT found")
    
    print()


def check_database():
    """Kiểm tra database có models không"""
    print("🔍 Checking database...")
    
    try:
        models = fetch_all("SELECT * FROM MLModels WHERE ISNULL(is_deleted,0)=0")
        print(f"   Total models in database: {len(models)}")
        
        if models:
            for model in models:
                print(f"   - Model #{model['id']}: {model['name']}")
                print(f"     Type: {model['model_type']}, Version: {model['version']}")
                print(f"     Active: {bool(model['is_active'])}")
                print(f"     Accuracy: {model.get('accuracy', 0):.2%}")
        else:
            print("   ❌ No models found in database")
        
        print()
        
        runs = fetch_all("SELECT * FROM TrainingRuns WHERE ISNULL(is_deleted,0)=0")
        print(f"   Total training runs in database: {len(runs)}")
        
        if runs:
            for run in runs[:5]:  # Show first 5
                print(f"   - Run #{run['id']}: {run['model_type']}")
                print(f"     F1-Score: {run.get('f1_score', 0):.2%}")
        else:
            print("   ❌ No training runs found in database")
        
        print()
        
    except Exception as e:
        print(f"   ❌ Error checking database: {e}")
        print()


def clear_artifacts():
    """Xóa file artifacts cũ"""
    print("🗑️  Clearing old artifacts...")
    
    if PRODUCTION_ARTIFACT.exists():
        PRODUCTION_ARTIFACT.unlink()
        print(f"   ✅ Deleted: {PRODUCTION_ARTIFACT}")
    
    if PRODUCTION_METADATA.exists():
        PRODUCTION_METADATA.unlink()
        print(f"   ✅ Deleted: {PRODUCTION_METADATA}")
    
    print("   ✅ Artifacts cleared. Please train a new model.")
    print()


def clear_database():
    """Xóa tất cả models và training runs trong database"""
    print("🗑️  Clearing database...")
    
    try:
        # Soft delete all models
        affected_models = execute_query(
            "UPDATE MLModels SET is_deleted = 1, deleted_at = GETDATE() WHERE ISNULL(is_deleted,0)=0"
        )
        print(f"   ✅ Soft deleted {affected_models} models")
        
        # Soft delete all training runs
        affected_runs = execute_query(
            "UPDATE TrainingRuns SET is_deleted = 1, deleted_at = GETDATE() WHERE ISNULL(is_deleted,0)=0"
        )
        print(f"   ✅ Soft deleted {affected_runs} training runs")
        
        print("   ✅ Database cleared. Please train a new model.")
        print()
        
    except Exception as e:
        print(f"   ❌ Error clearing database: {e}")
        print()


def sync_from_metadata():
    """Đồng bộ database từ metadata file (nếu có)"""
    print("🔄 Syncing database from metadata...")
    
    if not PRODUCTION_METADATA.exists():
        print("   ❌ Metadata file not found. Cannot sync.")
        print()
        return
    
    try:
        import json
        from datetime import datetime
        from app.repositories import model_repository
        
        metadata = json.loads(PRODUCTION_METADATA.read_text())
        
        print(f"   📄 Metadata found:")
        print(f"      Version: {metadata.get('version')}")
        print(f"      Model type: {metadata.get('best_model_type')}")
        print(f"      Dataset ID: {metadata.get('dataset_id')}")
        
        # Get best model from comparison
        comparison = metadata.get('comparison', [])
        if not comparison:
            print("   ❌ No comparison data in metadata")
            print()
            return
        
        best = max(comparison, key=lambda x: (x.get('f1_score', 0), x.get('roc_auc', 0)))
        
        print(f"   🎯 Best model: {best['model_type']}")
        print(f"      F1-Score: {best.get('f1_score', 0):.2%}")
        print(f"      Accuracy: {best.get('accuracy', 0):.2%}")
        
        # Upsert production model
        model_id = model_repository.upsert_production_model({
            "name": model_repository.PRODUCTION_MODEL_NAME,
            "model_type": best['model_type'],
            "version": metadata['version'],
            "artifact_path": str(PRODUCTION_ARTIFACT),
            "is_active": 1,
            "latency_ms": best.get('latency_ms', 0),
            "hyperparameters_json": json.dumps(metadata, ensure_ascii=False),
            "feature_list_json": json.dumps(metadata.get('feature_columns', [])),
            "accuracy": best.get('accuracy'),
            "precision": best.get('precision'),
            "recall": best.get('recall'),
            "f1_score": best.get('f1_score'),
            "roc_auc": best.get('roc_auc'),
        })
        
        print(f"   ✅ Model synced to database (ID: {model_id})")
        
        # Create training runs for all models in comparison
        for item in comparison:
            run_id = model_repository.create_training_run({
                "model_id": model_id,
                "dataset_id": metadata.get('dataset_id'),
                "model_type": item['model_type'],
                "model_version": metadata['version'],
                "train_size": 0,  # Unknown from metadata
                "test_size": 0,   # Unknown from metadata
                "confusion_matrix_json": json.dumps(item.get('confusion_matrix', [])),
                "training_time_seconds": item.get('training_time_seconds', 0),
                "parameters_json": json.dumps(metadata, ensure_ascii=False),
                "started_at": datetime.now(),
                "completed_at": datetime.now(),
                "accuracy": item.get('accuracy'),
                "precision": item.get('precision'),
                "recall": item.get('recall'),
                "f1_score": item.get('f1_score'),
                "roc_auc": item.get('roc_auc'),
            })
            print(f"   ✅ Training run created (ID: {run_id}) for {item['model_type']}")
        
        print()
        print("   ✅ Sync completed successfully!")
        print()
        
    except Exception as e:
        print(f"   ❌ Error syncing: {e}")
        import traceback
        traceback.print_exc()
        print()


def main():
    print("=" * 60)
    print("🔧 MODEL ARTIFACT SYNC TOOL")
    print("=" * 60)
    print()
    
    # Check current state
    check_artifacts()
    check_database()
    
    # Menu
    print("📋 Options:")
    print("   1. Sync database from metadata (recommended)")
    print("   2. Clear artifacts only")
    print("   3. Clear database only")
    print("   4. Clear both artifacts and database")
    print("   5. Exit")
    print()
    
    choice = input("Choose an option (1-5): ").strip()
    print()
    
    if choice == "1":
        sync_from_metadata()
        check_database()
    elif choice == "2":
        confirm = input("⚠️  Are you sure you want to clear artifacts? (yes/no): ").strip().lower()
        if confirm == "yes":
            clear_artifacts()
            check_artifacts()
    elif choice == "3":
        confirm = input("⚠️  Are you sure you want to clear database? (yes/no): ").strip().lower()
        if confirm == "yes":
            clear_database()
            check_database()
    elif choice == "4":
        confirm = input("⚠️  Are you sure you want to clear BOTH? (yes/no): ").strip().lower()
        if confirm == "yes":
            clear_artifacts()
            clear_database()
            check_artifacts()
            check_database()
    elif choice == "5":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid option")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
