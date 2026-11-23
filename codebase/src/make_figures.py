"""Draw every figure from results/metrics.json and the tables; explanations quote metrics.json values."""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

import config as C
import rsm
from fetch_data import load
from figure_helpers import save_figure, save_metrics_png, style

OKABE = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9", "#F0E442", "#000000"]
SHORT = {"tenacity": "Tenacity", "elongation": "Elongation", "u_pct": "U%", "imperfections": "Imperfections", "hairiness": "Hairiness"}


def fits_all(df):
    X = df[[f"x_{f}" for f in C.FACTORS]].to_numpy()
    out = {}
    for r in C.RESPONSES:
        y = df[C.COLUMN[r]].to_numpy(float)
        out[r] = rsm.fit_ols(X, y, rsm.TERMS_QUAD, [9, 13, 14])
    return X, out


def main() -> None:
    style()
    M = json.loads((C.RESULTS / "metrics.json").read_text())
    df = load()
    X, F = fits_all(df)
    ad, au = M["adequacy"], M["audit"]
    s1 = M["optimum"]["S1_elong_in_range"]

    # 1 design space ------------------------------------------------------------------------------
    fig = plt.figure(figsize=(7.2, 3.2))
    ax = fig.add_subplot(1, 2, 1, projection="3d")
    cen = df["run"].isin([10, 14, 15])
    ax.scatter(df.x_blend[~cen], df.x_roller[~cen], df.x_rotor[~cen], c=OKABE[0], s=28, label="Edge runs (12)")
    ax.scatter(df.x_blend[cen], df.x_roller[cen], df.x_rotor[cen], c=OKABE[3], s=40, marker="D", label="Centre replicates (3)")
    ax.set_xlabel("Blend (coded)"); ax.set_ylabel("Roller (coded)"); ax.set_zlabel("Rotor (coded)")
    ax.legend(loc="upper left", fontsize=7)
    ax2 = fig.add_subplot(1, 2, 2)
    for lvl, col in zip([30, 50, 70], OKABE[:3]):
        sub = df[df.blend_first_pct == lvl]
        ax2.scatter(sub.tenacity_cN_tex, sub.hairiness_index, c=col, s=34, label=f"{lvl}:{100-lvl}")
    ax2.set_xlabel("Tenacity (cN/tex)"); ax2.set_ylabel("Hairiness index H"); ax2.legend(title="Blend label", fontsize=7)
    corr = M["data_checks"]["tenacity_vs_hairiness_corr"]
    save_figure(fig, "fig_01_design_and_tradeoff",
                "Left: the 15 Box-Behnken runs in coded factor space, twelve edge-midpoint runs and three centre replicates. Right: observed tenacity against hairiness for every run, coloured by the printed blend label.",
                f"Tenacity and hairiness are almost perfectly anti-correlated across the 15 runs (Pearson r = {corr:.3f}); the 70:30 label gives the strongest and least hairy yarns, the 30:70 label the weakest and hairiest.",
                "Read the left panel as the geometry of the design: no run sits at a corner of the cube. In the right panel, each dot is one yarn; points lower right are better (stronger, less hairy).")

    # 2 predicted vs observed ----------------------------------------------------------------------
    fig, axs = plt.subplots(1, 5, figsize=(7.4, 2.0))
    for ax, r in zip(axs, C.RESPONSES):
        y = df[C.COLUMN[r]].to_numpy(float); q = F[r]
        loo = y - q.resid / (1 - q.hat)
        lo, hi = min(y.min(), loo.min()), max(y.max(), loo.max())
        ax.plot([lo, hi], [lo, hi], c="grey", lw=0.8)
        ax.scatter(y, q.fitted, s=12, c=OKABE[0], label="fitted")
        ax.scatter(y, loo, s=12, c=OKABE[1], marker="x", label="leave-one-out")
        ax.set_title(f"{SHORT[r]}\nR$^2_{{pred}}$={ad[r]['R2_pred']:.2f}", fontsize=7)
        ax.set_xlabel("Observed", fontsize=7); ax.tick_params(labelsize=6)
    axs[0].set_ylabel("Predicted", fontsize=7); axs[0].legend(fontsize=5)
    worst = min(C.RESPONSES, key=lambda r: ad[r]["R2_pred"])
    save_figure(fig, "fig_02_predicted_vs_observed",
                "Observed against predicted yarn properties for the full quadratic model: blue circles are fitted values, orange crosses are leave-one-out predictions that leave each run out of the fit.",
                f"Fitted points hug the diagonal (R2 = {ad['tenacity']['R2']:.3f} for tenacity) but leave-one-out points scatter: predicted R2 is {ad['tenacity']['R2_pred']:.2f} for tenacity and {ad[worst]['R2_pred']:.2f} for {SHORT[worst]}, so the models describe these 15 runs better than they would predict a new one.",
                "A perfect model puts every point on the grey line. Distance of the crosses from the line is the honest estimate of error on a run the model has not seen.")

    # 3 residual diagnostics ------------------------------------------------------------------------
    fig, axs = plt.subplots(1, 2, figsize=(6.4, 2.6))
    for r, col in zip(C.RESPONSES, OKABE):
        q = F[r]; sres = q.resid / (q.rmse * np.sqrt(1 - q.hat))
        axs[0].scatter(q.fitted / q.fitted.mean(), sres, s=14, c=col, label=SHORT[r])
        (osm, osr), _ = stats.probplot(sres, dist="norm")[:2]
        axs[1].scatter(osm, osr, s=14, c=col)
    axs[0].axhline(0, c="grey", lw=0.8); axs[0].set_xlabel("Fitted / mean fitted (-)"); axs[0].set_ylabel("Studentised residual (-)")
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, fontsize=6, ncol=5, loc="lower center", bbox_to_anchor=(0.5, -0.08))
    axs[1].plot([-2, 2], [-2, 2], c="grey", lw=0.8); axs[1].set_xlabel("Normal quantile (-)"); axs[1].set_ylabel("Studentised residual (-)")
    minp = min(ad[r]["shapiro_p"] for r in C.RESPONSES)
    save_figure(fig, "fig_03_residual_diagnostics",
                "Studentised residuals of the five quadratic models against fitted value (left, scaled to each response mean) and against normal quantiles (right).",
                f"No response departs from normality by the Shapiro-Wilk test (smallest p = {minp:.2f}) and no single trend is obvious in the residual plot (a visual judgement), but with only {M['n_runs']} runs and five residual degrees of freedom per model these checks have little power.",
                "Residuals should scatter randomly around zero on the left and follow the grey line on the right. Departures would indicate a missing term or non-constant variance.")

    # 4 audit: R2 reported vs printed vs refit -----------------------------------------------------
    fig, ax = plt.subplots(figsize=(7.0, 3.0))
    w = 0.16; xs = np.arange(5)
    series = [("Reported in draft Table 4", [au[r]["R2_reported"] for r in C.RESPONSES], OKABE[7]),
              ("Printed equation applied to Table 3", [au[r]["R2_printed_equation_on_data"] for r in C.RESPONSES], OKABE[3]),
              ("Refit linear + 2FI", [au[r]["R2_refit_lin+2FI"] for r in C.RESPONSES], OKABE[1]),
              ("Refit full quadratic", [au[r]["R2_refit_quadratic"] for r in C.RESPONSES], OKABE[0]),
              ("Quadratic, predicted R$^2$", [au[r]["R2pred_quadratic"] for r in C.RESPONSES], OKABE[2])]
    for i, (lab, v, col) in enumerate(series):
        ax.bar(xs + (i - 2) * w, v, w, label=lab, color=col)
    ax.axhline(0, c="k", lw=0.6)
    ax.set_xticks(xs); ax.set_xticklabels([SHORT[r] for r in C.RESPONSES]); ax.set_ylabel("Coefficient of determination (-)")
    ax.legend(fontsize=6, ncol=2, loc="lower left")
    save_figure(fig, "fig_04_model_audit",
                "Five versions of R-squared for each response: the value printed in the draft, the R-squared obtained by applying the printed Table 4 equation to the Table 3 data, and refits with linear plus two-factor terms, the full quadratic model, and the leave-one-out predicted R-squared of the quadratic model.",
                f"For tenacity the printed equation reproduces only R2 = {au['tenacity']['R2_printed_equation_on_data']:.2f} of the variance against the {au['tenacity']['R2_reported']:.2f} reported; the linear + 2FI refit gives {au['tenacity']['R2_refit_lin+2FI']:.3f} and the quadratic refit {au['tenacity']['R2_refit_quadratic']:.3f}, which is close to the reported value, so the reported R2 values most likely came from a quadratic model whose squared terms were left out of the printed equations.",
                "Black bars are what the draft claims. If the other bars are lower, the printed equation does not deliver the claimed fit. Bars of the quadratic model that stay high but whose predicted R2 (green) is low indicate overfitting risk.")

    # 5 coefficient plot ------------------------------------------------------------------------------
    fig, axs = plt.subplots(1, 5, figsize=(7.4, 2.6), sharey=True)
    names = ["A", "B", "C", "AB", "AC", "BC", "A2", "B2", "C2"]
    for ax, r in zip(axs, C.RESPONSES):
        q = F[r]; sd = df[C.COLUMN[r]].std()
        b = q.beta[1:] / sd; lo = q.ci[1:, 0] / sd; hi = q.ci[1:, 1] / sd
        sig = q.p[1:] < C.ALPHA
        ax.errorbar(b, np.arange(9), xerr=[b - lo, hi - b], fmt="none", ecolor="grey", lw=0.8)
        ax.scatter(b, np.arange(9), c=[OKABE[3] if s else OKABE[0] for s in sig], s=14, zorder=3)
        ax.axvline(0, c="k", lw=0.6); ax.set_title(SHORT[r], fontsize=7); ax.tick_params(labelsize=6)
        ax.set_xlabel("Coef. / SD of response", fontsize=6)
    axs[0].set_yticks(range(9)); axs[0].set_yticklabels(["A blend", "B roller", "C rotor", "AB", "AC", "BC", "A$^2$", "B$^2$", "C$^2$"], fontsize=6)
    axs[0].invert_yaxis()
    save_figure(fig, "fig_05_standardised_coefficients",
                "Coded-factor coefficients of the full quadratic models, divided by the standard deviation of each response, with 95% confidence intervals; orange points have p below 0.05.",
                f"The blend term (A) is significant for all five responses; for tenacity the other significant terms are {', '.join(t for t in ad['tenacity']['sig_terms'] if t != 'A')}. For tenacity the blend effect moving from the 30 to the 70 level is {M['blend_effect_70_vs_30']['tenacity']['effect']:.2f} cN/tex (95% CI {M['blend_effect_70_vs_30']['tenacity']['ci'][0]:.2f} to {M['blend_effect_70_vs_30']['tenacity']['ci'][1]:.2f}), while process speeds matter far less.",
                "A bar that crosses zero is not distinguishable from no effect. Longer bars are larger effects once all factors are scaled to the same coded range (-1 to +1).")

    # 6 response surfaces -------------------------------------------------------------------------------
    gx = np.linspace(-1, 1, 41); GA, GB = np.meshgrid(gx, gx)
    fig, axs = plt.subplots(2, 5, figsize=(7.6, 3.4))
    for j, r in enumerate(C.RESPONSES):
        for i, (fac, lab) in enumerate([(1, "Roller"), (2, "Rotor")]):
            pts = np.zeros((GA.size, 3)); pts[:, 0] = GA.ravel(); pts[:, fac] = GB.ravel()
            Z = rsm.predict(F[r].beta, rsm.TERMS_QUAD, pts).reshape(GA.shape)
            cs = axs[i, j].contourf(C.CENTRE["blend"] + 20 * GA, C.CENTRE[C.FACTORS[fac]] / 1000 + C.HALF[C.FACTORS[fac]] / 1000 * GB, Z, 10, cmap="viridis")
            fig.colorbar(cs, ax=axs[i, j], pad=0.02).ax.tick_params(labelsize=5)
            axs[i, j].tick_params(labelsize=6)
            if i == 0: axs[i, j].set_title(SHORT[r], fontsize=7)
            axs[i, j].set_xlabel("Blend share (%)", fontsize=6)
            axs[i, j].set_ylabel("Roller (krpm)" if fac == 1 else "Rotor (krpm)", fontsize=6) if j == 0 else None
    save_figure(fig, "fig_06_response_surfaces",
                "Contour maps of the full quadratic models. Top row: blend share against opening-roller speed with rotor speed held at its centre; bottom row: blend share against rotor speed with the roller at its centre. One column per yarn property.",
                f"Moving the blend label from 30 to 70 changes the fitted tenacity by about {M['blend_effect_70_vs_30']['tenacity']['effect']:.1f} cN/tex and hairiness by {M['blend_effect_70_vs_30']['hairiness']['effect']:.1f} index units, while the speed axes bend the surface only gently, with tenacity peaking near the middle of the roller range (B$^2$ p = {M['coef_p']['tenacity']['B2']:.3f}).",
                "Colour bands are model predictions in the units of each response; closer contours mean a steeper change. Surfaces are fitted from 15 runs and are only valid inside the plotted design region.")

    # 7 optimisation ---------------------------------------------------------------------------------------
    B = np.load(C.PROCESSED / "bootstrap.npz")
    fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.4))
    for ax, j, fac in zip(axs, range(3), C.FACTORS):
        for name, col, lab in [("S1_elong_in_range", OKABE[0], "S1: elongation within range"), ("S2_elong_max", OKABE[1], "S2: elongation maximised")]:
            v = C.CENTRE[fac] + C.HALF[fac] * B[f"{name}_loc"][:, j]
            ax.hist(v, bins=np.linspace(C.CENTRE[fac] - C.HALF[fac], C.CENTRE[fac] + C.HALF[fac], 17), alpha=0.6, color=col, label=lab)
        ax.axvline(C.PAPER_OPT[fac], c="k", ls="--", lw=1, label="Draft optimum")
        ax.set_xlabel(C.FACTOR_LABEL[fac], fontsize=7); ax.tick_params(labelsize=6)
    axs[0].set_ylabel("Bootstrap optima (count of 2000)", fontsize=7); axs[0].legend(fontsize=5)
    fb = s1["boot_frac_blend_at_bound"]
    save_figure(fig, "fig_07_optimum_uncertainty",
                "Distribution of the desirability optimum over 2000 residual-bootstrap refits of the quadratic models, for two goal sets, with the optimum printed in the draft shown as a dashed line.",
                f"The blend optimum sits on the upper bound of the tested range in {100*fb:.1f}% of bootstrap refits (scenario S1), so the data say 'as high as tested', not an interior value such as the draft's {C.PAPER_OPT['blend']:.1f}; roller and rotor optima are broad (95% intervals {s1['boot_loc_ci95']['roller'][0]:.0f}-{s1['boot_loc_ci95']['roller'][1]:.0f} rpm and {s1['boot_loc_ci95']['rotor'][0]:.0f}-{s1['boot_loc_ci95']['rotor'][1]:.0f} rpm).",
                "Each histogram counts where the optimum landed after resampling residuals. A narrow peak means a well-determined optimum; a flat spread means the data cannot place it. The draft's optimum lies inside the spread for roller and rotor.")

    # 8 optimum vs cotton benchmark (with PI) -------------------------------------------------------------------
    fig, axs = plt.subplots(1, 5, figsize=(7.4, 2.2))
    for ax, r in zip(axs, C.RESPONSES):
        p, pi, bci = s1["pred"][r], s1["pred_interval95"][r], s1["boot_pred_ci95"][r]
        ax.errorbar([0], [p], yerr=[[p - pi[0]], [pi[1] - p]], fmt="o", c=OKABE[0], capsize=3, label="Refit prediction, 95% PI")
        ax.scatter([1], [C.PAPER_TABLE5[r]], c=OKABE[1], marker="s", label="Draft Table 5")
        ax.scatter([2], [C.COTTON_BENCH[r]], c=OKABE[3], marker="D", label="Cotton benchmark (source unverified)")
        ax.set_xticks([0, 1, 2]); ax.set_xticklabels(["refit", "Tab. 5", "cotton"], fontsize=6, rotation=30)
        ax.set_title(SHORT[r], fontsize=7); ax.tick_params(axis="y", labelsize=6); ax.set_xlim(-0.6, 2.6)
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, fontsize=6, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.08))
    inside = [SHORT[r] for r in C.RESPONSES if M["benchmark_within_PI"][r]]
    save_figure(fig, "fig_08_optimum_vs_cotton",
                "Predicted properties at the recomputed optimum with 95% prediction intervals, the values printed in draft Table 5 for the blend yarn, and the draft's 100% cotton benchmark. No confirmation run was supplied, so every blue and orange point is a model prediction.",
                f"The 95% prediction interval for tenacity ({s1['pred_interval95']['tenacity'][0]:.1f} to {s1['pred_interval95']['tenacity'][1]:.1f} cN/tex) lies below the cotton benchmark of {C.COTTON_BENCH['tenacity']:.1f}; the benchmark falls inside the interval only for {', '.join(inside) if inside else 'none of the responses'}. The model therefore supports a strength deficit relative to cotton; the benchmark values for U% and imperfections are above the upper end of the intervals, which is consistent with a cleaner blend yarn, but without the benchmark's replicate data this is not a significance test.",
                "Blue dot and bar: refit prediction and where a single new yarn would fall 95% of the time. Orange square: value printed in the draft. Red diamond: benchmark. Overlap of the red diamond with the bar means no model-based evidence of a difference.")

    # 9 level means / blend and responses -------------------------------------------------------------------------
    fig, axs = plt.subplots(1, 5, figsize=(7.4, 2.1))
    for ax, r in zip(axs, C.RESPONSES):
        for k, (lvl, col) in enumerate(zip([30, 50, 70], OKABE[:3])):
            v = df.loc[df.blend_first_pct == lvl, C.COLUMN[r]]
            ax.scatter(np.full(len(v), k) + np.linspace(-0.12, 0.12, len(v)), v, c=col, s=12, alpha=0.8)
            ax.hlines(v.mean(), k - 0.25, k + 0.25, colors="k", lw=1)
        ax.set_xticks([0, 1, 2]); ax.set_xticklabels(["30:70", "50:50", "70:30"], fontsize=6, rotation=30)
        ax.set_title(SHORT[r], fontsize=7); ax.tick_params(axis="y", labelsize=6)
    axs[0].set_ylabel("Observed value", fontsize=7)
    bm = M["blend_means"]
    save_figure(fig, "fig_09_blend_level_results",
                "Observed values of all five responses for each printed blend label, one dot per run (four runs at 30:70 and at 70:30, seven at 50:50 including the three centre replicates), with the mean as a black bar.",
                f"Mean tenacity rises from {bm['30']['tenacity']:.2f} to {bm['50']['tenacity']:.2f} to {bm['70']['tenacity']:.2f} cN/tex and mean hairiness falls from {bm['30']['hairiness']:.2f} to {bm['70']['hairiness']:.2f} across the three labels, whereas mean elongation falls from {bm['30']['elongation']:.2f}% to {bm['70']['elongation']:.2f}%; strength and extensibility pull in opposite directions.",
                "Compare bar heights between columns; the spread of dots inside a column shows the effect of the speed settings at that blend. Which fibre the first number refers to is unresolved in the draft.")

    # 10 centre replicate + lack of fit -------------------------------------------------------------------------------
    fig, axs = plt.subplots(1, 2, figsize=(6.4, 2.5))
    rr = C.RESPONSES
    axs[0].bar(range(5), [ad[r]["RMSE"] / df[C.COLUMN[r]].mean() * 100 for r in rr], color=OKABE[0])
    axs[0].bar(range(5), [M["centre_sd"][r] / M["centre_mean"][r] * 100 for r in rr], width=0.4, color=OKABE[1])
    axs[0].set_xticks(range(5)); axs[0].set_xticklabels([SHORT[r] for r in rr], rotation=30, fontsize=6)
    axs[0].set_ylabel("Relative scatter (% of mean)", fontsize=7)
    axs[0].legend(["Model RMSE (5 df)", "SD of 3 centre runs"], fontsize=6)
    axs[1].bar(range(5), [ad[r]["adeq_precision"] for r in rr], color=OKABE[2]); axs[1].axhline(4, c="k", ls="--", lw=0.8)
    axs[1].set_xticks(range(5)); axs[1].set_xticklabels([SHORT[r] for r in rr], rotation=30, fontsize=6)
    axs[1].set_ylabel("Signal-to-noise ratio (-)", fontsize=7)
    lofp = {r: ad[r]["LOF_p"] for r in rr}
    sigl = [SHORT[r] for r in rr if lofp[r] is not None and lofp[r] < 0.05]
    save_figure(fig, "fig_10_noise_and_lack_of_fit",
                "Left: model residual standard error (blue) against the standard deviation of the three centre replicates (orange), both as percent of the response mean. Right: signal-to-noise ratio of each model; the dashed line is the conventional threshold of 4.",
                f"Signal-to-noise is above 4 for all five models (smallest {min(ad[r]['adeq_precision'] for r in rr):.1f}); the lack-of-fit test is significant (p < 0.05) for {', '.join(sigl) if sigl else 'none'} and undefined for tenacity and elongation because the centre replicates are identical, so pure error is zero.",
                "Centre replicates measure noise alone; a model error far above that suggests a missing term. Only two degrees of freedom support the pure-error estimate, so lack-of-fit p-values are indicative.")

    # 11 predicted effect of printed vs refit equation on tenacity/hairiness surfaces (optimum prediction comparison) ----------------
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    chk = M["paper_optimum_check"]; xs = np.arange(5)
    for i, (key, lab, col) in enumerate([("printed_equation", "Printed Table 4 equation", OKABE[3]), ("quadratic_refit", "Quadratic refit", OKABE[0]), ("table5", "Draft Table 5", OKABE[1])]):
        ax.bar(xs + (i - 1) * 0.26, [chk[r][key] / chk[r]["table5"] for r in C.RESPONSES], 0.26, label=lab, color=col)
    ax.axhline(1, c="k", lw=0.6); ax.set_xticks(xs); ax.set_xticklabels([SHORT[r] for r in C.RESPONSES])
    ax.set_ylabel("Prediction / Table 5 value (-)"); ax.set_ylim(0.8, 1.2); ax.legend(fontsize=6)
    save_figure(fig, "fig_11_table5_provenance",
                "Predictions at the optimum printed in the draft (blend 68.727, roller 4713.754 rpm, rotor 47430.327 rpm) from the printed Table 4 equations and from the quadratic refit, each divided by the value printed in Table 5.",
                f"Table 5 reports tenacity {chk['tenacity']['table5']:.3f} cN/tex; the quadratic refit predicts {chk['tenacity']['quadratic_refit']:.3f} and the printed equation {chk['tenacity']['printed_equation']:.3f}. Hairiness differs most: Table 5 {chk['hairiness']['table5']:.2f}, refit {chk['hairiness']['quadratic_refit']:.2f}, printed equation {chk['hairiness']['printed_equation']:.2f}. These agreements show that Table 5 holds model predictions, not measurements.",
                "Bars at 1.0 match Table 5 exactly. Agreement of a model prediction with Table 5 suggests that the number came from the model; it does not prove it, and a confirmation trial is still required.")

    # Metrics summary
    save_metrics_png(M["headline"], note="Values come from the re-analysis of the 15-run Box-Behnken table; no confirmation run was supplied.")
    print("figures done")


if __name__ == "__main__":
    main()
