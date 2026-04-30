from __future__ import annotations

import io
import json
from collections import Counter

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

from app.repositories import dataset_repository, metric_repository, model_repository, prediction_repository, report_repository
from app.utils.risk_utils import prediction_label

NAVY = "0F172A"
WHITE = "FFFFFF"
RISK_FILLS = {"LOW": "DCFCE7", "MEDIUM": "FEF3C7", "HIGH": "FFEDD5", "CRITICAL": "FEE2E2"}
RISK_TEXT = {"LOW": "166534", "MEDIUM": "854D0E", "HIGH": "9A3412", "CRITICAL": "991B1B"}
PREDICTION_FILLS = {"No Defect": "CCFBF1", "Possible Defect": "FEF3C7", "Defect": "FEE2E2"}
PREDICTION_TEXT = {"No Defect": "115E59", "Possible Defect": "92400E", "Defect": "991B1B"}


def _risk_distribution(rows: list[dict]) -> list[dict]:
    counts = Counter(row.get("risk_level") for row in rows)
    return [{"risk_level": key, "count": counts.get(key, 0)} for key in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]]


def _prediction_rows(dataset_id: int) -> list[dict]:
    rows = prediction_repository.by_dataset(dataset_id)
    if rows:
        return [
            {
                "Module Name": row["module_name"],
                "LOC": row["loc"],
                "NCLOC": row.get("ncloc"),
                "CLOC": row.get("cloc"),
                "Complexity": row["complexity"],
                "Cyclomatic Complexity": row.get("cyclomatic_complexity"),
                "Coupling": row["coupling"],
                "Cohesion": row.get("cohesion"),
                "Code Churn": row["code_churn"],
                "Defect Density": row.get("defect_density"),
                "Risk Score": row.get("risk_score"),
                "Defect Probability": row["defect_probability"],
                "Prediction Label": row.get("prediction_label") or prediction_label(row["defect_probability"]),
                "Risk Level": row["risk_level"],
                "Suggested Action": row["suggested_action"],
                "Model Used": row.get("model_used") or ("Measurement-based fallback" if row.get("model_id") is None else "DefectAI P7 Production Model"),
                "Created At": row["created_at"],
            }
            for row in rows
        ]
    raise ValueError("Dataset has no predictions to export.")


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


def _style_sheet(ws):
    thin = Side(style="thin", color="CBD5E1")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    for cell in ws[1]:
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.font = Font(color=WHITE, bold=True)
        cell.alignment = Alignment(horizontal="center")
    for row in ws.iter_rows():
        for cell in row:
            cell.border = border
            cell.alignment = Alignment(vertical="center")
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    for column_cells in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in column_cells)
        ws.column_dimensions[get_column_letter(column_cells[0].column)].width = min(max_len + 3, 45)


def _write_rows(ws, rows: list[dict]):
    if not rows:
        ws.append(["No data"])
        return
    headers = list(rows[0].keys())
    ws.append(headers)
    for row in rows:
        ws.append([row.get(header) for header in headers])
    _style_sheet(ws)
    if "Risk Level" in headers:
        col = headers.index("Risk Level") + 1
        for row_idx in range(2, ws.max_row + 1):
            value = ws.cell(row_idx, col).value
            if value in RISK_FILLS:
                ws.cell(row_idx, col).fill = PatternFill("solid", fgColor=RISK_FILLS[value])
                ws.cell(row_idx, col).font = Font(bold=True, color=RISK_TEXT.get(value, "0F172A"))
    if "Prediction Label" in headers:
        col = headers.index("Prediction Label") + 1
        for row_idx in range(2, ws.max_row + 1):
            value = ws.cell(row_idx, col).value
            if value in PREDICTION_FILLS:
                ws.cell(row_idx, col).fill = PatternFill("solid", fgColor=PREDICTION_FILLS[value])
                ws.cell(row_idx, col).font = Font(bold=True, color=PREDICTION_TEXT.get(value, "0F172A"))
    probability_header = "Defect Probability" if "Defect Probability" in headers else "Final Probability" if "Final Probability" in headers else None
    if probability_header:
        col = headers.index(probability_header) + 1
        col_letter = get_column_letter(col)
        for row_idx in range(2, ws.max_row + 1):
            ws.cell(row_idx, col).number_format = "0.0%"
        ws.conditional_formatting.add(
            f"{col_letter}2:{col_letter}{ws.max_row}",
            ColorScaleRule(start_type="num", start_value=0, start_color="22C55E", mid_type="num", mid_value=0.6, mid_color="F59E0B", end_type="num", end_value=1, end_color="DC2626"),
        )


