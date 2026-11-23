"""Response-surface helpers: design matrices, OLS with ANOVA, PRESS, lack of fit, desirability."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

TERMS_QUAD = ["1", "A", "B", "C", "AB", "AC", "BC", "A2", "B2", "C2"]
TERMS_2FI = ["1", "A", "B", "C", "AB", "AC", "BC"]
TERMS_LIN = ["1", "A", "B", "C"]


def design(X: np.ndarray, terms: list[str]) -> np.ndarray:
    """Model matrix for coded factors X (n x 3) with columns A, B, C."""
    A, B, C = X[:, 0], X[:, 1], X[:, 2]
    lib = {"1": np.ones(len(X)), "A": A, "B": B, "C": C, "AB": A * B, "AC": A * C, "BC": B * C,
           "A2": A * A, "B2": B * B, "C2": C * C}
    return np.column_stack([lib[t] for t in terms])


@dataclass
class Fit:
    terms: list[str]
    beta: np.ndarray
    se: np.ndarray
    t: np.ndarray
    p: np.ndarray
    ci: np.ndarray
    r2: float
    r2_adj: float
    r2_pred: float
    press: float
    sse: float
    sst: float
    df_res: int
    df_model: int
    f_model: float
    p_model: float
    resid: np.ndarray
    fitted: np.ndarray
    hat: np.ndarray
    rmse: float
    adeq_precision: float
    lof_f: float
    lof_p: float
    pure_error_df: int
    cv_pct: float


def fit_ols(X: np.ndarray, y: np.ndarray, terms: list[str], centre_idx: list[int] | None = None) -> Fit:
    """Ordinary least squares with the usual ANOVA statistics. centre_idx marks replicated centre runs."""
    M = design(X, terms)
    n, k = M.shape
    XtXi = np.linalg.pinv(M.T @ M)
    beta = XtXi @ M.T @ y
    fitted = M @ beta
    resid = y - fitted
    sse = float(resid @ resid)
    sst = float(((y - y.mean()) ** 2).sum())
    df_res = n - k
    mse = sse / df_res if df_res > 0 else np.nan
    se = np.sqrt(np.diag(XtXi) * mse)
    t = beta / se
    p = 2 * stats.t.sf(np.abs(t), df_res)
    tcrit = stats.t.ppf(0.975, df_res)
    ci = np.column_stack([beta - tcrit * se, beta + tcrit * se])
    hat = np.einsum("ij,jk,ik->i", M, XtXi, M)
    press = float(((resid / (1 - hat)) ** 2).sum())
    ssm = sst - sse
    dfm = k - 1
    f_model = (ssm / dfm) / mse
    p_model = float(stats.f.sf(f_model, dfm, df_res))
    # lack of fit from replicated centre runs
    lof_f = lof_p = np.nan
    pe_df = 0
    if centre_idx and len(centre_idx) > 1:
        yc = y[centre_idx]
        ss_pe = float(((yc - yc.mean()) ** 2).sum())
        pe_df = len(centre_idx) - 1
        ss_lof, df_lof = sse - ss_pe, df_res - pe_df
        if df_lof > 0 and ss_pe > 0:
            lof_f = (ss_lof / df_lof) / (ss_pe / pe_df)
            lof_p = float(stats.f.sf(lof_f, df_lof, pe_df))
    sig = (fitted.max() - fitted.min()) / np.sqrt(mse * k / n) if mse > 0 else np.nan
    return Fit(terms, beta, se, t, p, ci, 1 - sse / sst, 1 - (sse / df_res) / (sst / (n - 1)) if df_res > 0 else np.nan,
               1 - press / sst, press, sse, sst, df_res, dfm, float(f_model), p_model, resid, fitted, hat,
               float(np.sqrt(mse)), float(sig), float(lof_f), float(lof_p), pe_df, float(100 * np.sqrt(mse) / y.mean()))


def predict(beta: np.ndarray, terms: list[str], X: np.ndarray) -> np.ndarray:
    """Predict from coefficients at coded points X."""
    return design(np.atleast_2d(X), terms) @ beta


def desirability(y: np.ndarray, goal: str, lo: float, hi: float) -> np.ndarray:
    """Derringer-Suich one-sided/range desirability, weight 1. lo/hi are the observed response range."""
    y = np.asarray(y, dtype=float)
    if goal == "max":
        return np.clip((y - lo) / (hi - lo), 0, 1)
    if goal == "min":
        return np.clip((hi - y) / (hi - lo), 0, 1)
    if goal == "range":
        return ((y >= lo) & (y <= hi)).astype(float)
    raise ValueError(goal)


def grid_points(n: int = 41) -> np.ndarray:
    """Regular grid over the coded cube [-1, 1]^3."""
    g = np.linspace(-1, 1, n)
    return np.array(np.meshgrid(g, g, g, indexing="ij")).reshape(3, -1).T


def backward_eliminate(X: np.ndarray, y: np.ndarray, centre_idx: list[int] | None = None, alpha: float = 0.10) -> list[str]:
    """Backward elimination of the least significant term (p > alpha) from the full quadratic model, keeping hierarchy:
    a linear term stays while any interaction or square containing it stays."""
    terms = list(TERMS_QUAD)
    while True:
        fit = fit_ols(X, y, terms, centre_idx)
        cand = []
        for t, p in zip(fit.terms, fit.p):
            if t == "1" or p <= alpha:
                continue
            if len(t) == 1 and any(len(u) > 1 and t in u for u in terms):
                continue
            cand.append((p, t))
        if not cand:
            return terms
        terms.remove(max(cand)[1])
