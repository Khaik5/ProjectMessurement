import pandas as pd

from app.ml.feature_engineering import P7_FEATURE_COLUMNS, build_p7_features


def test_missing_optional_columns_and_loc_zero_do_not_crash():
    features = build_p7_features(
        [{"module_name": "zero_loc", "loc": 0, "complexity": 0, "coupling": 0, "code_churn": 0}]
    )

    assert list(features.reindex(columns=P7_FEATURE_COLUMNS).columns) == P7_FEATURE_COLUMNS
    assert features.loc[0, "kloc"] == 0
    assert features.loc[0, "comment_ratio"] == 0
    assert 0 <= features.loc[0, "risk_score"] <= 1
    assert features.attrs["warnings"]


def test_ratio_and_percent_inputs_are_normalized_consistently():
    features = build_p7_features(
        pd.DataFrame(
            [
                {
                    "module_name": "ratio",
                    "loc": 100,
                    "complexity": 10,
                    "coupling": 5,
                    "code_churn": 10,
                    "cohesion": 0.8,
                    "percent_reused": 0.5,
                },
                {
                    "module_name": "percent",
                    "loc": 100,
                    "complexity": 10,
                    "coupling": 5,
                    "code_churn": 10,
                    "cohesion": 80,
                    "percent_reused": 50,
                },
            ]
        )
    )

    assert features.loc[0, "cohesion"] == features.loc[1, "cohesion"] == 0.8
    assert features.loc[0, "percent_reused"] == features.loc[1, "percent_reused"] == 0.5
    assert features.loc[0, "cohesion_score"] == features.loc[1, "cohesion_score"] == 0.8
    assert features.loc[0, "reuse_score"] == features.loc[1, "reuse_score"] == 0.5


def test_defect_label_and_defect_count_do_not_leak_by_default():
    row = {
        "module_name": "leak_check",
        "loc": 1000,
        "complexity": 20,
        "coupling": 8,
        "code_churn": 50,
        "defect_label": 1,
        "defect_count": 10,
    }

    safe = build_p7_features([row], use_label_density=False)
    label_density = build_p7_features([row], use_label_density=True)
    count_density = build_p7_features([row], use_defect_count_density=True)

    assert safe.loc[0, "defect_density"] == 0
    assert label_density.loc[0, "defect_density"] == 1
    assert count_density.loc[0, "defect_density"] == 10