def dataset_xlsx(dataset_id: int) -> bytes:
    dataset = dataset_repository.get_dataset(dataset_id)
    predictions = prediction_repository.by_dataset(dataset_id)
    if not predictions:
        raise ValueError("Dataset has no predictions to export.")
    prediction_rows = _prediction_rows(dataset_id)
    models = model_repository.comparison()
    active_model = model_repository.get_active_production_model()
    distribution = _risk_distribution(predictions)
    avg = sum(float(row.get("defect_probability") or 0) for row in predictions) / max(len(predictions), 1)
    high_count = sum(1 for row in predictions if row.get("risk_level") in {"HIGH", "CRITICAL"})
    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    _write_rows(
        ws,
        [
            {"Metric": "Project ID", "Value": dataset.get("project_id") if dataset else ""},
            {"Metric": "Dataset Name", "Value": dataset.get("file_name") if dataset else dataset_id},
            {"Metric": "Analysis Date", "Value": predictions[0]["created_at"] if predictions else ""},
            {"Metric": "Active Model", "Value": active_model.get("name") if active_model else "Measurement-based fallback"},
            {"Metric": "Total Modules", "Value": dataset.get("row_count") if dataset else len(prediction_rows)},
            {"Metric": "Defects Detected", "Value": sum(1 for row in prediction_rows if row.get("Prediction Label") == "Defect")},
            {"Metric": "Avg Defect Probability", "Value": avg},
            {"Metric": "High/Critical Count", "Value": high_count},
        ],
    )
    ws["B7"].number_format = "0.0%"

    # Metrics sheet (raw + measurement)
    ws_metrics = wb.create_sheet("Measurement Metrics")
    metric_rows = metric_repository.list_by_dataset(dataset_id)
    metrics_table = []
    for r in metric_rows:
        metrics_table.append(
            {
                "Module Name": r.get("module_name"),
                "LOC": r.get("loc"),
                "NCLOC": r.get("ncloc"),
                "CLOC": r.get("cloc"),
                "Complexity": r.get("complexity"),
                "Cyclomatic Complexity": r.get("cyclomatic_complexity"),
                "Depth of Nesting": r.get("depth_of_nesting"),
                "Coupling": r.get("coupling"),
                "Cohesion": r.get("cohesion"),
                "Information Flow Complexity": r.get("information_flow_complexity"),
                "Code Churn": r.get("code_churn"),
                "Change Request Backlog": r.get("change_request_backlog"),
                "Pending Effort Hours": r.get("pending_effort_hours"),
                "Percent Reused": r.get("percent_reused"),
                "Defect Count": r.get("defect_count"),
                "Defect Label": r.get("defect_label"),
                "KLOC": r.get("kloc"),
                "Comment Ratio": r.get("comment_ratio"),
                "Defect Density": r.get("defect_density"),
                "Size Score": r.get("size_score"),
                "Complexity Score": r.get("complexity_score"),
                "Coupling Score": r.get("coupling_score"),
                "Churn Score": r.get("churn_score"),
                "Risk Score": r.get("risk_score"),
            }
        )
    _write_rows(ws_metrics, metrics_table)

    ws_pred = wb.create_sheet("AI Predictions")
    # Ensure Predictions columns match the spec order
    if prediction_rows and "Module Name" in prediction_rows[0]:
        ordered = []
        for r in prediction_rows:
            ordered.append(
                {
                    "Module Name": r.get("Module Name"),
                    "LOC": r.get("LOC"),
                    "NCLOC": r.get("NCLOC"),
                    "CLOC": r.get("CLOC"),
                    "Complexity": r.get("Complexity"),
                    "Cyclomatic Complexity": r.get("Cyclomatic Complexity"),
                    "Coupling": r.get("Coupling"),
                    "Cohesion": r.get("Cohesion"),
                    "Code Churn": r.get("Code Churn"),
                    "Defect Density": r.get("Defect Density"),
                    "Risk Score": r.get("Risk Score"),
                    "Defect Probability": r.get("Defect Probability"),
                    "Prediction Label": r.get("Prediction Label"),
                    "Risk Level": r.get("Risk Level"),
                    "Suggested Action": r.get("Suggested Action"),
                    "Model Used": r.get("Model Used"),
                }
            )
        _write_rows(ws_pred, ordered)
    else:
        _write_rows(ws_pred, prediction_rows)
    headers = [cell.value for cell in ws_pred[1]]
    if len(prediction_rows) > 1 and "Defect Probability" in headers:
        chart = BarChart()
        chart.title = "Defect Probability by Module"
        chart.y_axis.title = "Probability"
        chart.x_axis.title = "Module"
        max_row = min(ws_pred.max_row, 25)
        data_col = headers.index("Defect Probability") + 1
        data = Reference(ws_pred, min_col=data_col, min_row=1, max_row=max_row)
        cats = Reference(ws_pred, min_col=1, min_row=2, max_row=max_row)
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        chart.height = 8
        chart.width = 18
        ws_pred.add_chart(chart, "K2")

    ws_model = wb.create_sheet("Model Performance")
    _write_rows(ws_model, models or [{"Model": "No active model", "Accuracy": None}])

    ws_risk = wb.create_sheet("Risk Distribution")
    _write_rows(ws_risk, distribution)
    if ws_risk.max_row > 1:
        chart = BarChart()
        chart.title = "Risk Distribution"
        data = Reference(ws_risk, min_col=2, min_row=1, max_row=ws_risk.max_row)
        cats = Reference(ws_risk, min_col=1, min_row=2, max_row=ws_risk.max_row)
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        ws_risk.add_chart(chart, "D2")

    ws_heatmap = wb.create_sheet("Risk Heatmap")
    _write_rows(
        ws_heatmap,
        [
            {
                "Module Name": row.get("module_name"),
                "Size Score": row.get("size_score"),
                "Complexity Score": row.get("complexity_score"),
                "Coupling Score": row.get("coupling_score"),
                "Churn Score": row.get("churn_score"),
                "Final Probability": row.get("defect_probability"),
                "Prediction Label": row.get("prediction_label"),
                "Risk Level": row.get("risk_level"),
            }
            for row in predictions
        ],
    )

    ws_matrix = wb.create_sheet("Confusion Matrix")
    matrix_rows = [{"Cell": "TN", "Value": 0}, {"Cell": "FP", "Value": 0}, {"Cell": "FN", "Value": 0}, {"Cell": "TP", "Value": 0}]
    for model in models:
        try:
            parsed = json.loads(model.get("confusion_matrix_json") or "null")
        except Exception:
            parsed = None
        if isinstance(parsed, list) and len(parsed) >= 2:
            matrix_rows = [
                {"Cell": "TN", "Value": parsed[0][0]},
                {"Cell": "FP", "Value": parsed[0][1]},
                {"Cell": "FN", "Value": parsed[1][0]},
                {"Cell": "TP", "Value": parsed[1][1]},
            ]
            break
        if isinstance(parsed, dict):
            matrix_rows = [{"Cell": str(key).upper(), "Value": value} for key, value in parsed.items()]
            break
    _write_rows(ws_matrix, matrix_rows)

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def dataset_csv(dataset_id: int) -> bytes:
    return dataframe_to_csv_bytes(pd.DataFrame(_prediction_rows(dataset_id)))


