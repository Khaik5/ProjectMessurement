from app.database import fetch_all, fetch_one


def summary(project_id: int, dataset_id: int):
    return fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM MetricRecords WHERE dataset_id = ?) AS total_modules,
            (SELECT COUNT(*) FROM Predictions WHERE dataset_id = ?) AS prediction_count,
            (SELECT AVG(defect_probability) FROM Predictions WHERE dataset_id = ?) AS avg_probability,
            (SELECT AVG(ISNULL(risk_score, 0)) FROM Predictions WHERE dataset_id = ?) AS avg_risk_score,
            (SELECT SUM(CASE WHEN prediction_label = 'No Defect' THEN 1 ELSE 0 END) FROM Predictions WHERE dataset_id = ?) AS no_defect_count,
            (SELECT SUM(CASE WHEN prediction_label = 'Possible Defect' THEN 1 ELSE 0 END) FROM Predictions WHERE dataset_id = ?) AS possible_defect_label_count,
            (SELECT SUM(CASE WHEN prediction_label = 'Defect' THEN 1 ELSE 0 END) FROM Predictions WHERE dataset_id = ?) AS defects_detected,
            (SELECT SUM(CASE WHEN r.name = 'MEDIUM' THEN 1 ELSE 0 END) FROM Predictions p LEFT JOIN RiskLevels r ON r.id = p.risk_level_id WHERE p.dataset_id = ?) AS possible_defects,
            (SELECT SUM(CASE WHEN r.name IN ('HIGH','CRITICAL') THEN 1 ELSE 0 END) FROM Predictions p LEFT JOIN RiskLevels r ON r.id = p.risk_level_id WHERE p.dataset_id = ?) AS high_risk,
            (SELECT SUM(CASE WHEN r.name = 'CRITICAL' THEN 1 ELSE 0 END) FROM Predictions p LEFT JOIN RiskLevels r ON r.id = p.risk_level_id WHERE p.dataset_id = ?) AS critical_count,
            (SELECT CASE WHEN COUNT(*) > 0 AND SUM(CASE WHEN model_id IS NULL THEN 1 ELSE 0 END) = COUNT(*) THEN 1 ELSE 0 END FROM Predictions WHERE dataset_id = ?) AS used_fallback,
            (SELECT TOP 1 accuracy FROM MLModels WHERE is_active = 1 AND name = 'DefectAI P7 Production Model' ORDER BY created_at DESC) AS active_accuracy
        """,
        [
            dataset_id,
            dataset_id,
            dataset_id,
            dataset_id,
            dataset_id,
            dataset_id,
            dataset_id,
            dataset_id,
            dataset_id,
            dataset_id,
            dataset_id,
        ],
    )


def active_model():
    return fetch_one("SELECT TOP 1 * FROM MLModels WHERE is_active = 1 AND name = 'DefectAI P7 Production Model' ORDER BY created_at DESC")


def risk_distribution(project_id: int, dataset_id: int):
    return fetch_all(
        """
        SELECT r.name, r.color, COUNT(p.id) AS value
        FROM RiskLevels r
        LEFT JOIN Predictions p ON p.risk_level_id = r.id AND p.project_id = ? AND p.dataset_id = ?
        GROUP BY r.name, r.color, r.min_probability
        ORDER BY r.min_probability
        """,
        [project_id, dataset_id],
    )


def probability_trend(project_id: int, dataset_id: int):
    return fetch_all(
        """
        SELECT
            CONVERT(date, p.created_at) AS [date],
            AVG(p.defect_probability) AS probability
        FROM Predictions p
        WHERE p.project_id = ? AND p.dataset_id = ?
        GROUP BY CONVERT(date, p.created_at)
        ORDER BY CONVERT(date, p.created_at)
        """,
        [project_id, dataset_id],
    )


def risk_heatmap(project_id: int, dataset_id: int):
    return fetch_all(
        """
        SELECT TOP 80 p.module_name, p.loc, p.complexity, p.coupling, p.code_churn, p.defect_probability, r.name AS risk_level, r.color
        FROM Predictions p
        JOIN RiskLevels r ON r.id = p.risk_level_id
        WHERE p.project_id = ? AND p.dataset_id = ?
        ORDER BY p.defect_probability DESC, p.created_at DESC
        """,
        [project_id, dataset_id],
    )


def loc_complexity(project_id: int, dataset_id: int):
    return fetch_all(
        """
        SELECT TOP 200 mr.module_name, mr.loc, mr.complexity, mr.coupling, mr.code_churn, p.defect_probability
        FROM MetricRecords mr
        LEFT JOIN Predictions p ON p.dataset_id = mr.dataset_id AND p.module_name = mr.module_name
        WHERE mr.project_id = ? AND mr.dataset_id = ?
        ORDER BY mr.id
        """,
        [project_id, dataset_id],
    )


def churn_probability(project_id: int, dataset_id: int):
    return fetch_all(
        """
        SELECT TOP 100 module_name, code_churn, coupling, defect_probability
        FROM Predictions
        WHERE project_id = ? AND dataset_id = ?
        ORDER BY created_at DESC
        """,
        [project_id, dataset_id],
    )


def coupling_distribution(project_id: int, dataset_id: int):
    return fetch_all(
        """
        SELECT bucket, COUNT(*) AS count
        FROM (
            SELECT CASE
                WHEN coupling < 5 THEN '0-5'
                WHEN coupling < 10 THEN '5-10'
                WHEN coupling < 20 THEN '10-20'
                ELSE '20+'
            END AS bucket
            FROM MetricRecords WHERE project_id = ? AND dataset_id = ?
        ) x
        GROUP BY bucket
        ORDER BY bucket
        """,
        [project_id, dataset_id],
    )


def dataset_info(dataset_id: int):
    return fetch_one("SELECT * FROM MetricsDatasets WHERE id = ?", [dataset_id])


def top_risky_modules(project_id: int, dataset_id: int, limit: int = 10):
    return fetch_all(
        """
        SELECT TOP (?) p.module_name, p.loc, p.complexity, p.coupling, p.code_churn,
               p.defect_probability, p.prediction_label, p.risk_score,
               r.name AS risk_level, r.color, p.suggested_action, p.created_at
        FROM Predictions p
        JOIN RiskLevels r ON r.id = p.risk_level_id
        WHERE p.project_id = ? AND p.dataset_id = ?
        ORDER BY p.defect_probability DESC, p.created_at DESC
        """,
        [limit, project_id, dataset_id],
    )


def risk_heatmap_v2(project_id: int, dataset_id: int, limit: int = 80):
    return fetch_all(
        """
        SELECT TOP (?)
            p.module_name,
            p.loc,
            p.complexity,
            p.coupling,
            p.code_churn,
            p.defect_probability,
            p.prediction_label,
            p.risk_score,
            p.size_score,
            p.complexity_score,
            p.coupling_score,
            p.churn_score,
            r.name AS risk_level,
            r.color,
            p.suggested_action,
            CASE WHEN p.model_id IS NULL THEN 'Measurement fallback' ELSE 'AI production model' END AS model_source
        FROM Predictions p
        JOIN RiskLevels r ON r.id = p.risk_level_id
        WHERE p.project_id = ? AND p.dataset_id = ?
        ORDER BY p.defect_probability DESC, p.created_at DESC
        """,
        [limit, project_id, dataset_id],
    )


def loc_complexity_scatter(project_id: int, dataset_id: int, limit: int = 200):
    return fetch_all(
        """
        SELECT TOP (?)
            mr.module_name,
            mr.loc,
            mr.complexity,
            mr.coupling,
            mr.code_churn,
            mr.risk_score,
            p.defect_probability
        FROM MetricRecords mr
        LEFT JOIN Predictions p
            ON p.dataset_id = mr.dataset_id
            AND p.project_id = mr.project_id
            AND p.module_name = mr.module_name
        WHERE mr.project_id = ? AND mr.dataset_id = ?
        ORDER BY mr.id
        """,
        [limit, project_id, dataset_id],
    )


def critical_alerts(project_id: int, dataset_id: int, limit: int = 10):
    return fetch_all(
        """
        SELECT TOP (?)
            p.module_name,
            p.defect_probability,
            p.prediction_label,
            r.name AS risk_level,
            r.color,
            p.suggested_action,
            p.created_at
        FROM Predictions p
        JOIN RiskLevels r ON r.id = p.risk_level_id
        WHERE p.project_id = ? AND p.dataset_id = ? AND r.name = 'CRITICAL'
        ORDER BY p.defect_probability DESC, p.created_at DESC
        """,
        [limit, project_id, dataset_id],
    )


def used_fallback(project_id: int, dataset_id: int) -> bool:
    # Kept for backward compatibility; prefer `summary.used_fallback`
    row = fetch_one("SELECT TOP 1 used_fallback = (CASE WHEN COUNT(*) > 0 AND SUM(CASE WHEN model_id IS NULL THEN 1 ELSE 0 END) = COUNT(*) THEN 1 ELSE 0 END) FROM Predictions WHERE project_id = ? AND dataset_id = ?", [project_id, dataset_id]) or {}
    return bool(int(row.get("used_fallback") or 0) == 1)


def latest_confusion_matrix_for_active_model():
    return fetch_one(
        """
        SELECT TOP 1 tr.confusion_matrix_json
        FROM TrainingRuns tr
        JOIN MLModels m ON m.id = tr.model_id
        WHERE m.is_active = 1 AND ISNULL(tr.is_deleted,0)=0 AND ISNULL(m.is_deleted,0)=0
        ORDER BY tr.completed_at DESC, tr.id DESC
        """
    )
