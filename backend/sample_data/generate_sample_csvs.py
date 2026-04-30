from __future__ import annotations

import math
import random
from pathlib import Path

import pandas as pd


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def make_modules() -> list[dict]:
    """
    Create a realistic set of module "families":
    - core/auth/payment/db/gateway: typically larger + higher churn/coupling
    - ui/utils: smaller + lower risk
    """
    families = [
        ("core.auth", 1.35),
        ("core.payment", 1.45),
        ("core.db", 1.50),
        ("gateway.api", 1.25),
        ("services.billing", 1.20),
        ("workers.notifications", 1.10),
        ("reports.export", 1.05),
        ("ui.components", 0.85),
        ("utils.formatters", 0.75),
        ("infra.cache", 1.00),
    ]
    mods = []
    for fam, mult in families:
        for i in range(1, 41):
            mods.append({"module_name": f"{fam}.module_{i:02d}", "risk_multiplier": mult})
    return mods


def synth_row(mod: dict, rng: random.Random, labeled: bool) -> dict:
    mult = float(mod["risk_multiplier"])

    # Base metrics (scale by family)
    loc = int(rng.triangular(60, 420, 140) * mult)
    loc = max(loc, 20)
    cloc = int(clamp(loc * rng.uniform(0.05, 0.22), 0, loc * 0.6))
    ncloc = max(loc - cloc, 1)

    complexity = clamp(rng.triangular(1, 35, 8) * (0.8 + 0.5 * mult), 0, 120)
    cyclo = clamp(complexity * rng.uniform(0.9, 1.2), 0, 160)
    depth = clamp(rng.triangular(1, 14, 4) * (0.85 + 0.35 * mult), 0, 40)
    ifc = clamp(rng.triangular(0, 40, 8) * (0.9 + 0.4 * mult), 0, 120)

    coupling = clamp(rng.triangular(1, 18, 5) * (0.8 + 0.55 * mult), 0, 60)
    cohesion = clamp(rng.triangular(0.25, 0.95, 0.65) - (mult - 1.0) * 0.12, 0.05, 0.98)

    backlog = clamp(rng.triangular(0, 18, 4) * (0.75 + 0.65 * mult), 0, 60)
    effort = clamp(rng.triangular(0, 40, 8) * (0.70 + 0.75 * mult), 0, 120)
    churn = clamp(rng.triangular(2, 220, 40) * (0.75 + 0.65 * mult), 0, 600)
    # Prefer a churn signal influenced by backlog/effort
    churn = churn + backlog * 2.2 + effort * 0.6

    percent_reused = clamp(rng.triangular(0.0, 0.7, 0.15), 0.0, 0.95)

    # A measurement-like probability to derive defect_count/label (NOT random noise)
    loc_score = min(loc / 1600.0, 1.0)
    comp_score = min((cyclo + ifc * 0.4 + depth * 1.2) / 180.0, 1.0)
    coup_score = min(coupling / 45.0, 1.0)
    churn_score = min(churn / 520.0, 1.0)
    cohesion_bonus = min(cohesion, 1.0) * 0.25
    reused_bonus = min(percent_reused, 1.0) * 0.10

    # Slightly higher sensitivity to complexity/churn for labeled training data realism
    base_prob = (
        0.22 * loc_score
        + 0.34 * comp_score
        + 0.20 * coup_score
        + 0.26 * churn_score
        - 0.10 * cohesion_bonus
        - 0.06 * reused_bonus
    )
    base_prob = clamp(base_prob, 0.01, 0.99)

    # Keep labels correlated with measurement risk but noisy enough to avoid a trivially separable dataset.
    kloc = loc / 1000.0
    expected = base_prob * (0.5 + 1.8 * kloc) * 1.5
    defect_count = int(round(max(0.0, expected + rng.gauss(0, 0.9))))
    defect_count = int(clamp(defect_count, 0, 12))
    label_prob = clamp(0.08 + 0.78 * base_prob + rng.uniform(-0.12, 0.12), 0.03, 0.92)
    defect_label = 1 if rng.random() < label_prob else 0
    if defect_label and defect_count == 0 and rng.random() < 0.65:
        defect_count = 1

    row = {
        "module_name": mod["module_name"],
        "loc": loc,
        "ncloc": ncloc,
        "cloc": cloc,
        "complexity": round(float(complexity), 3),
        "cyclomatic_complexity": round(float(cyclo), 3),
        "depth_of_nesting": round(float(depth), 3),
        "coupling": round(float(coupling), 3),
        "cohesion": round(float(cohesion), 3),
        "information_flow_complexity": round(float(ifc), 3),
        "code_churn": round(float(churn), 3),
        "change_request_backlog": round(float(backlog), 3),
        "pending_effort_hours": round(float(effort), 3),
        "percent_reused": round(float(percent_reused), 3),
    }

    if labeled:
        row["defect_count"] = defect_count
        row["defect_label"] = defect_label
    return row


def generate(train_rows: int = 300, predict_rows: int = 100, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = random.Random(seed)
    modules = make_modules()

    train = [synth_row(modules[rng.randrange(len(modules))], rng, labeled=True) for _ in range(train_rows)]
    # Ensure both classes exist (required by training endpoint)
    df_train = pd.DataFrame(train)
    if "defect_label" in df_train.columns:
        score_cols = ["code_churn", "coupling", "cyclomatic_complexity", "loc"]
        positive_rate = float(df_train["defect_label"].mean())
        if df_train["defect_label"].nunique() < 2 or positive_rate < 0.25:
            df_train = df_train.sort_values(by=score_cols, ascending=False).reset_index(drop=True)
            flip_n = max(45, int(len(df_train) * 0.28))
            df_train.loc[: flip_n - 1, "defect_label"] = 1
            df_train.loc[: flip_n - 1, "defect_count"] = df_train.loc[: flip_n - 1, "defect_count"].fillna(0).astype(int).clip(lower=1)
        if float(df_train["defect_label"].mean()) > 0.75:
            df_train = df_train.sort_values(by=score_cols, ascending=True).reset_index(drop=True)
            flip_n = max(45, int(len(df_train) * 0.28))
            df_train.loc[: flip_n - 1, "defect_label"] = 0
            df_train.loc[: flip_n - 1, "defect_count"] = 0
    train = df_train.to_dict(orient="records")
    predict = [synth_row(modules[rng.randrange(len(modules))], rng, labeled=False) for _ in range(predict_rows)]

    return pd.DataFrame(train), pd.DataFrame(predict)


def main():
    train_df, predict_df = generate()
    out_dir = Path(__file__).resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)

    train_path = out_dir / "train_defect_dataset.csv"
    predict_path = out_dir / "predict_only_dataset.csv"
    prediction_only_path = out_dir / "prediction_only_dataset.csv"
    rubric_train_path = out_dir / "defect_metrics_dataset.csv"

    train_df.to_csv(train_path, index=False, encoding="utf-8-sig")
    train_df.to_csv(rubric_train_path, index=False, encoding="utf-8-sig")
    predict_df.to_csv(predict_path, index=False, encoding="utf-8-sig")
    predict_df.to_csv(prediction_only_path, index=False, encoding="utf-8-sig")

    print(f"Wrote: {train_path} ({len(train_df)} rows)")
    print(f"Wrote: {rubric_train_path} ({len(train_df)} rows)")
    print(f"Wrote: {predict_path} ({len(predict_df)} rows)")
    print(f"Wrote: {prediction_only_path} ({len(predict_df)} rows)")


if __name__ == "__main__":
    main()
