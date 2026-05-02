from __future__ import annotations

import json

import pandas as pd

from app.repositories import dataset_repository
from app.repositories import metric_repository, model_repository, prediction_repository
from app.repositories import project_state_repository
from app.ml.feature_engineering import build_p7_features
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

    has_label = "defect_label" in df.columns and df["defect_label"].notna().all()
    if has_label:
        df["defect_label"] = df["defect_label"].astype(int)
    else:
        df["defect_label"] = None

    # Compute measurement metrics/scores without label-derived leakage.
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
            float(row.get("reuse_score") or 0),
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


def _series_stats(df: pd.DataFrame, column: str) -> dict:
    if column not in df.columns:
        return {"min": None, "mean": None, "max": None}
    values = pd.to_numeric(df[column], errors="coerce").dropna()
    if values.empty:
        return {"min": None, "mean": None, "max": None}
    return {"min": float(values.min()), "mean": float(values.mean()), "max": float(values.max())}


def quality_summary(dataset_id: int):
    dataset = dataset_repository.get_dataset(dataset_id)
    if not dataset:
        raise ValueError(f"Dataset #{dataset_id} not found")
    metrics = metric_repository.list_by_dataset(dataset_id)
    if not metrics:
        return {"dataset": dataset, "message": "Dataset has no MetricRecords", "feature_stats": {}, "prediction_summary": None}
    df = pd.DataFrame(metrics)
    engineered = build_p7_features(df, use_label_density=False)
    feature_columns = [
        "complexity",
        "cyclomatic_complexity",
        "coupling",
        "cohesion",
        "code_churn",
        "change_request_backlog",
        "pending_effort_hours",
        "percent_reused",
        "risk_score",
    ]
    labels = pd.to_numeric(df.get("defect_label"), errors="coerce") if "defect_label" in df else pd.Series(dtype=float)
    defect_counts = pd.to_numeric(df.get("defect_count"), errors="coerce") if "defect_count" in df else pd.Series(dtype=float)
    predictions = prediction_repository.by_dataset(dataset_id)
    probability_values = pd.Series([row.get("defect_probability") for row in predictions], dtype="float64") if predictions else pd.Series(dtype=float)
    risk_counts = {level: 0 for level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]}
    for row in predictions:
        risk = str(row.get("risk_level") or "").upper()
        if risk in risk_counts:
            risk_counts[risk] += 1
    active_model = model_repository.get_active_production_model()
    prediction_model = next((row for row in predictions if row.get("model_id")), None)
    warnings = list(engineered.attrs.get("warnings", []))
    for ratio_column in ["cohesion", "percent_reused"]:
        raw_values = pd.to_numeric(df.get(ratio_column), errors="coerce") if ratio_column in df else pd.Series(dtype=float)
        if not raw_values.empty and raw_values.dropna().gt(1).any():
            warnings.append(f"{ratio_column} contained values > 1 and should be interpreted as 0-100 percentage input.")
        normalized = pd.to_numeric(engineered.get(ratio_column), errors="coerce")
        if normalized.dropna().gt(1).any() or normalized.dropna().lt(0).any():
            warnings.append(f"{ratio_column} normalization produced values outside [0,1].")
    return {
        "dataset": dataset,
        "total_modules": len(df),
        "feature_stats": {column: _series_stats(engineered, column) for column in feature_columns},
        "label_summary": {
            "label_0": int((labels == 0).sum()) if not labels.empty else 0,
            "label_1": int((labels == 1).sum()) if not labels.empty else 0,
            "positive_rate": float((labels == 1).mean()) if not labels.dropna().empty else None,
        },
        "defect_count_summary": {
            "zero_count": int((defect_counts.fillna(0) == 0).sum()) if not defect_counts.empty else 0,
            "max": float(defect_counts.max()) if not defect_counts.dropna().empty else None,
            "avg": float(defect_counts.mean()) if not defect_counts.dropna().empty else None,
        },
        "prediction_summary": {
            "total": len(predictions),
            "avg_probability": float(probability_values.mean()) if not probability_values.empty else None,
            "min_probability": float(probability_values.min()) if not probability_values.empty else None,
            "max_probability": float(probability_values.max()) if not probability_values.empty else None,
            "risk_distribution": risk_counts,
            "model_id": prediction_model.get("model_id") if prediction_model else None,
            "model_used": prediction_model.get("model_used") if prediction_model else None,
        },
        "active_model": {
            "id": active_model.get("id") if active_model else None,
            "name": active_model.get("name") if active_model else None,
            "model_type": active_model.get("model_type") if active_model else None,
            "dataset_id": active_model.get("dataset_id") if active_model else None,
            "training_profile": active_model.get("training_profile") if active_model else None,
            "threshold": active_model.get("threshold") if active_model else None,
            "accuracy": active_model.get("accuracy") if active_model else None,
            "precision": active_model.get("precision") if active_model else None,
            "recall": active_model.get("recall") if active_model else None,
            "f1_score": active_model.get("f1_score") if active_model else None,
            "roc_auc": active_model.get("roc_auc") if active_model else None,
            "pr_auc": active_model.get("pr_auc") if active_model else None,
        },
        "warnings": warnings,
    }


def trainable(project_id: int):
    return dataset_repository.trainable(project_id)
