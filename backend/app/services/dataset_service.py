from __future__ import annotations

import json

import pandas as pd

from app.repositories import dataset_repository
from app.repositories import project_state_repository
from app.utils.file_utils import upload_to_dataframe
from app.utils.validators import OPTIONAL_COLUMNS, REQUIRED_COLUMNS, validate_metrics_dataframe
from app.utils.measurement_utils import compute_measurement_metrics
from app.services.audit_service import log_action


async def upload_dataset(file, project_id: int = 1, uploaded_by_id: int | None = 1):
    df = await upload_to_dataframe(file)
    valid, errors, df = validate_metrics_dataframe(df)
    optional_detected = [column for column in OPTIONAL_COLUMNS if column in df.columns]
    missing_required = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    duplicated_modules = int(df["module_name"].duplicated().sum()) if "module_name" in df.columns else 0
    missing_values = {
        column: int(df[column].isna().sum())
        for column in df.columns
        if column in [*REQUIRED_COLUMNS, *OPTIONAL_COLUMNS]
    }
    label_distribution = {}
    if "defect_label" in df.columns:
        label_distribution = {str(k): int(v) for k, v in df["defect_label"].value_counts(dropna=True).to_dict().items()}
    validation_payload = {
        "valid": bool(valid),
        "errors": errors,
        "required_columns": REQUIRED_COLUMNS,
        "optional_columns_detected": optional_detected,
        "missing_columns": missing_required,
        "data_quality": {
            "missing_values": missing_values,
            "invalid_rows": int(df[REQUIRED_COLUMNS].isna().any(axis=1).sum()) if all(column in df.columns for column in REQUIRED_COLUMNS) else 0,
            "duplicated_modules": duplicated_modules,
            "label_distribution": label_distribution,
        },
    }
    if not valid:
        dataset_id = dataset_repository.create_dataset(
            project_id,
            (file.filename or "invalid_dataset").rsplit(".", 1)[0],
            file.filename or "dataset",
            (file.filename or "csv").rsplit(".", 1)[-1],
            len(df),
            uploaded_by_id,
            "FAILED",
            "; ".join(errors),
            "{}",
            has_label=False,
        )
        return {"dataset": dataset_repository.get_dataset(dataset_id), "validation": validation_payload, "preview": []}

    has_label = "defect_label" in df.columns and df["defect_label"].notna().any()
    if "defect_label" in df.columns:
        df["defect_label"] = df["defect_label"].fillna(0).astype(int)
    else:
        df["defect_label"] = None

    # Compute measurement metrics/scores (risk_score, defect_density, etc.)
    df = compute_measurement_metrics(df)

    dataset_id = dataset_repository.create_dataset(
        project_id,
        (file.filename or "metrics_dataset").rsplit(".", 1)[0],
        file.filename or "metrics_dataset.csv",
        (file.filename or "csv").rsplit(".", 1)[-1],
        len(df),
        uploaded_by_id,
        "VALIDATED",
        None,
        json.dumps({**validation_payload, "has_defect_label": bool(has_label)}, ensure_ascii=False),
        has_label=bool(has_label),
    )
    rows = [
        (
            dataset_id,
            project_id,
            None,
            row["module_name"],
            int(row["loc"]) if not pd.isna(row.get("loc")) else 0,
            int(row.get("ncloc") or row["loc"]) if not pd.isna(row.get("ncloc")) else int(row["loc"]),
            int(row.get("cloc") or 0) if not pd.isna(row.get("cloc")) else 0,
            float(row.get("complexity") or 0),
            float(row.get("cyclomatic_complexity") or row.get("complexity") or 0),
            float(row.get("depth_of_nesting") or 0),
            float(row.get("coupling") or 0),
            float(row.get("cohesion") or 0),
            float(row.get("information_flow_complexity") or 0),
            float(row.get("code_churn") or 0),
            float(row.get("change_request_backlog") or 0),
            float(row.get("pending_effort_hours") or 0),
            float(row.get("percent_reused") or 0),
            float(row.get("defect_count") or 0) if not pd.isna(row.get("defect_count")) else None,
            None if pd.isna(row.get("defect_label")) else int(row["defect_label"]),
            float(row.get("kloc") or 0),
            float(row.get("comment_ratio") or 0),
            None if pd.isna(row.get("defect_density")) else float(row.get("defect_density")),
            float(row.get("size_score") or 0),
            float(row.get("complexity_score") or 0),
            float(row.get("coupling_score") or 0),
            float(row.get("churn_score") or 0),
            float(row.get("defect_density_score") or 0),
            float(row.get("cohesion_score") or 0),
            float(row.get("risk_score") or 0),
        )
        for row in df.to_dict(orient="records")
    ]
    dataset_repository.insert_metric_records(rows)
    project_state_repository.update_state(project_id, current_dataset_id=dataset_id)
    log_action("dataset.uploaded", "MetricsDataset", dataset_id, project_id, uploaded_by_id, {"rows": len(rows)})
    return {
        "dataset": dataset_repository.get_dataset(dataset_id),
        "validation": {**validation_payload, "row_count": len(rows), "has_defect_label": bool(has_label)},
        "preview": dataset_repository.preview_dataset(dataset_id),
    }


def list_datasets():
    return dataset_repository.list_datasets()


def get_dataset(dataset_id: int):
    return dataset_repository.get_dataset(dataset_id)


def preview(dataset_id: int):
    dataset = dataset_repository.get_dataset(dataset_id)
    if not dataset:
        raise ValueError(f"Dataset #{dataset_id} not found")
    rows = dataset_repository.preview_dataset(dataset_id)
    return {
        "dataset": dataset,
        "dataset_id": dataset_id,
        "rows": rows,
        "total": len(rows),
        "total_rows": dataset["row_count"] if dataset else 0,
        "analyzed": any(row.get("defect_probability") is not None for row in rows),
        "message": "OK" if rows else "Dataset has no metric records",
    }


def delete_dataset(dataset_id: int):
    affected = dataset_repository.delete_dataset(dataset_id)
    log_action("dataset.deleted", "MetricsDataset", dataset_id)
    return {"deleted": affected > 0}


def history(project_id: int):
    return dataset_repository.history(project_id)


def set_current(dataset_id: int):
    dataset = dataset_repository.get_dataset(dataset_id)
    if not dataset:
        raise ValueError("Dataset not found")
    project_state_repository.update_state(dataset["project_id"], current_dataset_id=dataset_id, current_analysis_dataset_id=dataset_id)
    return project_state_repository.get_state(dataset["project_id"])


def analysis_summary(dataset_id: int):
    return dataset_repository.analysis_summary(dataset_id)


def trainable(project_id: int):
    return dataset_repository.trainable(project_id)
