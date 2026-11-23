"""Pipeline tests: data integrity, OLS against a closed form, metrics.json contract."""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import config as C  # noqa: E402
import rsm  # noqa: E402
from fetch_data import load  # noqa: E402


def test_design_is_box_behnken():
    df = load()
    X = df[[f"x_{f}" for f in C.FACTORS]].to_numpy()
    assert len(df) == 15 and np.abs(X).max() == 1
    assert int((np.abs(X).sum(axis=1) == 2).sum()) == 12  # edge midpoints, no corners
    assert int((X == 0).all(axis=1).sum()) == 3  # centre replicates


def test_ols_recovers_known_coefficients():
    df = load()
    X = df[[f"x_{f}" for f in C.FACTORS]].to_numpy()
    y = 2 + 3 * X[:, 0] - X[:, 1] + 0.5 * X[:, 0] * X[:, 2] + 0.7 * X[:, 2] ** 2
    fit = rsm.fit_ols(X, y, rsm.TERMS_QUAD)
    assert np.allclose(fit.beta[[0, 1, 2, 5, 9]], [2, 3, -1, 0.5, 0.7], atol=1e-9)
    assert fit.r2 > 0.999999


def test_desirability_bounds():
    d = rsm.desirability(np.array([0.0, 5.0, 10.0]), "max", 0.0, 10.0)
    assert d.tolist() == [0.0, 0.5, 1.0]


def test_metrics_contract():
    m = json.loads((C.RESULTS / "metrics.json").read_text())
    assert set(m["headline"]) and m["n_runs"] == 15
    assert 0 <= m["optimum"]["S1_elong_in_range"]["desirability"] <= 1
    for r in C.RESPONSES:
        assert m["adequacy"][r]["R2"] >= m["adequacy"][r]["R2_adj"] >= m["adequacy"][r]["R2_pred"]
