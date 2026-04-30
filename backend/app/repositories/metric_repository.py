from app.database import fetch_all, fetch_one


def list_metrics(limit: int = 500):
    return fetch_all("SELECT TOP (?) * FROM MetricRecords ORDER BY recorded_at DESC", [limit])


def get_metric(record_id: int):
    return fetch_one("SELECT * FROM MetricRecords WHERE id = ?", [record_id])


def list_by_project(project_id: int, limit: int = 500):
    return fetch_all("SELECT TOP (?) * FROM MetricRecords WHERE project_id = ? ORDER BY id DESC", [limit, project_id])


def list_by_dataset(dataset_id: int):
    return fetch_all("SELECT * FROM MetricRecords WHERE dataset_id = ? ORDER BY id", [dataset_id])


def training_records(project_id: int, dataset_id: int | None = None):
    if dataset_id:
        return fetch_all(
            """
            SELECT
                module_name,
                loc, ncloc, cloc,
                complexity, cyclomatic_complexity, depth_of_nesting,
                coupling, cohesion, information_flow_complexity,
                code_churn, change_request_backlog, pending_effort_hours, percent_reused,
                defect_count,
                size_score, complexity_score, coupling_score, churn_score,
                defect_density, kloc, comment_ratio, cohesion_score, reuse_score, risk_score,
                defect_label
            FROM MetricRecords
            WHERE project_id = ? AND dataset_id = ? AND defect_label IS NOT NULL
            """,
            [project_id, dataset_id],
        )
    return fetch_all(
        """
        SELECT
            module_name,
            loc, ncloc, cloc,
            complexity, cyclomatic_complexity, depth_of_nesting,
            coupling, cohesion, information_flow_complexity,
            code_churn, change_request_backlog, pending_effort_hours, percent_reused,
            defect_count,
            size_score, complexity_score, coupling_score, churn_score,
            defect_density, kloc, comment_ratio, cohesion_score, reuse_score, risk_score,
            defect_label
        FROM MetricRecords
        WHERE project_id = ? AND defect_label IS NOT NULL
        """,
        [project_id],
    )


def statistics(project_id: int):
    return fetch_one(
        """
        SELECT
            COUNT(*) AS total_modules,
            AVG(CAST(loc AS FLOAT)) AS average_loc,
            AVG(complexity) AS average_complexity,
            AVG(coupling) AS average_coupling,
            AVG(code_churn) AS average_churn
        FROM MetricRecords
        WHERE project_id = ?
        """,
        [project_id],
    )
