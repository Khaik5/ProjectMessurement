from fastapi import HTTPException

from app.services import dataset_service, export_service


async def upload_dataset(file, project_id: int):
    return await dataset_service.upload_dataset(file, project_id)


def list_datasets():
    return dataset_service.list_datasets()


def get_dataset(dataset_id: int):
    dataset = dataset_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


def preview(dataset_id: int):
    return dataset_service.preview(dataset_id)


def delete_dataset(dataset_id: int):
    return dataset_service.delete_dataset(dataset_id)


def history(project_id: int):
    return dataset_service.history(project_id)


def set_current(dataset_id: int):
    return dataset_service.set_current(dataset_id)


def analysis_summary(dataset_id: int):
    return dataset_service.analysis_summary(dataset_id)


def export_csv(dataset_id: int):
    return export_service.dataset_csv(dataset_id)


def export_xlsx(dataset_id: int):
    return export_service.dataset_xlsx(dataset_id)
