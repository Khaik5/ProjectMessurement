import asyncio
import io

from fastapi import UploadFile

from app.services import dataset_service


def test_upload_training_csv_uses_contract_schema(monkeypatch):
    csv = (
        "module_name,loc,ncloc,cloc,complexity,cyclomatic_complexity,depth_of_nesting,"
        "coupling,cohesion,information_flow_complexity,code_churn,change_request_backlog,"
        "pending_effort_hours,percent_reused,defect_count,defect_label\n"
        "module_a,100,90,10,8,8,2,3,80,5,20,1,2,50,1,0\n"
        "module_b,600,540,60,45,45,6,18,40,20,260,8,10,20,2,1\n"
    )
    inserted_rows = []

    monkeypatch.setattr(dataset_service.dataset_repository, "create_dataset", lambda *args, **kwargs: 99)
    monkeypatch.setattr(
        dataset_service.dataset_repository,
        "get_dataset",
        lambda dataset_id: {"id": dataset_id, "file_name": "train.csv", "has_label": True, "row_count": 2},
    )
    monkeypatch.setattr(dataset_service.dataset_repository, "insert_metric_records", lambda rows: inserted_rows.extend(rows))
    monkeypatch.setattr(dataset_service.dataset_repository, "preview_dataset", lambda dataset_id: [])
    monkeypatch.setattr(dataset_service.project_state_repository, "update_state", lambda *args, **kwargs: 1)
    monkeypatch.setattr(dataset_service, "log_action", lambda *args, **kwargs: None)

    upload = UploadFile(filename="train.csv", file=io.BytesIO(csv.encode("utf-8")))
    result = asyncio.run(dataset_service.upload_dataset(upload, project_id=1, uploaded_by_id=1))

    assert result["validation"]["has_defect_label"] is True
    assert len(inserted_rows) == 2
    assert len(inserted_rows[0]) == 30
    assert inserted_rows[0][11] == 0.8
    assert inserted_rows[0][16] == 0.5
    assert inserted_rows[0][28] == 0.5
