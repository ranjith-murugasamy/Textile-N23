"""Re-analyse the 15-run Box-Behnken data: audit the printed Table 4, refit, ANOVA, optimise, bootstrap.
Writes results/metrics.json and results/tables/*.csv. Every number in the manuscript comes from here."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from scipy import stats

import config as C
import rsm
from fetch_data import load, main as fetch_main

CENTRE_IDX = [9, 13, 14]  # runs 10, 14, 15 (0-based)


def printed_predict(resp: str, X: np.ndarray) -> np.ndarray:
    e = C.PRINTED_EQ[resp]
    A, B, Cc = X[:, 0], X[:, 1], X[:, 2]
    return e["b0"] + e["A"] * A + e["B"] * B + e["C"] * Cc + e["AB"] * A * B + e["AC"] * A * Cc + e["BC"] * B * Cc


def desirability_matrix(pred: dict, ranges: dict, goals: dict) -> np.ndarray:
    d = np.ones(len(next(iter(pred.values()))))
    for r in C.RESPONSES:
        lo, hi = ranges[r]
        d = d * rsm.desirability(pred[r], goals[r], lo, hi)
    return d ** (1 / len(C.RESPONSES))


def optimise(betas: dict, grid: np.ndarray, ranges: dict, goals: dict) -> tuple[np.ndarray, float, dict]:
    pred = {r: rsm.predict(betas[r], rsm.TERMS_QUAD, grid) for r in C.RESPONSES}
    D = desirability_matrix(pred, ranges, goals)
    i = int(np.argmax(D))
    return grid[i], float(D[i]), {r: float(pred[r][i]) for r in C.RESPONSES}


def actual(x: np.ndarray) -> dict:
    return {f: float(C.CENTRE[f] + C.HALF[f] * x[j]) for j, f in enumerate(C.FACTORS)}


def clean(o):
    """Replace NaN/inf by None so metrics.json is valid JSON (for example lack of fit when centre runs are identical)."""
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (float, np.floating)) and not np.isfinite(o):
        return None
    return o


def main() -> None:
    fetch_main()
    df = load()
    X = df[[f"x_{f}" for f in C.FACTORS]].to_numpy()
    Y = {r: df[C.COLUMN[r]].to_numpy(float) for r in C.RESPONSES}
    C.TABLES.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(C.SEED)
    M: dict = {"seed": C.SEED, "n_runs": int(len(df)), "n_boot": C.N_BOOT}

    # 1 audit of the equations printed in Table 4 -------------------------------------------------
    audit_rows, fits = [], {}
    for r in C.RESPONSES:
        y = Y[r]
        quad = rsm.fit_ols(X, y, rsm.TERMS_QUAD, CENTRE_IDX)
        fi2 = rsm.fit_ols(X, y, rsm.TERMS_2FI, CENTRE_IDX)
        lin = rsm.fit_ols(X, y, rsm.TERMS_LIN, CENTRE_IDX)
        fits[r] = {"quad": quad, "2fi": fi2, "lin": lin}
        pp = printed_predict(r, X)
        sse_p = float(((y - pp) ** 2).sum())
        sst = quad.sst
        e = C.PRINTED_EQ[r]
        audit_rows.append({
            "response": C.LABEL[r], "R2_reported": e["R2"], "R2_printed_equation_on_data": 1 - sse_p / sst,
            "R2_refit_lin+2FI": fi2.r2, "R2adj_refit_lin+2FI": fi2.r2_adj, "R2pred_refit_lin+2FI": fi2.r2_pred,
            "R2_refit_quadratic": quad.r2, "R2adj_quadratic": quad.r2_adj, "R2pred_quadratic": quad.r2_pred,
            "max_abs_coef_diff_vs_printed(linear+2FI terms)": float(max(
                abs(fi2.beta[rsm.TERMS_2FI.index(k)] - e[k]) for k in ["A", "B", "C", "AB", "AC", "BC"])),
            "intercept_printed": e["b0"], "intercept_refit_2FI": float(fi2.beta[0]),
            "centre_mean": float(y[CENTRE_IDX].mean()),
        })
    audit = pd.DataFrame(audit_rows)
    audit.to_csv(C.TABLES / "table_audit_printed_vs_refit.csv", index=False, float_format="%.4f")
    M["audit"] = {C.RESPONSES[i]: {k: (float(v) if not isinstance(v, str) else v) for k, v in row.items()}
                  for i, row in enumerate(audit_rows)}

    # 2 ANOVA / coefficients of the full quadratic model ------------------------------------------
    anova_rows, coef_rows, adq = [], [], {}
    for r in C.RESPONSES:
        q = fits[r]["quad"]
        anova_rows.append({"response": C.LABEL[r], "F_model": q.f_model, "p_model": q.p_model, "R2": q.r2,
                           "R2_adj": q.r2_adj, "R2_pred": q.r2_pred, "RMSE": q.rmse, "CV_pct": q.cv_pct,
                           "adeq_precision": q.adeq_precision, "LOF_F": q.lof_f, "LOF_p": q.lof_p,
                           "df_model": q.df_model, "df_resid": q.df_res, "pure_error_df": q.pure_error_df,
                           "PRESS": q.press})
        sw = stats.shapiro(q.resid)
        adq[r] = {"F_model": q.f_model, "p_model": q.p_model, "R2": q.r2, "R2_adj": q.r2_adj, "R2_pred": q.r2_pred,
                  "RMSE": q.rmse, "CV_pct": q.cv_pct, "adeq_precision": q.adeq_precision, "LOF_F": q.lof_f,
                  "LOF_p": q.lof_p, "shapiro_p": float(sw.pvalue),
                  "max_leverage": float(q.hat.max()),
                  "n_terms_p<0.05": int(sum(q.p[1:] < C.ALPHA)),
                  "sig_terms": [t for t, p in zip(q.terms, q.p) if t != "1" and p < C.ALPHA]}
        for t, b, se, p, ci in zip(q.terms, q.beta, q.se, q.p, q.ci):
            coef_rows.append({"response": C.LABEL[r], "term": t, "coef": b, "se": se, "p": p, "ci_lo": ci[0], "ci_hi": ci[1]})
    pd.DataFrame(anova_rows).to_csv(C.TABLES / "table_anova_quadratic.csv", index=False, float_format="%.4g")
    pd.DataFrame(coef_rows).to_csv(C.TABLES / "table_coefficients_quadratic.csv", index=False, float_format="%.4f")
    M["adequacy"] = adq
    M["coefficients"] = {r: dict(zip(fits[r]["quad"].terms, map(float, fits[r]["quad"].beta))) for r in C.RESPONSES}
    M["coef_p"] = {r: dict(zip(fits[r]["quad"].terms, map(float, fits[r]["quad"].p))) for r in C.RESPONSES}

    # 2b reduced (backward-eliminated, alpha 0.10, hierarchical) models as a robustness check -----------
    red, red_rows = {}, []
    for r in C.RESPONSES:
        tr = rsm.backward_eliminate(X, Y[r], CENTRE_IDX)
        fr = rsm.fit_ols(X, Y[r], tr, CENTRE_IDX)
        red[r] = (tr, fr)
        red_rows.append({"response": C.LABEL[r], "terms_kept": " ".join(t for t in tr if t != "1"), "n_terms": len(tr) - 1,
                         "R2": fr.r2, "R2_adj": fr.r2_adj, "R2_pred": fr.r2_pred, "RMSE": fr.rmse})
    pd.DataFrame(red_rows).to_csv(C.TABLES / "table_reduced_models.csv", index=False, float_format="%.4f")
    M["reduced"] = {r: {"terms": red[r][0], "R2": red[r][1].r2, "R2_adj": red[r][1].r2_adj, "R2_pred": red[r][1].r2_pred} for r in C.RESPONSES}
    pred_red = {r: rsm.design(grid_r := rsm.grid_points(41), red[r][0]) @ red[r][1].beta for r in C.RESPONSES}
    ranges_r = {r: (float(Y[r].min()), float(Y[r].max())) for r in C.RESPONSES}
    Dr = desirability_matrix(pred_red, ranges_r, C.GOALS)
    ir = int(np.argmax(Dr))
    M["reduced_optimum"] = {"actual": actual(grid_r[ir]), "desirability": float(Dr[ir]),
                            "pred": {r: float(pred_red[r][ir]) for r in C.RESPONSES}}

    # 3 does Table 5 equal the printed-equation prediction at the printed optimum? -------------------
    xopt_paper = np.array([[(C.PAPER_OPT[f] - C.CENTRE[f]) / C.HALF[f] for f in C.FACTORS]])
    chk = {}
    for r in C.RESPONSES:
        chk[r] = {"printed_equation": float(printed_predict(r, xopt_paper)[0]),
                  "quadratic_refit": float(rsm.predict(fits[r]["quad"].beta, rsm.TERMS_QUAD, xopt_paper)[0]),
                  "table5": C.PAPER_TABLE5[r]}
    M["paper_optimum_check"] = chk

    # 4 desirability optimisation ----------------------------------------------------------------------
    grid = rsm.grid_points(41)
    ranges = {r: (float(Y[r].min()), float(Y[r].max())) for r in C.RESPONSES}
    betas = {r: fits[r]["quad"].beta for r in C.RESPONSES}
    scen = {"S1_elong_in_range": C.GOALS, "S2_elong_max": {**C.GOALS, "elongation": "max"}}
    M["optimum"] = {"ranges": ranges}
    boot_store = {}
    resid_scaled = {r: fits[r]["quad"].resid / np.sqrt(1 - fits[r]["quad"].hat) for r in C.RESPONSES}
    resid_scaled = {r: v - v.mean() for r, v in resid_scaled.items()}
    for name, goals in scen.items():
        xo, d, pr = optimise(betas, grid, ranges, goals)
        a = actual(xo)
        # residual bootstrap: refit, re-optimise, record optimum location and predicted responses
        locs, preds, dd = [], {r: [] for r in C.RESPONSES}, []
        for _ in range(C.N_BOOT):
            bb = {}
            for r in C.RESPONSES:
                yb = fits[r]["quad"].fitted + rng.choice(resid_scaled[r], size=len(df), replace=True)
                bb[r] = rsm.fit_ols(X, yb, rsm.TERMS_QUAD).beta
            xb, db, pb = optimise(bb, grid, ranges, goals)
            locs.append(xb); dd.append(db)
            for r in C.RESPONSES:
                preds[r].append(pb[r])
        locs = np.array(locs)
        # prediction-interval half-width at the optimum (analytical, per response)
        m0 = rsm.design(xo[None, :], rsm.TERMS_QUAD)
        pi, ci = {}, {}
        for r in C.RESPONSES:
            q = fits[r]["quad"]
            Md = rsm.design(X, rsm.TERMS_QUAD)
            h0 = float((m0 @ np.linalg.pinv(Md.T @ Md) @ m0.T)[0, 0])
            tc = stats.t.ppf(0.975, q.df_res)
            pi[r] = [pr[r] - tc * q.rmse * np.sqrt(1 + h0), pr[r] + tc * q.rmse * np.sqrt(1 + h0)]
            ci[r] = [pr[r] - tc * q.rmse * np.sqrt(h0), pr[r] + tc * q.rmse * np.sqrt(h0)]
        M["optimum"][name] = {
            "coded": [float(v) for v in xo], "actual": a, "desirability": d, "pred": pr,
            "mean_ci95": ci, "pred_interval95": pi,
            "boot_loc_ci95": {f: [float(np.percentile(C.CENTRE[f] + C.HALF[f] * locs[:, j], 2.5)),
                                  float(np.percentile(C.CENTRE[f] + C.HALF[f] * locs[:, j], 97.5))]
                              for j, f in enumerate(C.FACTORS)},
            "boot_pred_ci95": {r: [float(np.percentile(preds[r], 2.5)), float(np.percentile(preds[r], 97.5))] for r in C.RESPONSES},
            "boot_desirability_ci95": [float(np.percentile(dd, 2.5)), float(np.percentile(dd, 97.5))],
            "boot_frac_blend_at_bound": float(np.mean(np.abs(locs[:, 0]) > 0.999)),
        }
        boot_store[name] = (locs, preds)
    np.savez(C.PROCESSED / "bootstrap.npz", **{f"{n}_loc": v[0] for n, v in boot_store.items()})

    # 5 observed best run, benchmark comparison, blend means -------------------------------------------
    s1 = M["optimum"]["S1_elong_in_range"]
    comp = []
    for r in C.RESPONSES:
        lo, hi = s1["boot_pred_ci95"][r]
        comp.append({"response": C.LABEL[r], "cotton_benchmark_unverified": C.COTTON_BENCH[r],
                     "draft_Table5_blend": C.PAPER_TABLE5[r], "refit_prediction": s1["pred"][r],
                     "refit_bootstrap_ci_lo": lo, "refit_bootstrap_ci_hi": hi,
                     "refit_PI95_lo": s1["pred_interval95"][r][0], "refit_PI95_hi": s1["pred_interval95"][r][1],
                     "best_observed_run": float(Y[r].max() if r in ("tenacity", "elongation") else Y[r].min())})
    pd.DataFrame(comp).to_csv(C.TABLES / "table_optimum_vs_benchmark.csv", index=False, float_format="%.4g")
    M["benchmark_within_PI"] = {r: bool(s1["pred_interval95"][r][0] <= C.COTTON_BENCH[r] <= s1["pred_interval95"][r][1]) for r in C.RESPONSES}

    lev = df.groupby("blend_first_pct")[[C.COLUMN[r] for r in C.RESPONSES]].agg(["mean", "std"])
    lev.columns = [f"{a}_{b}" for a, b in lev.columns]
    lev.reset_index().to_csv(C.TABLES / "table_level_means.csv", index=False, float_format="%.3f")
    M["blend_means"] = {int(k): {r: float(v[C.COLUMN[r]]) for r in C.RESPONSES} for k, v in df.groupby("blend_first_pct")[[C.COLUMN[r] for r in C.RESPONSES]].mean().iterrows()}
    # centre-run repeatability (3 runs)
    M["centre_sd"] = {r: float(Y[r][CENTRE_IDX].std(ddof=1)) for r in C.RESPONSES}
    M["centre_mean"] = {r: float(Y[r][CENTRE_IDX].mean()) for r in C.RESPONSES}
    # Blend-effect size: 70 vs 30 share, tenacity and hairiness, Welch t on the 4 runs at each level + effect from model
    for r in C.RESPONSES:
        q = fits[r]["quad"]
        M.setdefault("blend_effect_70_vs_30", {})[r] = {"effect": float(2 * q.beta[1]),
            "ci": [float(2 * q.ci[1][0]), float(2 * q.ci[1][1])], "p": float(q.p[1])}
    # design table and run table
    df.drop(columns=["blend", "roller", "rotor"]).to_csv(C.TABLES / "table_design_runs.csv", index=False)
    # predicted vs observed + LOO table
    pv = {"run": df["run"]}
    for r in C.RESPONSES:
        q = fits[r]["quad"]
        pv[f"{r}_obs"] = Y[r]; pv[f"{r}_fit"] = q.fitted; pv[f"{r}_loo"] = Y[r] - q.resid / (1 - q.hat)
    pd.DataFrame(pv).to_csv(C.TABLES / "table_predicted_vs_observed.csv", index=False, float_format="%.4f")

    # Table-3 internal consistency flags
    M["data_checks"] = {
        "tenacity_vs_hairiness_corr": float(np.corrcoef(Y["tenacity"], Y["hairiness"])[0, 1]),
        "u_vs_imperfections_corr": float(np.corrcoef(Y["u_pct"], Y["imperfections"])[0, 1]),
        "tenacity_vs_elongation_corr": float(np.corrcoef(Y["tenacity"], Y["elongation"])[0, 1]),
        "hairiness_range": [float(Y["hairiness"].min()), float(Y["hairiness"].max())],
        "cotton_benchmark_hairiness_inside_observed_range": bool(Y["hairiness"].min() <= C.COTTON_BENCH["hairiness"] <= Y["hairiness"].max()),
    }
    sd_q = {r: adq[r] for r in C.RESPONSES}
    M["headline"] = {
        "Runs (3 centre replicates)": len(df),
        "R2 reported (tenacity, draft)": C.PRINTED_EQ["tenacity"]["R2"],
        "R2 printed eq. on data (tenacity)": float(audit_rows[0]["R2_printed_equation_on_data"]),
        "R2 lin+2FI refit (tenacity)": float(audit_rows[0]["R2_refit_lin+2FI"]),
        "R2 quadratic (tenacity)": sd_q["tenacity"]["R2"],
        "R2 predicted, quadratic (tenacity)": sd_q["tenacity"]["R2_pred"],
        "Blend share at optimum (%)": s1["actual"]["blend"],
        "Opening roller at optimum (rpm)": s1["actual"]["roller"],
        "Rotor speed at optimum (rpm)": s1["actual"]["rotor"],
        "Composite desirability": s1["desirability"],
        "Predicted tenacity at optimum (cN/tex)": s1["pred"]["tenacity"],
    }
    (C.RESULTS / "metrics.json").write_text(json.dumps(clean(M), indent=2, default=float))
    print("wrote metrics.json")


if __name__ == "__main__":
    main()
