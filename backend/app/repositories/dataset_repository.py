from app.database import execute_many, execute_query, fetch_all, fetch_one, insert_and_get_id


def list_datasets():
    # Do not mix archived with active selection lists
    return fetch_all("SELECT * FROM MetricsDatasets WHERE status <> 'ARCHIVED' ORDER BY uploaded_at DESC")


def history(project_id: int):
    return fetch_all(
        """
        SELECT
            d.*,
            (SELECT TOP 1 m.name FROM Predictions p LEFT JOIN MLModels m ON m.id = p.model_id WHERE p.dataset_id = d.id ORDER BY p.created_at DESC) AS model_used,
            (SELECT AVG(defect_probability) FROM Predictions WHERE dataset_id = d.id) AS avg_defect_probability,
            (SELECT COUNT(*) FROM Predictions p JOIN RiskLevels r ON r.id = p.risk_level_id WHERE p.dataset_id = d.id AND r.name = 'HIGH') AS high_risk_count,
            (SELECT COUNT(*) FROM Predictions p JOIN RiskLevels r ON r.id = p.risk_level_id WHERE p.dataset_id = d.id AND r.name = 'CRITICAL') AS critical_count,
            (SELECT COUNT(*) FROM Predictions WHERE dataset_id = d.id) AS prediction_count
        FROM MetricsDatasets d
        WHERE d.project_id = ?
        ORDER BY d.uploaded_at DESC
        """,
        [project_id],
    )


def get_dataset(dataset_id: int):
    return fetch_one("SELECT * FROM MetricsDatasets WHERE id = ?", [dataset_id])


def create_dataset(
    project_id: int,
    name: str,
    file_name: str,
    file_type: str,
    row_count: int,
    uploaded_by_id: int | None,
    status: str,
    validation_errors: str | None,
    metadata_json: str | None,
    has_label: bool = False,
):
    return insert_and_get_id(
        """
        INSERT INTO MetricsDatasets
        (project_id, name, file_name, file_type, row_count, uploaded_by_id, status, validation_errors, metadata_json, has_label, uploaded_at)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
        """,
        [project_id, name, file_name, file_type, row_count, uploaded_by_id, status, validation_errors, metadata_json, int(bool(has_label))],
    )


def delete_dataset(dataset_id: int):
    # P7 requirement: do not physically delete; archive dataset for History
    return execute_query("UPDATE MetricsDatasets SET status = 'ARCHIVED' WHERE id = ?", [dataset_id])


def update_status(dataset_id: int, status: str):
    return execute_query("UPDATE MetricsDatasets SET status = ? WHERE id = ?", [status.upper(), dataset_id])


def analysis_summary(dataset_id: int):
    return fetch_one(
        """
        SELECT
            d.id AS dataset_id,
            d.project_id,
            d.file_name,
            d.name,
            d.row_count,
            d.status,
            d.uploaded_at,
            COUNT(p.id) AS prediction_count,
            AVG(p.defect_probability) AS avg_defect_probability,
            SUM(CASE WHEN p.prediction = 1 THEN 1 ELSE 0 END) AS defects_detected,
            SUM(CASE WHEN r.name = 'MEDIUM' THEN 1 ELSE 0 END) AS possible_defects,
            SUM(CASE WHEN r.name IN ('HIGH','CRITICAL') THEN 1 ELSE 0 END) AS high_risk_count,
            SUM(CASE WHEN r.name = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_count,
            MAX(m.name) AS model_used
        FROM MetricsDatasets d
        LEFT JOIN Predictions p ON p.dataset_id = d.id
        LEFT JOIN RiskLevels r ON r.id = p.risk_level_id
        LEFT JOIN MLModels m ON m.id = p.model_id
        WHERE d.id = ?
        GROUP BY d.id, d.project_id, d.file_name, d.name, d.row_count, d.status, d.uploaded_at
        """,
        [dataset_id],
    )


def trainable(project_id: int):
    return fetch_all(
        """
        SELECT
            d.*,
            stats.labeled_records,
            stats.no_defect_count,
            stats.defect_count
        FROM MetricsDatasets d
        CROSS APPLY (
            SELECT
                COUNT(*) AS labeled_records,
                SUM(CASE WHEN mr.defect_label = 0 THEN 1 ELSE 0 END) AS no_defect_count,
                SUM(CASE WHEN mr.defect_label = 1 THEN 1 ELSE 0 END) AS defect_count
            FROM MetricRecords mr
            WHERE mr.dataset_id = d.id
              AND mr.project_id = d.project_id
              AND mr.defect_label IS NOT NULL
        ) stats
        WHERE d.project_id = ?
          AND d.status IN ('VALIDATED','TRAINED','ANALYZED')
          AND d.has_label = 1
          AND stats.labeled_records >= 4
          AND stats.no_defect_count >= 2
          AND stats.defect_count >= 2
        ORDER BY d.uploaded_at DESC
        """,
        [project_id],
    )


def preview_dataset(dataset_id: int, limit: int = 50):
    return fetch_all(
        """
        SELECT TOP (?)
            mr.id,
            mr.dataset_id,
            mr.module_name,
            mr.loc,
            mr.ncloc,
            mr.cloc,
            mr.kloc,
            mr.comment_ratio,
            mr.complexity,
            mr.cyclomatic_complexity,
            mr.depth_of_nesting,
            mr.coupling,
            mr.cohesion,
            mr.information_flow_complexity,
            mr.code_churn,
            mr.change_request_backlog,
            mr.pending_effort_hours,
            mr.percent_reused,
            mr.defect_count,
            mr.defect_label,
            mr.defect_density,
            mr.size_score,
            mr.complexity_score,
            mr.coupling_score,
            mr.churn_score,
            mr.cohesion_score,
            mr.risk_score,
            p.defect_probability,
            p.prediction_label,
            rl.name AS risk_level,
            rl.color,
            p.suggested_action,
            COALESCE(p.created_at, mr.recorded_at) AS [timestamp],
            mr.recorded_at
        FROM MetricRecords mr
        LEFT JOIN Predictions p
            ON p.dataset_id = mr.dataset_id
            AND p.module_name = mr.module_name
        LEFT JOIN RiskLevels rl
            ON rl.id = p.risk_level_id
        WHERE mr.dataset_id = ?
        ORDER BY mr.id ASC
        """,
        [limit, dataset_id],
    )


def insert_metric_records(rows: list[tuple]):
    return execute_many(
        """
        INSERT INTO MetricRecords
        (
            dataset_id, project_id, module_id, module_name,
            loc, ncloc, cloc,
            complexity, cyclomatic_complexity, depth_of_nesting,
            coupling, cohesion, information_flow_complexity,
            code_churn, change_request_backlog, pending_effort_hours, percent_reused,
            defect_count, defect_label,
            kloc, comment_ratio, defect_density,
            size_score, complexity_score, coupling_score, churn_score, defect_density_score, cohesion_score, reuse_score,
            risk_score,
            recorded_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
        """,
        rows,
    )
