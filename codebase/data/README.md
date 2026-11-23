# Data

- **Name and version:** `raw/bbd_table3.csv`, the 15-run Box-Behnken table (Table 3) transcribed by hand from the author's own manuscript `Paper.docx` (supplied as `inputs/current_paper/Paper.docx`). Evidence-ladder step 1 (user data). The values are the rounded numbers printed in the manuscript, not the original unrounded laboratory records.
- **Source / citation:** the authors' own rotor-spinning trials (Coimbatore, India). The `blend_first_pct` column is the first number of the printed blend label (for example 70 in "70:30"); which fibre it refers to is contradictory in the draft (Methods: cellulose acetate; Table 3 header "CO:CBF": comber noil). See `audit.md` item 1.
- **Licence:** unpublished author data; not for redistribution beyond the authors' own submission.
- **Size and split rule:** 15 rows (12 edge points + 3 centre replicates: runs 10, 14, 15). No train/test split is possible; model adequacy uses leave-one-out PRESS and lack-of-fit instead. No confirmation-run data were supplied.
- **How to obtain it:** the file is part of the repository. `python src/fetch_data.py` verifies the SHA-256 and writes the coded design to `processed/`.
- **Also in `raw/`:** `user_image1..4` are the author's Fig. 1 (process flow), Fig. 3 (SEM), Fig. 2 (FTIR, as PNG) and Fig. 4 (TGA, as PNG), extracted from `Paper.docx`; they are reused unchanged in the manuscript. No numerical spectra or thermograms were supplied.
- **Not available (never invented):** mass balance, recovery yield, nicotine/metal assays, water/chemical/energy records, replicate yarn measurements, confirmation trial, the 100% cotton benchmark raw data.
- **Hardware:** Apple-silicon macOS laptop (analysis is a 15-row least-squares problem; the full pipeline runs in under a minute on CPU).
