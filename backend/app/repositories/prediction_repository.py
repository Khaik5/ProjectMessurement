from app.database import execute_many, fetch_all, fetch_one, insert_and_get_id


def insert_prediction(values: dict):
    return insert_and_get_id(
        """
        INSERT INTO Predictions
        (
            project_id, dataset_id, model_id,
            module_name,
            loc, complexity, coupling, code_churn,
            defect_probability, prediction,
            prediction_label,
            risk_score,
            defect_density, size_score, complexity_score, coupling_score, churn_score,
            risk_level_id, suggested_action, created_at
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
        """,
        [
            values["project_id"],
            values.get("dataset_id"),
            values.get("model_id"),
            values["module_name"],
            values["loc"],
            values["complexity"],
            values["coupling"],
            values["code_churn"],
            values["defect_probability"],
            values["prediction"],
            values.get("prediction_label"),
            values.get("risk_score"),
            values.get("defect_density"),
            values.get("size_score"),
            values.get("complexity_score"),
            values.get("coupling_score"),
            values.get("churn_score"),
            values["risk_level_id"],
            values["suggested_action"],
        ],
    )


def delete_by_dataset(dataset_id: int):
    from app.database import execute_query

    return execute_query("DELETE FROM Predictions WHERE dataset_id = ?", [dataset_id])


def insert_predictions(rows: list[tuple]):
    return execute_many(
        """
        INSERT INTO Predictions
        (
            project_id, dataset_id, model_id,
            module_name,
            loc, complexity, coupling, code_churn,
            defect_probability, prediction,
            prediction_label,
            risk_score,
            defect_density, size_score, complexity_score, coupling_score, churn_score,
            risk_level_id, suggested_action, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
        """,
        rows,
    )


def list_predictions(limit: int = 500):
    return fetch_all(
        """
        SELECT TOP (?) p.*, r.name AS risk_level, r.color
        FROM Predictions p
        JOIN RiskLevels r ON r.id = p.risk_level_id
        ORDER BY p.created_at DESC
        """,
        [limit],
    )


def by_project(project_id: int, limit: int = 500):
    return fetch_all(
        """
        SELECT TOP (?) p.*, r.name AS risk_level, r.color
        FROM Predictions p
        JOIN RiskLevels r ON r.id = p.risk_level_id
        WHERE p.project_id = ?
        ORDER BY p.created_at DESC
        """,
        [limit, project_id],
    )


def by_dataset(dataset_id: int):
    return fetch_all(
        """
        SELECT
            p.id,
            p.dataset_id,
            p.project_id,
            p.model_id,
            p.module_name,
            p.loc,
            p.complexity,
            p.coupling,
            p.code_churn,
            p.defect_probability,
            p.prediction,
            p.prediction_label,
            p.risk_score,
            p.defect_density,
            p.size_score,
            p.complexity_score,
            p.coupling_score,
            p.churn_score,
            r.name AS risk_level,
            r.color,
            p.suggested_action,
            p.created_at,
            m.name AS model_used,
            CASE WHEN p.model_id IS NULL THEN 'Measurement fallback' ELSE 'AI production model' END AS model_source
        FROM Predictions p
        LEFT JOIN RiskLevels r ON r.id = p.risk_level_id
        LEFT JOIN MLModels m ON m.id = p.model_id
        WHERE p.dataset_id = ?
        ORDER BY p.defect_probability DESC, p.created_at DESC
        """,
        [dataset_id],
    )


def top_risk(project_id: int = 1, limit: int = 10, dataset_id: int | None = None):
    if dataset_id:
        return fetch_all(
            """
            SELECT TOP (?) p.module_name, p.loc, p.complexity, p.coupling, p.code_churn, p.defect_probability,
                   p.prediction, p.created_at, r.name AS risk_level, r.color
            FROM Predictions p
            JOIN RiskLevels r ON r.id = p.risk_level_id
            WHERE p.project_id = ? AND p.dataset_id = ?
            ORDER BY p.defect_probability DESC, p.created_at DESC
            """,
            [limit, project_id, dataset_id],
        )
    return fetch_all(
        """
        SELECT TOP (?) p.module_name, p.loc, p.complexity, p.coupling, p.code_churn, p.defect_probability,
               p.prediction, p.created_at, r.name AS risk_level, r.color
        FROM Predictions p
        JOIN RiskLevels r ON r.id = p.risk_level_id
        WHERE p.project_id = ?
        ORDER BY p.defect_probability DESC, p.created_at DESC
        """,
        [limit, project_id],
    )


def recent(limit: int = 20):
    return list_predictions(limit)


def get_risk_level_id(name: str):
    row = fetch_one("SELECT id FROM RiskLevels WHERE name = ?", [name])
    return int(row["id"]) if row else None
