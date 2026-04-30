RISK_LEVELS = [
    ("LOW", 0.0, 0.3, "#22c55e", "Continue monitoring."),
    ("MEDIUM", 0.3, 0.6, "#f59e0b", "Review module and add targeted tests."),
    ("HIGH", 0.6, 0.8, "#f97316", "Require code review and increase test coverage."),
    ("CRITICAL", 0.8, 1.000001, "#dc2626", "Immediate QA inspection and refactoring recommended."),
]


def classify_risk(probability: float) -> dict:
    value = max(0.0, min(1.0, float(probability)))
    for name, min_p, max_p, color, action in RISK_LEVELS:
        if min_p <= value < max_p:
            return {
                "name": name,
                "min_probability": min_p,
                "max_probability": max_p,
                "color": color,
                "suggested_action": action,
            }
    name, min_p, max_p, color, action = RISK_LEVELS[-1]
    return {"name": name, "min_probability": min_p, "max_probability": max_p, "color": color, "suggested_action": action}


def rule_based_probability(loc: float, complexity: float, coupling: float, code_churn: float) -> float:
    loc_score = min(float(loc) / 1500.0, 1.0)
    complexity_score = min(float(complexity) / 80.0, 1.0)
    coupling_score = min(float(coupling) / 35.0, 1.0)
    churn_score = min(float(code_churn) / 420.0, 1.0)
    score = loc_score * 0.25 + complexity_score * 0.30 + coupling_score * 0.20 + churn_score * 0.25
    return round(max(0.01, min(0.99, score)), 4)


def prediction_label(probability: float) -> str:
    value = float(probability)
    if value < 0.3:
        return "No Defect"
    if value < 0.6:
        return "Possible Defect"
    return "Defect"
