"""Write output/cover_letter.docx from results/metrics.json (numbers are read, not typed)."""
import json

from docx import Document

import config as C

M = json.loads((C.RESULTS / "metrics.json").read_text())
S1, AU = M["optimum"]["S1_elong_in_range"], M["audit"]["tenacity"]
d = Document()
d.add_paragraph("To the Editor, Waste and Biomass Valorization")
d.add_paragraph("Subject: Submission of an original research article")
for t in [
    "Dear Editor,",
    "We submit the manuscript 'Valorization of Cigarette-Butt and Cotton Comber Noil Wastes into Rotor-Spun Blended Yarns: Response-Surface Re-analysis of a Box-Behnken Spinning Study' for consideration in Waste and Biomass Valorization.",
    "The work converts two waste streams, cellulose acetate from discarded cigarette filters and cotton comber noil, into rotor-spun yarn, and re-analyses a 15-run Box-Behnken experiment with full quadratic response-surface models, ANOVA, leave-one-out validation and a bootstrap. "
    f"The corrected analysis predicts a tenacity of {S1['pred']['tenacity']:.2f} cN/tex at the desirability optimum, with the blend factor at the upper edge of the tested range.",
    f"We state plainly what the study does not show. The regression equations printed in an earlier version reproduced R2 = {AU['R2_printed_equation_on_data']:.2f} of tenacity variance rather than the {AU['R2_reported']:.2f} reported, and the paper corrects this. No mass balance, contaminant assay or confirmation run was available, so we claim spinnability and a corrected optimisation, not recovery efficiency or product safety.",
    "The manuscript is not under consideration elsewhere. An AI assistant was used for code, figures and drafting under our direction, as disclosed in the Declarations; we are responsible for the content.",
    "Sincerely,",
    "[AUTHORS: corresponding author name, affiliation and e-mail]",
]:
    d.add_paragraph(t)
d.save(C.ROOT / "output" / "cover_letter.docx")
print("cover letter written")
