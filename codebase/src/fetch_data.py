"""Verify the bundled Box-Behnken table and write the coded design to data/processed/."""
import hashlib
import sys

import pandas as pd

from config import CENTRE, DATA_FILE, FACTORS, HALF, PROCESSED


def load() -> pd.DataFrame:
    """Return the raw table with coded factor columns x_blend, x_roller, x_rotor."""
    df = pd.read_csv(DATA_FILE)
    df["blend"], df["roller"], df["rotor"] = df["blend_first_pct"], df["opening_roller_rpm"], df["rotor_rpm"]
    for f in FACTORS:
        df[f"x_{f}"] = (df[f] - CENTRE[f]) / HALF[f]
    return df


def main() -> int:
    if not DATA_FILE.is_file():
        print(f"missing {DATA_FILE}; see data/README.md", file=sys.stderr)
        return 1
    digest = hashlib.sha256(DATA_FILE.read_bytes()).hexdigest()
    df = load()
    assert len(df) == 15 and (df[[f"x_{f}" for f in FACTORS]].abs().max() <= 1).all()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED / "coded_design.csv", index=False)
    (PROCESSED / "raw_sha256.txt").write_text(digest + "\n")
    print(f"ok: {len(df)} runs, sha256={digest[:16]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
