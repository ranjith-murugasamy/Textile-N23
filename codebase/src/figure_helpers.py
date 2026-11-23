"""Save every chart as results/figures/<name>.png (200 dpi) with an explanation file <name>.md beside it, and mirror
each PNG into output/ together with output/explanations.txt (one entry per PNG, naming the file).

usage in src/make_figures.py:
    from figure_helpers import save_figure, style
    style(); fig, ax = plt.subplots(); ...
    save_figure(fig, "fig_01_training_curves", "Training and validation loss ...", takeaway="Validation loss flattens after epoch 18 (0.41).")
Explanations must use numbers read from results/metrics.json, never typed by hand.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "figures"
OUTPUT = ROOT / "output"


def style():
    plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.grid": True, "grid.alpha": 0.3,
                         "figure.dpi": 150, "savefig.dpi": 200, "savefig.bbox": "tight", "axes.spines.top": False, "axes.spines.right": False})


def save_figure(fig, name: str, what_it_shows: str, takeaway: str = "", how_to_read: str = "", outdir: Path = OUT) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    png = outdir / f"{name}.png"
    fig.savefig(png)
    plt.close(fig)
    parts = [f"**What it shows.** {what_it_shows.strip()}"]
    if how_to_read:
        parts.append(f"**How to read it.** {how_to_read.strip()}")
    if takeaway:
        parts.append(f"**Key takeaway.** {takeaway.strip()}")
    (outdir / f"{name}.md").write_text("\n\n".join(parts) + "\n")
    export_to_output(outdir)
    return png


def save_metrics_png(headline: dict, name: str = "metrics_summary", outdir: Path = OUT, note: str = "") -> Path:
    """Render the headline metrics (from results/metrics.json) as a table image and explain it."""
    rows = [[k, f"{v:.3f}" if isinstance(v, float) else str(v)] for k, v in headline.items()]
    fig, ax = plt.subplots(figsize=(4.2, 0.45 * (len(rows) + 1)))
    ax.axis("off")
    tbl = ax.table(cellText=rows, colLabels=["Metric", "Value"], loc="center", cellLoc="left")
    tbl.auto_set_font_size(False); tbl.set_fontsize(9); tbl.scale(1, 1.4)
    for (r, _), cell in tbl.get_celld().items():
        if r == 0:
            cell.set_facecolor("#E7ECF2"); cell.set_text_props(weight="bold")
    summary = "; ".join(f"{k} = {v:.3f}" if isinstance(v, float) else f"{k} = {v}" for k, v in headline.items())
    return save_figure(fig, name, "Headline evaluation metrics of the final model on the held-out test set." + (" " + note if note else ""),
                       f"{summary}.", "Each row is one metric; values are copied from results/metrics.json.", outdir)


def export_to_output(figdir: Path = OUT, output: Path = OUTPUT) -> None:
    """Copy every chart PNG into output/ and rebuild output/explanations.txt (idempotent)."""
    output.mkdir(parents=True, exist_ok=True)
    entries = []
    for png in sorted(figdir.glob("*.png")):
        (output / png.name).write_bytes(png.read_bytes())
        md = png.with_suffix(".md")
        text = md.read_text().replace("**", "").strip() if md.exists() else "(no explanation written)"
        entries.append(f"File: {png.name}\n{text}\n")
    header = "Charts, graphs and metrics: explanations\n" + "=" * 40 + "\nEach entry names the PNG file in this folder that it explains.\n\n"
    (output / "explanations.txt").write_text(header + "\n".join(entries))