def _pdf_for_dataset(dataset_id: int, title: str) -> bytes:
    rows = prediction_repository.by_dataset(dataset_id)
    if not rows:
        raise ValueError("Dataset has no predictions to export.")
    dataset = dataset_repository.get_dataset(dataset_id)
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    pdf.setTitle(title)
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(36, height - 42, title)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(36, height - 62, f"Dataset: {dataset.get('file_name') if dataset else dataset_id}")
    avg = sum(float(row.get("defect_probability") or 0) for row in rows) / max(len(rows), 1)
    high = sum(1 for row in rows if row.get("risk_level") in {"HIGH", "CRITICAL"})
    pdf.drawString(36, height - 78, f"Modules: {len(rows)}  Avg probability: {avg * 100:.1f}%  High/Critical: {high}")
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(36, height - 110, "Risk Heatmap")
    x, y = 36, height - 135
    for idx, row in enumerate(rows[:70]):
        risk = row.get("risk_level", "LOW")
        fill = {
            "LOW": colors.HexColor("#dcfce7"),
            "MEDIUM": colors.HexColor("#fef3c7"),
            "HIGH": colors.HexColor("#ffedd5"),
            "CRITICAL": colors.HexColor("#fee2e2"),
        }.get(risk, colors.white)
        pdf.setFillColor(fill)
        pdf.rect(x, y, 102, 34, stroke=1, fill=1)
        pdf.setFillColor(colors.HexColor("#0f172a"))
        pdf.setFont("Helvetica-Bold", 6)
        pdf.drawString(x + 4, y + 20, str(row["module_name"])[:18])
        pdf.setFont("Helvetica", 7)
        pdf.drawString(x + 4, y + 8, f"{risk} {float(row['defect_probability']) * 100:.1f}%")
        x += 108
        if x > width - 120:
            x = 36
            y -= 42
            if y < 42:
                pdf.showPage()
                x, y = 36, height - 60
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def dataset_pdf(dataset_id: int) -> bytes:
    return _pdf_for_dataset(dataset_id, "DefectAI P7 Report")


