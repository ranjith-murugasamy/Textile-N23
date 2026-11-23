# Audit of the supplied draft (`inputs/current_paper/Paper.docx`)

Scope: the draft has an introduction, methods, results and 36 references; no abstract and an empty Conclusion. No base code was supplied (the BASE CODE section is empty), so the analysis code is new. Each finding gives its evidence. Items marked "not verified" were not checked.

| # | Finding | Evidence |
|---|---------|----------|
| 1 | **Blend label is defined two opposite ways.** | Section 2.3 and 2.5: "cellulose acetate/cotton comber noil"; Table 3 header: "Blend Ratio (CO:CBF)"; Section 3.4.3: "70:30 (CO : CA)"; Table 5 row "CO/CA 70/30" and text "Comber noil/Cellulose acetate 70/30". The supplied files cannot settle it. Needs the mixing sheets. |
| 2 | **Printed Table 4 equations do not reproduce the printed Table 3 data.** | Applying them to the 15 runs gives R2 = 0.450 (tenacity), 0.439, -0.120 (U%), 0.847, 0.672 against reported 0.980, 0.989, 0.931, 0.981, 0.986 (`results/tables/table_audit_printed_vs_refit.csv`). Linear+2FI refit: 0.857 for tenacity, which equals the reviewer's 0.857. |
| 3 | **Equations have no squared terms but the text describes optima.** | Table 4 has only A, B, C, AB, AC, BC; Sections 3.4.1-3.4.5 describe responses that rise to an optimum speed then fall. That needs squared terms. |
| 4 | **Quadratic refit reproduces the claimed R2 roughly.** | R2 = 0.975, 0.980, 0.932, 0.975, 0.968, versus claimed 0.980, 0.989, 0.931, 0.981, 0.986. Printed intercepts equal the centre-run means and printed blend coefficients equal the quadratic-fit values. Several other coefficients differ, some in sign (tenacity BC +0.15 vs -0.15). Cause is not verified; needs the original software output. |
| 5 | **Table 5 values are model predictions, not measurements.** | At the draft's optimum the quadratic refit predicts 9.572 / 5.699 / 11.084 / 459.9 vs Table 5 9.617 / 5.702 / 11.098 / 456 (`metrics.json: paper_optimum_check`). No confirmation-run data is in the draft. |
| 6 | **"Comparable to 100% cotton" is not supported.** | Table 5 tenacity 9.617 vs 12.0 cN/tex, a 19.9% deficit (arithmetic: (12.0-9.617)/12.0). Cotton yarn has no description, count or replicates. |
| 7 | **Extrapolation beyond the tested range.** | Section 3.4.3 and 3.4.4 discuss rotor speeds above 60,000 and ~50,000 rpm; the design stops at 50,000 (Table 2). |
| 8 | **Wrong table and figure cross-references.** | Section 3.5 says comparison is "shown in Table 4" (it is Table 5); Section 3.4.4 points to "Fig. 4" for imperfections (Fig. 8); Section 3.4.5 points to "Fig. 5" for hairiness (Fig. 9). |
| 9 | **Rotor-speed inconsistency.** | Section 2.3: "operating at 20,000 rpm"; Table 2 and Table 3: 30,000-50,000 rpm. |
| 10 | **Citation numbers do not match the list.** | Introduction: "Maderuelo-Sanz 11" and "Mohajerani et al.10 encapsulated bitumen", but list item 10 is Maderuelo-Sanz and 11 is Ogundare; the pretreatment method cites "11, 19" which are Ogundare (nanocrystalline cellulose) and El Fadili (J Build Eng); in-text citation 37 (Section 3.4.5) has no entry, the list ends at 36. |
| 11 | **Table 1 values look doubtful.** | Cigarette-butt fibre strength 0.13 g/tex vs noil 2.5 g/tex; yarn strengths are in cN/tex (9.5), and a 0.13 g/tex fibre could not be spun; micronaire is a cotton measure. Units and method not stated. Treated as quoted, not verified. |
| 12 | **TGA text vs plotted curve.** | Text: 4.5% loss up to 225 C. The Fig. 4 curve, read by eye, is near 90% at 225 C (approximate, not digitised). The figure prints residual mass 16.56% at 498 C. Raw data needed. |
| 13 | **No evidence of conversion efficiency, contaminant removal or resource use.** | No masses, assays or utility records anywhere in the draft (searched Sections 2.1-2.2 and 3). |
| 14 | **Centre runs identical on several responses.** | Runs 10, 14, 15 give tenacity 8.8/8.8/8.8, elongation 6.7/6.7/6.7; makes lack-of-fit undefined for those two. Confirm they are independent spinning runs. |
| 15 | **Reviewer's claim that FTIR text resembles a published study** | Not verified (the cited nonwoven paper was not available). |
| 16 | **Target journal.** | The brief lists IJIES, Applied Sciences, IEEE Access; the reviewer file and reference papers target Waste and Biomass Valorization. We followed the reviewer file and reference papers. |

## Evidence ladder used
Step 1 (user data): the 15-run table printed in the draft, transcribed to `data/raw/bbd_table3.csv`. It is rounded and single-valued. No public benchmark replaces missing lab records; no network data were used.
