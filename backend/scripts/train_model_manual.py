"""
Script để train model thủ công và populate database
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.ml_training_service import train_production
from app.schemas.model_schema import TrainingRequest

def main():
    print("🚀 Starting manual model training...")
    
    # Tạo training request với dataset #2 (realistic_project_3)
    payload = TrainingRequest(
        project_id=1,
        dataset_id=2,  # Dataset #2: 200 records, balanced
        test_size=0.2,
        random_state=42,
        auto_activate_best=True
    )
    
    print(f"📊 Training with dataset_id={payload.dataset_id}")
    print(f"   Test size: {payload.test_size}")
    print(f"   Random state: {payload.random_state}")
    
    try:
        result = train_production(payload)
        
        print("\n✅ Training completed successfully!")
        print(f"   Best model: {result['best_model_type']}")
        print(f"   Model ID: {result['best_model_id']}")
        print(f"   Artifact: {result['artifact_path']}")
        print(f"   Metadata: {result['metadata_path']}")
        
        print("\n📈 Comparison results:")
        for item in result['comparison']:
            print(f"   - {item['model_type']}: F1={item['f1_score']:.4f}, Accuracy={item['accuracy']:.4f}")
        
        if result.get('warnings'):
            print("\n⚠️  Warnings:")
            for warning in result['warnings']:
                print(f"   - {warning}")
        
        print("\n🎯 Models in database:", len(result['models']))
        print("🏃 Training runs in database:", len(result['training_runs']))
        
    except Exception as e:
        print(f"\n❌ Training failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