def report_rows(report_id: int) -> list[dict]:
    report = report_repository.get_report(report_id)
    if not report:
        raise ValueError("Report not found")
    filters = json.loads(report.get("filters_json") or "{}")
    dataset_id = filters.get("dataset_id")
    if dataset_id:
        return _prediction_rows(dataset_id)
    raise ValueError("Report is not linked to a dataset")


def report_csv(report_id: int) -> bytes:
    report = report_repository.get_report(report_id)
    if not report:
        return dataset_csv(report_id)
    filters = json.loads(report.get("filters_json") or "{}") if report else {}
    dataset_id = filters.get("dataset_id")
    return dataset_csv(dataset_id) if dataset_id else dataframe_to_csv_bytes(pd.DataFrame(report_rows(report_id)))


def report_xlsx(report_id: int) -> bytes:
    report = report_repository.get_report(report_id)
    if not report:
        return dataset_xlsx(report_id)
    filters = json.loads(report.get("filters_json") or "{}") if report else {}
    dataset_id = filters.get("dataset_id")
    if not dataset_id:
        raise ValueError("Report is not linked to a dataset")
    return dataset_xlsx(dataset_id)


def report_pdf(report_id: int) -> bytes:
    report = report_repository.get_report(report_id)
    if not report:
        return dataset_pdf(report_id)
    filters = json.loads(report.get("filters_json") or "{}")
    dataset_id = filters.get("dataset_id")
    if not dataset_id:
        raise ValueError("Report is not linked to a dataset")
    return _pdf_for_dataset(dataset_id, report["title"])
