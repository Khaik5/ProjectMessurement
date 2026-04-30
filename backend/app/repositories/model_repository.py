from app.database import execute_query, fetch_all, fetch_one, insert_and_get_id

PRODUCTION_MODEL_NAME = "DefectAI P7 Production Model"


def list_models():
    return fetch_all(
        """
        WITH ranked AS (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY name, model_type
                    ORDER BY is_active DESC, created_at DESC, id DESC
                ) AS rn
            FROM MLModels
            WHERE ISNULL(is_deleted,0)=0
        )
        SELECT *
        FROM ranked
        WHERE rn = 1
        ORDER BY
            CASE WHEN name = ? THEN 0 ELSE 1 END,
            is_active DESC,
            created_at DESC
        """,
        [PRODUCTION_MODEL_NAME],
    )


def get_model(model_id: int):
    return fetch_one("SELECT * FROM MLModels WHERE id = ? AND ISNULL(is_deleted,0)=0", [model_id])


def get_active_model():
    return fetch_one("SELECT TOP 1 * FROM MLModels WHERE is_active = 1 AND ISNULL(is_deleted,0)=0 ORDER BY CASE WHEN name = ? THEN 0 ELSE 1 END, created_at DESC", [PRODUCTION_MODEL_NAME])


def get_active_production_model():
    return fetch_one(
        """
        SELECT TOP 1 *
        FROM MLModels
        WHERE is_active = 1 AND name = ? AND ISNULL(is_deleted,0)=0
        ORDER BY created_at DESC, id DESC
        """,
        [PRODUCTION_MODEL_NAME],
    )


def create_model(values: dict):
    return insert_and_get_id(
        """
        INSERT INTO MLModels
        (name, model_type, version, artifact_path, is_active, accuracy, precision, recall, f1_score, roc_auc, latency_ms, hyperparameters_json, feature_list_json, created_at)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
        """,
        [
            values["name"],
            values["model_type"],
            values["version"],
            values["artifact_path"],
            int(values.get("is_active", 0)),
            values.get("accuracy"),
            values.get("precision"),
            values.get("recall"),
            values.get("f1_score"),
            values.get("roc_auc"),
            values.get("latency_ms"),
            values.get("hyperparameters_json"),
            values.get("feature_list_json"),
        ],
    )


def upsert_production_model(values: dict):
    execute_query("UPDATE MLModels SET is_active = 0 WHERE ISNULL(is_deleted,0)=0")
    existing = fetch_one("SELECT TOP 1 id FROM MLModels WHERE name = ? ORDER BY created_at DESC, id DESC", [PRODUCTION_MODEL_NAME])
    if existing:
        execute_query(
            """
            UPDATE MLModels
            SET model_type = ?,
                version = ?,
                artifact_path = ?,
                is_active = 1,
                accuracy = ?,
                precision = ?,
                recall = ?,
                f1_score = ?,
                roc_auc = ?,
                latency_ms = ?,
                hyperparameters_json = ?,
                feature_list_json = ?,
                is_deleted = 0,
                deleted_at = NULL,
                created_at = GETDATE()
            WHERE id = ?
            """,
            [
                values["model_type"],
                values["version"],
                values["artifact_path"],
                values.get("accuracy"),
                values.get("precision"),
                values.get("recall"),
                values.get("f1_score"),
                values.get("roc_auc"),
                values.get("latency_ms"),
                values.get("hyperparameters_json"),
                values.get("feature_list_json"),
                existing["id"],
            ],
        )
        return int(existing["id"])
    return create_model({**values, "name": PRODUCTION_MODEL_NAME, "is_active": 1})


def activate_model(model_id: int):
    execute_query("UPDATE MLModels SET is_active = 0 WHERE ISNULL(is_deleted,0)=0")
    return execute_query("UPDATE MLModels SET is_active = 1 WHERE id = ? AND ISNULL(is_deleted,0)=0", [model_id])


def create_training_run(values: dict):
    return insert_and_get_id(
        """
        INSERT INTO TrainingRuns
        (model_id, dataset_id, model_type, model_version, status, train_size, test_size, accuracy, precision, recall, f1_score, roc_auc,
         confusion_matrix_json, training_time_seconds, parameters_json, started_at, completed_at)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            values.get("model_id"),
            values.get("dataset_id"),
            values["model_type"],
            values["model_version"],
            values.get("status", "completed"),
            values.get("train_size", 0),
            values.get("test_size", 0),
            values.get("accuracy"),
            values.get("precision"),
            values.get("recall"),
            values.get("f1_score"),
            values.get("roc_auc"),
            values.get("confusion_matrix_json"),
            values.get("training_time_seconds"),
            values.get("parameters_json"),
            values.get("started_at"),
            values.get("completed_at"),
        ],
    )


def list_training_runs():
    return fetch_all("SELECT * FROM TrainingRuns WHERE ISNULL(is_deleted,0)=0 ORDER BY started_at DESC")


def get_training_run(run_id: int):
    return fetch_one("SELECT * FROM TrainingRuns WHERE id = ? AND ISNULL(is_deleted,0)=0", [run_id])


def comparison():
    return fetch_all(
        """
        WITH ranked AS (
            SELECT
                tr.model_type AS model,
                tr.model_type,
                tr.accuracy,
                tr.precision,
                tr.recall,
                tr.f1_score,
                tr.roc_auc,
                CAST(CASE WHEN m.is_active = 1 THEN 1 ELSE 0 END AS BIT) AS is_active,
                tr.started_at AS created_at,
                tr.dataset_id,
                tr.confusion_matrix_json,
                ROW_NUMBER() OVER (PARTITION BY tr.model_type ORDER BY tr.started_at DESC, tr.id DESC) AS rn
            FROM TrainingRuns tr
            LEFT JOIN MLModels m ON m.id = tr.model_id
            WHERE ISNULL(tr.is_deleted,0)=0
        )
        SELECT model, model_type, accuracy, precision, recall, f1_score, roc_auc, is_active, created_at, dataset_id, confusion_matrix_json
        FROM ranked
        WHERE rn = 1
        ORDER BY created_at DESC
        """
    )


def soft_delete_model(model_id: int):
    execute_query("UPDATE MLModels SET is_active = 0 WHERE id = ?", [model_id])
    return execute_query("UPDATE MLModels SET is_deleted = 1, deleted_at = GETDATE() WHERE id = ?", [model_id])


def soft_delete_training_run(run_id: int):
    return execute_query("UPDATE TrainingRuns SET is_deleted = 1, deleted_at = GETDATE() WHERE id = ?", [run_id])


def restore_training_run(run_id: int):
    return execute_query("UPDATE TrainingRuns SET is_deleted = 0, deleted_at = NULL WHERE id = ?", [run_id])
