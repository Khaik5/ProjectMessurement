from app.repositories import metric_repository


def list_metrics(limit: int = 500):
    return metric_repository.list_metrics(limit)


def get_metric(record_id: int):
    return metric_repository.get_metric(record_id)


def project_metrics(project_id: int, limit: int = 500):
    return metric_repository.list_by_project(project_id, limit)


def dataset_metrics(dataset_id: int):
    return metric_repository.list_by_dataset(dataset_id)


def statistics(project_id: int, dataset_id: int | None = None):
    if dataset_id:
        rows = metric_repository.list_by_dataset(dataset_id)
        if not rows:
            stats = {}
        else:
            stats = {
                "total_modules": len(rows),
                "average_loc": sum(float(row["loc"]) for row in rows) / len(rows),
                "average_complexity": sum(float(row["complexity"]) for row in rows) / len(rows),
                "average_coupling": sum(float(row["coupling"]) for row in rows) / len(rows),
                "average_churn": sum(float(row["code_churn"]) for row in rows) / len(rows),
            }
    else:
        stats = metric_repository.statistics(project_id) or {}
    return {
        "total_modules": int(stats.get("total_modules") or 0),
        "average_loc": round(float(stats.get("average_loc") or 0), 2),
        "average_complexity": round(float(stats.get("average_complexity") or 0), 2),
        "average_coupling": round(float(stats.get("average_coupling") or 0), 2),
        "average_churn": round(float(stats.get("average_churn") or 0), 2),
    }
