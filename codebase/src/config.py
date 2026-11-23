"""Single place for paths, seeds and analysis settings."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"
TABLES = RESULTS / "tables"
FIGURES = RESULTS / "figures"

SEED = 20231123
N_BOOT = 2000
ALPHA = 0.05
DATA_FILE = RAW / "bbd_table3.csv"
DATA_SHA256 = "not pinned; computed by fetch_data.py"

# Coding: x = (actual - centre) / half-range
CENTRE = {"blend": 50.0, "roller": 5000.0, "rotor": 40000.0}
HALF = {"blend": 20.0, "roller": 1000.0, "rotor": 10000.0}
FACTORS = ["blend", "roller", "rotor"]
FACTOR_LABEL = {"blend": "Blend share, first-named fibre (%)", "roller": "Opening roller (rpm)", "rotor": "Rotor speed (rpm)"}

RESPONSES = ["tenacity", "elongation", "u_pct", "imperfections", "hairiness"]
COLUMN = {"tenacity": "tenacity_cN_tex", "elongation": "elongation_pct", "u_pct": "u_pct",
          "imperfections": "imperfections_per_km", "hairiness": "hairiness_index"}
LABEL = {"tenacity": "Tenacity (cN/tex)", "elongation": "Elongation (%)", "u_pct": "Unevenness U (%)",
         "imperfections": "Imperfections (per km)", "hairiness": "Hairiness index H"}
# desirability goals for the primary scenario (decided before the analysis)
GOALS = {"tenacity": "max", "elongation": "range", "u_pct": "min", "imperfections": "min", "hairiness": "min"}

# Equations printed in Table 4 of the draft (coded factors A=blend, B=roller, C=rotor); no quadratic terms.
PRINTED_EQ = {
    "tenacity":      dict(b0=8.80, A=0.9875, B=-0.0500, C=0.2125, AB=-0.001, AC=-0.0250, BC=0.1500, R2=0.9800),
    "elongation":    dict(b0=6.70, A=-0.9750, B=0.0625, C=-0.1875, AB=0.0250, AC=0.0250, BC=-0.1, R2=0.9887),
    "u_pct":         dict(b0=12.24, A=-0.7275, B=0.5112, C=-0.5338, AB=-0.1675, AC=-0.1725, BC=-0.7300, R2=0.9313),
    "imperfections": dict(b0=500.0, A=-35.25, B=4.75, C=-7.00, AB=0.5, AC=-2.00, BC=3.00, R2=0.9805),
    "hairiness":     dict(b0=6.28, A=-1.76, B=0.1150, C=-0.3962, AB=0.0250, AC=-0.1625, BC=0.16, R2=0.9861),
}
# Optimum and Table 5 values printed in the draft
PAPER_OPT = {"blend": 68.727, "roller": 4713.754, "rotor": 47430.327}
PAPER_TABLE5 = {"tenacity": 9.617, "elongation": 5.702, "u_pct": 11.098, "imperfections": 456.0, "hairiness": 4.37}
COTTON_BENCH = {"tenacity": 12.0, "elongation": 6.0, "u_pct": 12.5, "imperfections": 545.0, "hairiness": 4.70}
