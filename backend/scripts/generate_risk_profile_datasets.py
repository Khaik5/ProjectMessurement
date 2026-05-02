from __future__ import annotations

import random
from pathlib import Path

import pandas as pd

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "sample_data" / "diagnostics"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _bounded(value: float, minimum: float, maximum: float) -> float:
    return round(max(minimum, min(maximum, value)), 3)


def _row(idx: int, profile: str, rng: random.Random) -> dict:
    if profile == "low":
        defect_label = 1 if rng.random() < 0.10 else 0
        loc = rng.randint(80, 800)
        complexity = rng.uniform(2, 18) + defect_label * rng.uniform(2, 5)
        cyclomatic = rng.uniform(2, 20) + defect_label * rng.uniform(1, 4)
        nesting = rng.uniform(1, 6)
        coupling = rng.uniform(1, 8) + defect_label * rng.uniform(1, 3)
        cohesion = rng.uniform(0.70, 0.95) - defect_label * rng.uniform(0.05, 0.12)
        ifc = rng.uniform(1, 20)
        churn = rng.uniform(0, 80) + defect_label * rng.uniform(15, 40)
        backlog = rng.uniform(0, 6) + defect_label * rng.uniform(0, 2)
        effort = rng.uniform(0, 20) + defect_label * rng.uniform(2, 8)
        reuse = rng.uniform(0.45, 0.90) - defect_label * rng.uniform(0.05, 0.12)
        defect_count = 1 if defect_label and rng.random() < 0.65 else 0
    elif profile == "medium":
        defect_label = 1 if rng.random() < 0.35 else 0
        loc = rng.randint(250, 1800)
        complexity = rng.uniform(8, 45) + defect_label * rng.uniform(4, 12)
        cyclomatic = rng.uniform(8, 50) + defect_label * rng.uniform(4, 12)
        nesting = rng.uniform(2, 12)
        coupling = rng.uniform(4, 22) + defect_label * rng.uniform(2, 6)
        cohesion = rng.uniform(0.45, 0.82) - defect_label * rng.uniform(0.04, 0.10)
        ifc = rng.uniform(5, 55)
        churn = rng.uniform(40, 260) + defect_label * rng.uniform(40, 120)
        backlog = rng.uniform(1, 20) + defect_label * rng.uniform(2, 8)
        effort = rng.uniform(8, 80) + defect_label * rng.uniform(8, 30)
        reuse = rng.uniform(0.25, 0.72) - defect_label * rng.uniform(0.03, 0.10)
        defect_count = rng.choice([0, 0, 1, 1, 2]) if defect_label else rng.choice([0, 0, 0, 1])
    else:
        defect_label = 1 if rng.random() < 0.70 else 0
        loc = rng.randint(900, 4200)
        complexity = rng.uniform(35, 120) + defect_label * rng.uniform(5, 20)
        cyclomatic = rng.uniform(35, 140) + defect_label * rng.uniform(5, 22)
        nesting = rng.uniform(8, 28)
        coupling = rng.uniform(16, 55) + defect_label * rng.uniform(2, 10)
        cohesion = rng.uniform(0.15, 0.58) - defect_label * rng.uniform(0.02, 0.08)
        ifc = rng.uniform(40, 160)
        churn = rng.uniform(250, 1200) + defect_label * rng.uniform(80, 250)
        backlog = rng.uniform(12, 80) + defect_label * rng.uniform(6, 24)
        effort = rng.uniform(70, 360) + defect_label * rng.uniform(30, 110)
        reuse = rng.uniform(0.02, 0.42) - defect_label * rng.uniform(0.02, 0.08)
        defect_count = rng.choice([1, 2, 3, 4, 5]) if defect_label else rng.choice([0, 0, 1])

    cloc = int(loc * rng.uniform(0.08, 0.22))
    return {
        "module_name": f"{profile}_module_{idx:03d}",
        "loc": loc,
        "ncloc": max(0, loc - cloc),
        "cloc": cloc,
        "complexity": round(complexity, 3),
        "cyclomatic_complexity": round(cyclomatic, 3),
        "depth_of_nesting": round(nesting, 3),
        "coupling": round(coupling, 3),
        "cohesion": _bounded(cohesion, 0.02, 0.98),
        "information_flow_complexity": round(ifc, 3),
        "code_churn": round(churn, 3),
        "change_request_backlog": round(backlog, 3),
        "pending_effort_hours": round(effort, 3),
        "percent_reused": _bounded(reuse, 0.0, 0.95),
        "defect_count": defect_count,
        "defect_label": defect_label,
    }


def generate(profile: str, filename: str, rows: int = 200, seed: int = 20260502) -> Path:
    offsets = {"low": 101, "medium": 202, "high": 303}
    rng = random.Random(seed + offsets[profile])
    df = pd.DataFrame([_row(idx, profile, rng) for idx in range(1, rows + 1)])
    path = OUTPUT_DIR / filename
    df.to_csv(path, index=False)
    return path


def main() -> None:
    files = [
        generate("low", "low_risk_clean_project.csv"),
        generate("medium", "medium_risk_mixed_project.csv"),
        generate("high", "high_risk_legacy_project.csv"),
    ]
    for path in files:
        print(path)


if __name__ == "__main__":
    main()
