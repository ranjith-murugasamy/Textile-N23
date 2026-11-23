"""Generate manuscript/manuscript.json from results/metrics.json (all numbers via f-strings), then call build_manuscript."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import config as C
from paper_refs import REFS

ROOT = C.ROOT
M = json.loads((C.RESULTS / "metrics.json").read_text())
AD, AU, S1, S2 = M["adequacy"], M["audit"], M["optimum"]["S1_elong_in_range"], M["optimum"]["S2_elong_max"]
CK, BM, BE = M["paper_optimum_check"], M["blend_means"], M["blend_effect_70_vs_30"]
SHORT = {"tenacity": "tenacity", "elongation": "elongation", "u_pct": "U%", "imperfections": "imperfections", "hairiness": "hairiness"}
RL = ["tenacity", "elongation", "u_pct", "imperfections", "hairiness"]


def f(x, d=2):
    return f"{x:.{d}f}"


def R(*keys):
    return "{ref:" + ",".join(keys) + "}"


def fig_caption(name: str) -> str:
    md = (C.FIGURES / f"{name}.md").read_text()
    return re.search(r"\*\*What it shows\.\*\* (.*)", md).group(1).strip()


def fig(name: str, extra: str = "", width: float = 14.0) -> dict:
    return {"type": "figure", "path": f"../codebase/results/figures/{name}.png", "caption": fig_caption(name) + extra, "width_cm": width}


def P(t): return {"type": "p", "text": t}
def H2(t): return {"type": "h2", "text": t}
def EQ(t, n): return {"type": "equation", "text": t, "number": n}


def pv(p):
    return "<0.001" if p < 0.001 else f(p, 3)


# ---------------------------------------------------------------- tables
T1 = {"type": "table", "caption": "Fibre properties as reported in the draft (the instrument and standard used are not stated, so these values are quoted, not verified).",
      "header": ["Property", "Cigarette-butt fibre", "Comber noil"],
      "rows": [["2.5% span length (mm)", "20.50", "12"], ["50% span length (mm)", "9.00", "7"], ["Uniformity ratio (%)", "43.90", "50.4"],
               ["Fineness (micronaire)", "4.68", "3.16"], ["Strength (g/tex)", "0.13", "2.5"], ["Elongation (%)", "9.00", "4.3"], ["Density (g/cm3)", "1.31", "1.52"]]}
T2 = {"type": "table", "caption": "Box-Behnken factors, levels and coding. The first number of the blend label is the share (%) of the first-listed fibre.",
      "header": ["Factor", "Unit", "-1", "0", "+1"],
      "rows": [["X1 blend label (first-listed : second-listed fibre)", "%", "30:70", "50:50", "70:30"], ["X2 opening roller speed", "rpm", "4000", "5000", "6000"], ["X3 rotor speed", "rpm", "30000", "40000", "50000"]]}
import pandas as pd  # noqa: E402
runs = pd.read_csv(C.RAW / "bbd_table3.csv")
T3 = {"type": "table", "caption": "The 15 Box-Behnken runs and observed yarn properties as printed in the draft (rounded values; single measurement per run as far as the draft states). Runs 10, 14 and 15 are the centre replicates.",
      "header": ["Run", "Blend label", "Roller (rpm)", "Rotor (rpm)", "Tenacity (cN/tex)", "Elong. (%)", "U (%)", "Imperf. (/km)", "Hairiness"],
      "rows": [[int(r.run), f"{int(r.blend_first_pct)}:{int(r.blend_second_pct)}", int(r.opening_roller_rpm), int(r.rotor_rpm), r.tenacity_cN_tex, r.elongation_pct, r.u_pct, int(r.imperfections_per_km), r.hairiness_index] for r in runs.itertuples()], "font": 7}
T4 = {"type": "table", "caption": "Audit of the draft's response-surface equations: R2 as reported, R2 obtained when the printed equation is applied to the Table 3 data, and refits. Predicted R2 is the leave-one-out value.",
      "header": ["Response", "R2 reported", "R2 printed eq. on data", "R2 linear+2FI refit", "R2 quadratic", "Adj. R2 quad.", "Pred. R2 quad."],
      "rows": [[SHORT[r].capitalize() if r != "u_pct" else "U%", f(AU[r]["R2_reported"], 3), f(AU[r]["R2_printed_equation_on_data"], 3), f(AU[r]["R2_refit_lin+2FI"], 3),
                f(AU[r]["R2_refit_quadratic"], 3), f(AU[r]["R2adj_quadratic"], 3), f(AU[r]["R2pred_quadratic"], 3)] for r in RL]}
T5 = {"type": "table", "caption": "Adequacy statistics of the full quadratic models (10 coefficients, 15 runs, 5 residual degrees of freedom). LOF is the lack-of-fit test against pure error from the three centre runs (2 df); n.d. means not defined because the centre replicates were identical.",
      "header": ["Response", "F (9,5)", "p (model)", "RMSE", "CV (%)", "Signal/noise", "LOF p", "Shapiro-Wilk p"],
      "rows": [[SHORT[r].capitalize() if r != "u_pct" else "U%", f(AD[r]["F_model"], 1), pv(AD[r]["p_model"]), f(AD[r]["RMSE"], 3), f(AD[r]["CV_pct"], 1), f(AD[r]["adeq_precision"], 1),
                "n.d." if AD[r]["LOF_p"] is None else pv(AD[r]["LOF_p"]), f(AD[r]["shapiro_p"], 2)] for r in RL]}
terms = ["1", "A", "B", "C", "AB", "AC", "BC", "A2", "B2", "C2"]
tn = {"1": "Intercept", "A": "A (blend)", "B": "B (roller)", "C": "C (rotor)", "AB": "AB", "AC": "AC", "BC": "BC", "A2": "A2", "B2": "B2", "C2": "C2"}
T6 = {"type": "table", "caption": "Coefficients of the full quadratic models in coded units (A = (blend - 50)/20, B = (roller - 5000)/1000, C = (rotor - 40000)/10000). An asterisk marks p < 0.05.",
      "header": ["Term", "Tenacity", "Elongation", "U%", "Imperfections", "Hairiness"],
      "rows": [[tn[t]] + [f(M["coefficients"][r][t], 3) + ("*" if t != "1" and M["coef_p"][r][t] < 0.05 else "") for r in RL] for t in terms]}
T7 = {"type": "table", "caption": "Predicted properties at the recomputed optimum (scenario S1) with intervals, the draft's Table 5 blend values and the draft's 100% cotton benchmark. All entries in the first three columns are model predictions, not measurements.",
      "header": ["Property", "Refit prediction", "Bootstrap 95% CI", "95% prediction interval", "Draft Table 5 (blend)", "Cotton benchmark (unverified)"],
      "rows": [[C.LABEL[r], f(S1["pred"][r], 2 if r != "imperfections" else 0), f"{f(S1['boot_pred_ci95'][r][0], 2 if r != 'imperfections' else 0)} to {f(S1['boot_pred_ci95'][r][1], 2 if r != 'imperfections' else 0)}",
                f"{f(S1['pred_interval95'][r][0], 2 if r != 'imperfections' else 0)} to {f(S1['pred_interval95'][r][1], 2 if r != 'imperfections' else 0)}",
                C.PAPER_TABLE5[r], C.COTTON_BENCH[r]] for r in RL]}
T8 = {"type": "table", "caption": "Evidence for waste valorisation that was not available for this study. Each item is named in the journal reviewer's list; none was measured or reconstructed here.",
      "header": ["Item", "What is needed", "Status in this paper"],
      "rows": [["Mass balance and recovery yield", "Masses of collected butts, isolated filters, dry pretreated fibre, comber noil, spinning waste, finished yarn", "Not recorded; yields cannot be computed from yarn properties"],
               ["Residual nicotine and metals", "Before and after assays with detection limits (for example ICP and chromatography)", "Not measured; no safety claim is made"],
               ["Effect of 5% NaOH on acetyl groups", "FTIR or degree-of-substitution of untreated and treated fibre", "Only treated-fibre FTIR available"],
               ["Resource use", "Water, NaOH, acetic acid, electricity, effluent per kg", "Not recorded; no environmental saving is claimed"],
               ["Confirmation trial at the optimum", "Replicate yarns spun and tested at the optimum settings", "Not supplied; optimum is a prediction"],
               ["Replicate yarn measurements", "Specimen counts and standard deviations per run", "Not supplied; one value per run is used"]]}

RD, RO = M["reduced"], M["reduced_optimum"]
T9 = {"type": "table", "caption": "Reduced models from backward elimination (terms removed when p > 0.10, hierarchy kept) compared with the full quadratic models. Because the same 15 runs choose the terms, the reduced predicted R2 is optimistic.",
      "header": ["Response", "Terms kept (coded)", "R2", "Adj. R2", "Pred. R2 reduced", "Pred. R2 full"],
      "rows": [[SHORT[r].capitalize() if r != "u_pct" else "U%", " ".join(t for t in RD[r]["terms"] if t != "1"), f(RD[r]["R2"], 3), f(RD[r]["R2_adj"], 3), f(RD[r]["R2_pred"], 3), f(AD[r]["R2_pred"], 3)] for r in RL]}

# ---------------------------------------------------------------- text
abstract = (
    f"Discarded cigarette filters are made of cellulose acetate and are the most littered item worldwide, yet routes that turn them into continuous textile products are rarely documented. "
    f"This paper revisits a rotor-spinning study in which pretreated cigarette-filter fibre was blended with cotton comber noil and spun into 7 Ne yarn under a 15-run Box-Behnken design "
    f"(blend label, opening-roller speed, rotor speed). We re-analysed the original run table with full quadratic response-surface models, ANOVA, leave-one-out validation, a bootstrap "
    f"and a composite desirability search. The equations printed in the earlier draft contained no squared terms and reproduced only R2 = {f(AU['tenacity']['R2_printed_equation_on_data'])} of the tenacity variance "
    f"against the {f(AU['tenacity']['R2_reported'])} claimed; the quadratic refit gives R2 = {f(AD['tenacity']['R2'], 3)} but a predicted R2 of only {f(AD['tenacity']['R2_pred'], 2)}; reduced models do better but are optimistic. "
    f"Moving the blend label from 30:70 to 70:30 raised tenacity by {f(BE['tenacity']['effect'])} cN/tex (95% CI {f(BE['tenacity']['ci'][0])} to {f(BE['tenacity']['ci'][1])}) and cut hairiness by {f(-BE['hairiness']['effect'])} index units. "
    f"The desirability optimum lies on the upper edge of the tested blend range, with predicted tenacity {f(S1['pred']['tenacity'])} cN/tex (95% prediction interval {f(S1['pred_interval95']['tenacity'][0], 1)} to {f(S1['pred_interval95']['tenacity'][1], 1)}). "
    f"No confirmation run, mass balance or contaminant assay was available, so the work demonstrates spinnability and a corrected optimisation, not recovery efficiency or product safety."
)

sections = []

sections.append({"heading": "1. Introduction", "blocks": [
    P(f"Cigarette butts are the most frequently littered item in the world. Each filter is a plug of cellulose acetate that can carry nicotine, heavy metals and combustion residues into soil and water {R('torkash', 'conradi')}, and it persists for years in urban and coastal settings {R('araujo')}. Collecting and landfilling the material treats only the symptom. A second line of work treats it as a feedstock."),
    P(f"Recycling studies have turned the filter material into fired-clay bricks and asphalt additives {R('moha16', 'moha17')}, acoustic absorbers {R('maderuelo')}, nanocrystalline cellulose for biomedical use {R('ogundare')} and cellulose pulp for paper {R('teixeira')}. Nonwoven sorbents made from recovered cellulose acetate and cotton have also been optimised with a Box-Behnken design {R('viju')}. The textile route is much less developed. A yarn is a harder target than a nonwoven web because the fibres must be drafted, aligned and twisted continuously, and cellulose acetate recovered from filters is short, irregular and smooth."),
    P("The earlier version of this study tackled that gap directly. Cigarette-filter fibre could not be spun alone on a rotor machine, because the shredded fibre clogged the card cylinder, so it was blended with cotton comber noil, itself a spinning-mill waste. Fifteen yarns were spun under a Box-Behnken design and described by response-surface equations. The draft had three weaknesses that a reviewer for a waste-valorisation journal would notice at once: the blend label was defined in two opposite ways, the printed regression equations did not fit the printed data, and nothing quantified how much waste was actually converted."),
    P("We therefore treat this paper as a corrected re-analysis with an explicit scope. The contributions are four. First, we audit the printed equations against the printed run table and show where they fail. Second, we refit full quadratic models with ANOVA, leave-one-out validation and bootstrap uncertainty. Third, we redo the multi-response optimisation and show how well the data determine it. Fourth, we list the valorisation evidence (mass balance, contaminants, resource use, confirmation trial) that is still missing, so that no reader mistakes a spinning study for a demonstrated recovery process."),
]})

sections.append({"heading": "2. Literature survey", "blocks": [
    P(f"Reviews of cigarette-butt management describe the scale of the problem and the toxicity of leachates {R('torkash', 'conradi', 'araujo')}. A comparison of cellulose acetate and plastic filter pollution frames the environmental case for recovering the polymer rather than abandoning it {R('joly')}, and a review of recycling options catalogues construction, sorption and energy uses {R('moha16')}. Beyond those cited above, applications reported for cigarette-butt material include adsorbents, adhesives, corrosion inhibitors and horticultural substrates {R('marinello', 'mariotti')}; we cite them as categories and leave the authors to confirm the specific attributions."),
    P(f"Characterisation of recovered cellulose acetate usually combines infrared spectroscopy, electron microscopy and thermogravimetry. The ester carbonyl band near 1735 cm-1, the C-O-C band near 1216 cm-1 and the broad hydroxyl band are the usual markers {R('candido', 'shaikh')}, and thermal degradation of cellulose acetate in an inert atmosphere is dominated by one main step in the 300-400 C range {R('arthan')}. Alkaline treatment is a standard way to clean and modify cellulosic fibres {R('mwaikambo')}, but with an acetate ester it may also deacetylate the polymer, which is why before-and-after spectra matter."),
    P(f"On the spinning side, rotor-yarn quality depends on how well the opening roller individualises fibres and how they are laid in the rotor groove. Published work links opening-roller speed, rotor speed and fibre length to strength, unevenness and hairiness {R('kothari', 'bagwan', 'habib')}, and describes imperfection and hairiness behaviour in short-staple blends {R('celik', 'roudbari', 'jabbar')}. Those studies are mostly on virgin or cotton-based blends. Cigarette-filter fibre brings a smooth surface, low cohesion and irregular cut length, so their conclusions cannot be transferred without testing."),
    P(f"Within the target journal, two recent studies show what a waste-to-fibre paper is expected to contain. One quantified separation yield and recyclable-fibre yield from textile waste after enzymatic treatment {R('etuk')}. Another linked lignin extracted from corn stover to wet-spun fibre composition, morphology, thermal stability and mechanical behaviour {R('szlek')}. Both report conversion or composition data next to product properties. The present study has the product properties and a statistical treatment of them; it lacks the conversion data, and we say so."),
    P(f"Statistical methods used here are standard. The Box-Behnken design {R('box')} supports quadratic models with few runs and has no corner points. Response-surface practice {R('myers')} calls for ANOVA, lack-of-fit and prediction statistics rather than a single R2. Prediction error is estimated by the PRESS statistic {R('allen')}, normality of residuals by the Shapiro-Wilk test {R('shapiro')}, uncertainty by the bootstrap {R('efron')}, and several responses are combined with the desirability function {R('derringer')}."),
]})

sections.append({"heading": "3. Materials and methods", "blocks": [
    H2("3.1 Feedstocks"),
    P(f"Two waste streams were used. Cigarette butts were collected from local sources and several commercial brands, separated by hand from remaining tobacco, and the filter material was isolated; cellulose acetate from both the inner and outer paper layers of the filters was used for yarn. Cotton comber noil came from spinning mills around Coimbatore, India. Table 1 gives the fibre properties as stated in the draft. The cigarette-butt fibre is longer (2.5% span length 20.5 mm against 12 mm) but its listed strength of 0.13 g/tex is much lower than that of the noil (2.5 g/tex); both the unit and the testing method for that value need to be confirmed, because a strength of 0.13 g/tex would not allow any yarn to be spun."),
    T1,
    H2("3.2 Pretreatment"),
    P("Isolated fibres were soaked in distilled water for 24 h, treated with 5% (w/v) sodium hydroxide at room temperature for 60 min, washed with distilled water, neutralised with 1% (w/v) acetic acid and dried at 80 C for 24 h. The protocol follows earlier work on removing nicotine, metals and organic contaminants. We did not measure its effect on contaminants, on the degree of acetylation or on the mass of fibre retained, so those aspects are outside the evidence of this paper."),
    H2("3.3 Yarn production"),
    P("Yarns were produced on a micro-spinning line (Trytex, India). Slivers were prepared on a miniature card and passed twice through a draw frame. The drawn sliver was spun on a rotor machine to a final count of 7 Ne with 18 twists per inch (Z twist), from a feed hank of 0.15 Ne. The draft states a base rotor speed of 20,000 rpm in the spinning description and 30,000 to 50,000 rpm in the experimental design; we use the design values because the run table is built on them, and flag the discrepancy for the authors. <<fig:user_image1>> shows the process flow."),
    {"type": "figure", "path": "../codebase/data/raw/user_image1.jpeg", "caption": "Manufacturing route from cigarette filters and comber noil to rotor-spun yarn (the authors' own flow chart, reproduced from the earlier draft).", "width_cm": 12.0},
    H2("3.4 Yarn testing"),
    P("Conditioning followed ISO 139 (20 +/- 2 C, 65 +/- 4% relative humidity). Single-yarn tenacity and elongation were measured on a Uster Tensorapid 4 following ASTM D2256. Unevenness (U%) and imperfections per kilometre were measured on a Uster Tester 5 following ASTM D1425, and hairiness was reported as a hairiness index. The draft does not state how many specimens were tested per run, so each run is treated as one value."),
    H2("3.5 Fibre characterisation"),
    P("Infrared spectra were recorded on a Shimadzu 8400S in attenuated total reflection mode. Fibre surfaces were imaged with a Zeiss EVO-18 environmental scanning electron microscope after gold coating. Thermogravimetric analysis used a Netzsch Jupiter STA 449 F3 on about 5 mg of sample, heated to 773 K at 20 K/min in nitrogen. Raw spectra and thermograms were not supplied, so we use the authors' figures and their stated numerical readings only."),
    H2("3.6 Experimental design and dataset"),
    P(f"A three-factor Box-Behnken design gives twelve edge-midpoint runs and three centre replicates, 15 in all (Table 2). The factors were the blend label (30:70, 50:50, 70:30), the opening-roller speed (4000, 5000, 6000 rpm) and the rotor speed (30,000, 40,000, 50,000 rpm). Table 3 lists the runs exactly as printed in the draft. These are rounded values, not the original laboratory records. There is no train/test split: with 15 runs every observation is needed to fit ten coefficients, so we use leave-one-out validation and the centre replicates for pure error instead."),
    P("The draft defines the blend label in two ways. The Methods section calls it cellulose acetate to comber noil, while the header of its Table 3 reads CO:CBF (comber noil to cigarette-butt fibre), and the discussion reads 70:30 as cotton to acetate. We could not resolve this from the supplied files. To avoid choosing the reading that suits the narrative, we refer to the first number of the label as the share of the first-listed fibre, code it as X1, and state which results depend on the assignment. All statistical results below are identical under either assignment; only the physical interpretation changes."),
    T2,
    T3,
    H2("3.7 Statistical analysis and evaluation parameters"),
    P("For each response y the coded design matrix contains an intercept, three linear terms, three two-factor interactions and three squared terms:"),
    EQ("y = b0 + b1 A + b2 B + b3 C + b12 AB + b13 AC + b23 BC + b11 A^2 + b22 B^2 + b33 C^2 + e", 1),
    P("Coefficients were estimated by ordinary least squares. We report the coefficient of determination, the adjusted value and the leave-one-out predicted value:"),
    EQ("R2 = 1 - SSE/SST;   R2_adj = 1 - [SSE/(n-p)] / [SST/(n-1)];   R2_pred = 1 - PRESS/SST", 2),
    P(f"where n = {M['n_runs']} runs, p = 10 coefficients and PRESS is the sum of squared leave-one-out residuals e_i/(1 - h_i) {R('allen')}. Lack of fit was tested against pure error from the three centre runs (two degrees of freedom). The signal-to-noise ratio is (max fitted - min fitted) divided by the square root of (MSE x p / n). Residual normality was tested with the Shapiro-Wilk test."),
    P("For optimisation each response was mapped to a desirability d between 0 and 1 over its observed range [L, U]. For a response to be maximised d = (y - L)/(U - L), for one to be minimised d = (U - y)/(U - L), and for a response left free within its observed range d = 1. The composite desirability is the geometric mean of the five values:"),
    EQ("D = (d_tenacity x d_elongation x d_U x d_imperf x d_hair)^(1/5)", 3),
    P(f"In the primary scenario (S1) tenacity is maximised, U%, imperfections and hairiness are minimised and elongation is free within its observed range; in S2 elongation is maximised as well. These goals were fixed before the analysis. Because the blend factor is bounded, the search covers the tested cube only (a 41 x 41 x 41 grid, which is 1 percentage point of blend, 50 rpm of roller speed and 500 rpm of rotor speed per step). Uncertainty of the optimum was estimated by a residual bootstrap with {M['n_boot']} resamples: leverage-adjusted, centred residuals were resampled onto the fitted values, all five models were refitted, and the optimum was recomputed each time (seed {M['seed']}). Prediction intervals at the optimum use the t distribution with 5 residual degrees of freedom. The code is in the repository listed under data and code availability."),
]})

sections.append({"heading": "4. Results and discussion", "blocks": [
    H2("4.1 Fibre characterisation"),
    P("The infrared spectrum of the treated cigarette-filter fibre (<<fig:user_image2>>) shows a broad hydroxyl band between 3800 and 3000 cm-1, a C-H stretching peak at 2922.59 cm-1, a strong ester carbonyl band at 1735 cm-1, bands at 1369 and 1029 cm-1 (C-H deformation and C-O stretching) and a C-O-C band at 1216 cm-1. These match the usual cellulose acetate pattern, so the fibre is still predominantly an acetate ester after the NaOH step. That conclusion has a limit: without the spectrum of the untreated fibre, we cannot say whether the carbonyl band lost intensity, and 5% NaOH can deacetylate cellulose acetate."),
    {"type": "figure", "path": "../codebase/data/raw/user_image2.png", "caption": "Infrared spectrum of the recovered cellulose acetate fibre (authors' measurement, reproduced from the earlier draft).", "width_cm": 10.0},
    P("Scanning electron micrographs (<<fig:user_image3>>) show a smooth, nearly featureless surface for the acetate fibre and a rough, convoluted surface with grooves for cotton. The difference matters for spinning: a smooth surface offers little frictional grip, which is the usual explanation for slippage and low cohesion in acetate-rich blends."),
    {"type": "figure", "path": "../codebase/data/raw/user_image3.jpeg", "caption": "Scanning electron micrographs of (a) cotton fibre and (b) cellulose acetate fibre (authors' images, reproduced from the earlier draft).", "width_cm": 11.0},
    P("The thermogram (<<fig:user_image4>>) shows a small early mass loss, a main degradation step centred near 370 C and a residual mass of 16.56% at 498 C, the figure printed on the curve. The draft's text gives 4.5% mass loss up to 225 C and a 70-80% loss between 225 and 380 C. Reading the plotted curve by eye, the mass at 225 C is closer to 90% than to 95.5%, so those text values do not obviously match the plot; we therefore quote only the residual mass and ask for the exported data to extract onset and peak temperatures. The late-stage 'carbonisation' of cellulose acetate between 380 and 500 C that the draft invokes is likewise not distinguishable here, since the curve is nearly flat after about 420 C."),
    {"type": "figure", "path": "../codebase/data/raw/user_image4.png", "caption": "Thermogravimetric curve of the recovered cellulose acetate fibre in nitrogen at 20 K/min (authors' measurement, reproduced from the earlier draft). The residual mass of 16.56% at 498 C is printed on the original figure.", "width_cm": 9.0},
    H2("4.2 What the run table shows"),
    P(f"Before any model, the raw table (Table 3) already carries the main result. Averaged over the runs at each label (<<fig:fig_09_blend_level_results>>), tenacity is {f(BM['30']['tenacity'])}, {f(BM['50']['tenacity'])} and {f(BM['70']['tenacity'])} cN/tex for 30:70, 50:50 and 70:30; elongation falls from {f(BM['30']['elongation'])}% to {f(BM['70']['elongation'])}%; U% falls from {f(BM['30']['u_pct'])} to {f(BM['70']['u_pct'])}; imperfections from {f(BM['30']['imperfections'], 0)} to {f(BM['70']['imperfections'], 0)} per km; and the hairiness index from {f(BM['30']['hairiness'])} to {f(BM['70']['hairiness'])}. Tenacity and hairiness are almost perfectly anti-correlated across all 15 runs (<<fig:fig_01_design_and_tradeoff>>; r = {f(M['data_checks']['tenacity_vs_hairiness_corr'], 3)}), and U% and imperfections are strongly correlated (r = {f(M['data_checks']['u_vs_imperfections_corr'], 3)}), so the five responses carry fewer than five independent pieces of information. Tenacity and elongation conflict (r = {f(M['data_checks']['tenacity_vs_elongation_corr'], 2)}): the label that gives strong yarn gives less extensible yarn."),
    fig("fig_01_design_and_tradeoff"),
    fig("fig_09_blend_level_results"),
    P(f"The three centre replicates are nearly identical (standard deviations of {f(M['centre_sd']['tenacity'], 2)} cN/tex for tenacity, {f(M['centre_sd']['u_pct'], 3)} for U% and {f(M['centre_sd']['imperfections'], 1)} per km for imperfections). Such close agreement is possible but also what one sees when repeated values are averaged or copied; the authors should confirm they are independent spinning runs, because the lack-of-fit test depends on them."),
    H2("4.3 The printed response-surface equations do not fit the printed data"),
    P(f"The draft's Table 4 lists, for each response, an intercept, three linear terms and three interactions, with R2 between {f(min(AU[r]['R2_reported'] for r in RL), 3)} and {f(max(AU[r]['R2_reported'] for r in RL), 3)}. We applied those equations to the Table 3 runs. For tenacity they explain {f(AU['tenacity']['R2_printed_equation_on_data'], 2)} of the variance, for elongation {f(AU['elongation']['R2_printed_equation_on_data'], 2)}, for U% {f(AU['u_pct']['R2_printed_equation_on_data'], 2)} (a negative value, worse than predicting the mean), for imperfections {f(AU['imperfections']['R2_printed_equation_on_data'], 2)} and for hairiness {f(AU['hairiness']['R2_printed_equation_on_data'], 2)} (Table 4, <<fig:fig_04_model_audit>>). Refitting the same linear-plus-interaction form by least squares gives {f(AU['tenacity']['R2_refit_lin+2FI'], 3)} for tenacity, matching an independent check reported by a reviewer, and {f(min(AU[r]['R2_refit_lin+2FI'] for r in RL), 2)} to {f(max(AU[r]['R2_refit_lin+2FI'] for r in RL), 2)} across the five responses. Neither matches the claimed values."),
    T4,
    fig("fig_04_model_audit"),
    P(f"The full quadratic fit gives R2 values of {f(min(AU[r]['R2_refit_quadratic'] for r in RL), 3)} to {f(max(AU[r]['R2_refit_quadratic'] for r in RL), 3)}, close to the reported ones. The printed intercept and the printed blend coefficient match the quadratic fit for all five responses (for tenacity 8.80 and 0.9875 in both, and the intercept equals the mean of the three centre runs), which is what one would expect if the printed equations were cut down from a quadratic model. The remaining coefficients do not all match: the printed BC term for tenacity is +0.15 against -0.15 in the refit, the printed roller term for elongation is +0.0625 against -0.087, and the printed AB term for U% is -0.1675 against +0.32. The most plausible reading is that the reported statistics came from a quadratic model whose squared terms were dropped when the equations were typed up, with some other coefficients altered on the way. We cannot prove that from rounded printed numbers; it needs the authors' original software output. The narrative of the draft also describes tenacity rising to an optimum roller or rotor speed and then falling, a behaviour that needs squared terms and that its printed equations cannot produce."),
    H2("4.4 Quadratic models: adequacy and what they can claim"),
    P(f"All five quadratic models are significant (Table 5; model p between {pv(min(AD[r]['p_model'] for r in RL))} and {pv(max(AD[r]['p_model'] for r in RL))}), and signal-to-noise ratios of {f(min(AD[r]['adeq_precision'] for r in RL), 1)} to {f(max(AD[r]['adeq_precision'] for r in RL), 1)} are well above the threshold of 4. Shapiro-Wilk p-values are all above {f(min(AD[r]['shapiro_p'] for r in RL), 2)}, so normal residuals are not rejected, though five residual degrees of freedom give that test little power (<<fig:fig_03_residual_diagnostics>>)."),
    T5,
    T6,
    P(f"The quantity that limits the claims is the predicted R2, {f(AD['tenacity']['R2_pred'], 2)} for tenacity, {f(AD['elongation']['R2_pred'], 2)} for elongation, {f(AD['u_pct']['R2_pred'], 2)} for U%, {f(AD['imperfections']['R2_pred'], 2)} for imperfections and {f(AD['hairiness']['R2_pred'], 2)} for hairiness. A model with ten coefficients fitted to 15 points describes those points well but loses much of that skill when one run is withheld (<<fig:fig_02_predicted_vs_observed>>). The U% model is the weakest: its predicted R2 is negative, and lack of fit is significant against pure error (p = {pv(AD['u_pct']['LOF_p'])}); the same test gives p = {pv(AD['imperfections']['LOF_p'])} for imperfections and p = {pv(AD['hairiness']['LOF_p'])} for hairiness. The lack-of-fit F ratios are inflated by the very small pure-error variance of the centre runs, so they should be read as warnings, not as proof. For tenacity and elongation the centre replicates are identical and the test is undefined (<<fig:fig_10_noise_and_lack_of_fit>>)."),
    fig("fig_02_predicted_vs_observed"),
    fig("fig_03_residual_diagnostics"),
    fig("fig_10_noise_and_lack_of_fit"),
    P(f"The low predicted R2 values suggest that the full model carries more terms than 15 runs can support. As a robustness check we removed terms with p above 0.10 one at a time, keeping model hierarchy (Table 7). Four of the five responses (tenacity, elongation, imperfections, hairiness) keep the blend term, both speed terms and both squared speed terms; U% keeps blend, roller, their interaction and the squared blend term. The reduced models keep R2 between {f(min(RD[r]['R2'] for r in RL), 2)} and {f(max(RD[r]['R2'] for r in RL), 2)} and raise the predicted R2 to {f(min(RD[r]['R2_pred'] for r in RL), 2)}-{f(max(RD[r]['R2_pred'] for r in RL), 2)}. That gain is partly an artefact: the same 15 runs picked the terms, so leave-one-out error computed afterwards is too optimistic. What matters for the paper's conclusions is that the optimum hardly moves. The reduced models place it at a blend label of {f(RO['actual']['blend'], 0)}, roller {f(RO['actual']['roller'], 0)} rpm and rotor {f(RO['actual']['rotor'], 0)} rpm (D = {f(RO['desirability'], 3)}), with predicted tenacity {f(RO['pred']['tenacity'])} cN/tex, against {f(S1['pred']['tenacity'])} from the full models."),
    T9,
    H2("4.5 Effects of blend and process speeds"),
    P(f"The blend term is the only effect that is significant for every response (Table 6, <<fig:fig_05_standardised_coefficients>>; p < 0.001 in each case). Moving the label from 30 to 70 changes tenacity by {f(BE['tenacity']['effect'])} cN/tex (95% CI {f(BE['tenacity']['ci'][0])} to {f(BE['tenacity']['ci'][1])}), elongation by {f(BE['elongation']['effect'])} percentage points ({f(BE['elongation']['ci'][0])} to {f(BE['elongation']['ci'][1])}), U% by {f(BE['u_pct']['effect'])} ({f(BE['u_pct']['ci'][0])} to {f(BE['u_pct']['ci'][1])}), imperfections by {f(BE['imperfections']['effect'], 1)} per km ({f(BE['imperfections']['ci'][0], 0)} to {f(BE['imperfections']['ci'][1], 0)}) and hairiness by {f(BE['hairiness']['effect'])} ({f(BE['hairiness']['ci'][0])} to {f(BE['hairiness']['ci'][1])}). Each of these intervals excludes zero."),
    P(f"Speed effects are smaller and less certain. For tenacity the significant terms other than blend are the squared roller term (p = {pv(M['coef_p']['tenacity']['B2'])}) and the squared rotor term (p = {pv(M['coef_p']['tenacity']['C2'])}), both negative, which means that tenacity peaks inside the tested range of both speeds and falls at either extreme (<<fig:fig_06_response_surfaces>>). The same two squared terms are significant for elongation. For U% and hairiness no speed term reaches p < 0.05; for imperfections only the squared roller term does (p = {pv(M['coef_p']['imperfections']['B2'])}). Many of these p-values lie between 0.05 and 0.15 and, with five residual degrees of freedom, the study cannot separate small speed effects from noise."),
    fig("fig_05_standardised_coefficients"),
    P("The mechanisms the draft offers (better fibre opening up to an optimum roller speed, fibre damage beyond it, poorer fibre laydown at high rotor speed) are plausible and consistent with the curvature found for tenacity and elongation, but the experiment did not test them. We kept them as hypotheses. Several statements in the draft concern rotor speeds above 50,000 or 60,000 rpm, which lie outside the tested range and cannot be supported by these data."),
    fig("fig_06_response_surfaces"),
    P(f"The meaning of the blend effect depends on which fibre the first number refers to. If the first number is cellulose acetate (Methods reading), yarns with more acetate are stronger, smoother and less hairy, which agrees with the longer span length of the acetate fibre in Table 1 but contradicts the draft's explanation that smooth acetate lowers cohesion and strength, and its listed fibre strength. If the first number is comber noil (Table 3 header reading), more noil gives stronger yarn, which agrees with the noil's higher listed fibre strength and the cohesion argument, but means that more of the short (12 mm) fibre goes together with lower hairiness and lower U%, which is the opposite of what short-fibre content normally does. Neither reading is free of difficulty. Until the mixing sheets settle it, we make no mechanistic claim from the sign of the blend effect."),
    H2("4.6 Multi-response optimisation"),
    P(f"The composite desirability search over the tested cube places the optimum at a blend label of {f(S1['actual']['blend'], 0)}, an opening-roller speed of {f(S1['actual']['roller'], 0)} rpm and a rotor speed of {f(S1['actual']['rotor'], 0)} rpm (D = {f(S1['desirability'], 3)}; scenario S1). The draft reports 68.727, 4713.754 and 47,430.327 rpm. The two differ, but the bootstrap shows that the data do not tell them apart: the 95% bootstrap interval for the roller optimum is {f(S1['boot_loc_ci95']['roller'][0], 0)} to {f(S1['boot_loc_ci95']['roller'][1], 0)} rpm and for the rotor optimum {f(S1['boot_loc_ci95']['rotor'][0], 0)} to {f(S1['boot_loc_ci95']['rotor'][1], 0)} rpm, which includes the draft values for both. The blend optimum is at the upper bound in {f(100 * S1['boot_frac_blend_at_bound'], 1)}% of the resamples. The data therefore say that more of the first-listed fibre is better for the chosen goals, up to the highest level tested; they cannot say that 68.7 is better than 70, and they say nothing about blends above 70. Under S2, where elongation is maximised as well, the optimum moves to roller {f(S2['actual']['roller'], 0)} rpm and rotor {f(S2['actual']['rotor'], 0)} rpm and the composite desirability falls to {f(S2['desirability'], 3)}, because tenacity and elongation pull against each other (<<fig:fig_07_optimum_uncertainty>>)."),
    fig("fig_07_optimum_uncertainty"),
    P(f"At the S1 optimum the models predict tenacity {f(S1['pred']['tenacity'])} cN/tex (95% prediction interval {f(S1['pred_interval95']['tenacity'][0], 1)} to {f(S1['pred_interval95']['tenacity'][1], 1)}), elongation {f(S1['pred']['elongation'])}%, U% {f(S1['pred']['u_pct'])}, {f(S1['pred']['imperfections'], 0)} imperfections per km and a hairiness index of {f(S1['pred']['hairiness'])} (Table 8). The prediction intervals are wide, for example {f(S1['pred_interval95']['hairiness'][0], 1)} to {f(S1['pred_interval95']['hairiness'][1], 1)} for hairiness, because they combine residual noise estimated on five degrees of freedom with parameter uncertainty."),
    T7,
    H2("4.7 Comparison with 100% cotton and the status of Table 5"),
    P(f"The draft's Table 5 compares the optimised blend yarn with a 100% cotton yarn, and states that the characteristics are comparable. We cannot confirm that. The cotton values (tenacity {C.COTTON_BENCH['tenacity']:.1f} cN/tex, elongation {C.COTTON_BENCH['elongation']:.1f}%, U% {C.COTTON_BENCH['u_pct']:.1f}, {C.COTTON_BENCH['imperfections']:.0f} imperfections per km, hairiness {C.COTTON_BENCH['hairiness']:.2f}) come with no description of the cotton, count, process or replicates, so we treat them as an external, unreproduced benchmark. The tenacity gap is large: the upper end of the 95% prediction interval for the blend ({f(S1['pred_interval95']['tenacity'][1], 1)} cN/tex) is below {C.COTTON_BENCH['tenacity']:.1f}. In U% and imperfections the benchmark lies above the upper end of the intervals, and for elongation and hairiness the benchmark falls inside them (<<fig:fig_08_optimum_vs_cotton>>). The sensible reading is a trade-off: the blend gives up roughly a fifth of the tenacity, and may gain in evenness and imperfections, which for coarse 7 Ne rotor yarn could suit applications that value regularity over strength. That claim would need a matched cotton yarn spun and tested in the same campaign."),
    P(f"The values in Table 5 of the draft are model predictions, not measurements. At the draft's optimum the quadratic refit predicts tenacity {f(CK['tenacity']['quadratic_refit'], 3)} cN/tex against the printed {CK['tenacity']['table5']:.3f}, elongation {f(CK['elongation']['quadratic_refit'], 3)} against {CK['elongation']['table5']:.3f}, U% {f(CK['u_pct']['quadratic_refit'], 3)} against {CK['u_pct']['table5']:.3f} and imperfections {f(CK['imperfections']['quadratic_refit'], 0)} against {CK['imperfections']['table5']:.0f}; the printed equations give {f(CK['tenacity']['printed_equation'], 3)}, {f(CK['elongation']['printed_equation'], 3)}, {f(CK['u_pct']['printed_equation'], 3)} and {f(CK['imperfections']['printed_equation'], 0)}. Close agreement of that kind (<<fig:fig_11_table5_provenance>>) is what a model produces, not what a tensile tester produces. Hairiness is the exception ({CK['hairiness']['table5']:.2f} printed, {f(CK['hairiness']['quadratic_refit'], 2)} refit, {f(CK['hairiness']['printed_equation'], 2)} from the printed equation). No confirmation trial was supplied. Until yarns are spun at the chosen settings and tested, the optimum should be described as predicted."),
    fig("fig_08_optimum_vs_cotton"),
    fig("fig_11_table5_provenance"),
    P("What would a spinner do with these results? The safest use is as a screening map. The blend label dominates, so the first decision is how much recovered filter fibre a mill is willing to put into the mix, and the data show a monotone improvement in every property except elongation up to the highest level tested. Roller and rotor speeds then act as fine tuning around the middle of their ranges, where the curvature terms place the tenacity maximum, and the loss from drifting to either end is modest compared with the gain from the blend. The elongation loss is the price: elongation falls from the 30:70 label to the 70:30 label by about two percentage points, which may matter for downstream weaving or knitting where yarns need to stretch without breaking. Those end uses were not tested here."),
    H2("4.8 Waste-valorisation evidence"),
    P("A waste-valorisation claim has two halves: the waste is converted into something useful, and the conversion is efficient and safe. The first half is supported. Pretreated cigarette-filter fibre was blended with comber noil and spun into 7 Ne rotor yarn in 15 successive trials, and the yarn properties varied in a systematic and statistically describable way. The second half is not supported by data we have. Table 9 lists what is missing."),
    T8,
    P("Without a mass balance we cannot say what fraction of collected butts ends up as yarn, and without before-and-after assays we cannot say that nicotine and metals were removed. The yarn should not be described as safe for skin contact or any end use that involves contact with people or water. The yield of cigarette-filter fibre compared with comber noil in the blend is also unknown, so the share of cigarette waste that the process can absorb is limited only by the 70% upper level tested, and we do not know whether higher shares are spinnable. Relative to the nonwoven sorbent route, the yarn route is distinguished by continuous production and by a different performance target, but this paper reports no head-to-head comparison and we do not claim one."),
    H2("4.9 Computation"),
    P("Reproducibility was a design goal. The 15-row table, the fixed random seed, the pinned library versions and the single pipeline script make every table and figure in this paper regenerate identically on a clean clone. We kept the analysis deliberately plain (ordinary least squares, residual bootstrap, grid search) so that the authors can repeat it in their own statistical package and compare the output with ours; a disagreement would point to rounding in the printed table or to a different model specification, both of which are worth knowing about before submission."),
    P("The re-analysis is a 15-row least-squares problem. The full pipeline, including 2 x 2000 bootstrap refits of five models and the figures, runs in well under a minute on a laptop CPU; there is no training stage and no hyperparameter search, and every number in this paper is regenerated by one script from the table of runs."),
]})

sections.append({"heading": "5. Limitations", "blocks": [
    P("The first limitation is data quality. The run table holds rounded values with one measurement per run, so we cannot estimate measurement error separately from model error, and the three centre values are almost identical. The second is size: 15 runs for ten coefficients leave five residual degrees of freedom, hence the low predicted R2 and wide intervals. The third is the unresolved blend label. The fourth is the absence of a confirmation run, which makes the optimum and Table 8 predictions rather than results. The fifth is the cotton benchmark, whose provenance is unknown."),
    P("Beyond statistics, no mass balance, resource inventory, contaminant assay or acetyl-group analysis exists, so we make no statement about recovery efficiency, environmental benefit or product safety. Thermogravimetric and spectral data were available only as images. The thermogram text values need to be reconciled with the plotted curve. Finally, all models are local to the tested region, with blend between 30 and 70, roller speed 4000 to 6000 rpm and rotor speed 30,000 to 50,000 rpm."),
]})

sections.append({"heading": "6. Conclusions and future work", "blocks": [
    P(f"Re-analysing the 15-run Box-Behnken data changes the paper's quantitative claims but supports its main qualitative one. The printed linear-plus-interaction equations reproduce only {f(AU['tenacity']['R2_printed_equation_on_data'], 2)} of the tenacity variance, not the {f(AU['tenacity']['R2_reported'], 2)} reported, whereas full quadratic models fit the runs well (R2 {f(min(AD[r]['R2'] for r in RL), 2)} to {f(max(AD[r]['R2'] for r in RL), 2)}) but predict a withheld run only modestly (predicted R2 {f(min(AD[r]['R2_pred'] for r in RL), 2)} to {f(max(AD[r]['R2_pred'] for r in RL), 2)}); reduced models raise that to {f(min(RD[r]['R2_pred'] for r in RL), 2)}-{f(max(RD[r]['R2_pred'] for r in RL), 2)} with an optimism caveat, and move the optimum only from rotor {f(S1['actual']['rotor'], 0)} to {f(RO['actual']['rotor'], 0)} rpm. The blend label is the dominant factor; the speed effects are small and mostly curvature."),
    P(f"The best-supported settings are the highest blend label tested with roller speed near {f(S1['actual']['roller'], 0)} rpm and rotor speed near {f(S1['actual']['rotor'], 0)} rpm, with wide uncertainty on both speeds. The predicted tenacity of {f(S1['pred']['tenacity'])} cN/tex is below the {C.COTTON_BENCH['tenacity']:.1f} cN/tex of the cotton benchmark, which is a real loss of strength that the application must tolerate."),
    P("The next steps are experimental, not statistical. The authors should settle the blend definition from the mixing sheets; record masses through the pretreatment and spinning chain; assay nicotine and selected metals before and after treatment; compare untreated and treated fibre by infrared spectroscopy; spin and test replicate confirmation yarns at the optimum together with a matched cotton control; and, if possible, extend the blend range above 70 to find where spinning fails. Only then can the process be presented as a quantified waste-valorisation pathway."),
]})

back = [
    {"heading": "Declarations: Conflicts of interest", "text": "[AUTHORS: state competing interests, or 'The authors declare no competing interests'.]"},
    {"heading": "Declarations: Author contributions", "text": "[Author 1] conceived the spinning study and produced the yarns. [Author 2] performed the characterisation. [AUTHORS: complete the CRediT statement.] The re-analysis code and the revised text were prepared with an AI assistant as described below, and the authors reviewed and take responsibility for them."},
    {"heading": "Declarations: Funding", "text": "[AUTHORS: funding sources or 'No funding was received'.]"},
    {"heading": "Declarations: Data and code availability", "text": "The 15-run table analysed here is printed as Table 3 and is included, with the analysis code, in the project repository under data/raw and src. [AUTHORS: add repository URL or DOI.] Raw FTIR, SEM and TGA files and the original unrounded yarn-test records are held by the authors."},
    {"heading": "Declarations: Use of AI tools", "text": "An AI assistant (Claude, Anthropic) was used to write the statistical re-analysis code, produce the figures and tables, and draft and revise the manuscript text, all under the authors' direction. Every number in the manuscript is generated by that code from the authors' run table. The authors checked the outputs and are responsible for the content. [AUTHORS: align this statement with the journal's current AI policy.]"},
]


def build() -> None:
    order: list[str] = []

    def sub(m):
        nums = []
        for k in m.group(1).split(","):
            if k not in order:
                order.append(k)
            nums.append(order.index(k) + 1)
        nums.sort()
        return "[" + ",".join(str(n) for n in nums) + "]"

    pat = re.compile(r"\{ref:([^}]*)\}")
    figorder = [Path(b["path"]).stem for sec in sections for b in sec["blocks"] if b["type"] == "figure"]
    fpat = re.compile(r"<<fig:([^>]*)>>")
    for sec in sections:
        for b in sec["blocks"]:
            if "text" in b:
                b["text"] = fpat.sub(lambda m: f"Fig. {figorder.index(m.group(1)) + 1}", pat.sub(sub, b["text"]))
    refs = [REFS[k] for k in order]
    spec = {
        "header_left": "Waste and Biomass Valorization", "header_right": "Original research article",
        "title": "Valorization of Cigarette-Butt and Cotton Comber Noil Wastes into Rotor-Spun Blended Yarns: Response-Surface Re-analysis of a Box-Behnken Spinning Study",
        "authors": "[Author 1], [Author 2], [Author 3]",
        "affiliations": ["[Affiliation: department, institution, city, country]"],
        "corresponding": "[AUTHORS: corresponding author name and e-mail]",
        "abstract": abstract,
        "keywords": "Cigarette butt waste; Cellulose acetate; Comber noil; Rotor spinning; Box-Behnken design; Response surface methodology",
        "sections": sections, "back_matter": back, "references": refs,
    }
    (ROOT.parent / "manuscript").mkdir(exist_ok=True)
    (ROOT.parent / "manuscript" / "manuscript.json").write_text(json.dumps(spec, indent=1))
    print("refs", len(refs), "abstract words", len(abstract.split()))


if __name__ == "__main__":
    build()
