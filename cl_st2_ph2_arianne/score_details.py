#!/usr/bin/env python3
import re
from pathlib import Path

import pandas as pd

# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------
SAS_BASE = Path("sas/output_cl_st2_ph2_arianne")
SCORES_FILE = SAS_BASE / "cl_st2_ph2_arianne_scores.tsv"

# word_labels_format.sas is generated in sas/, not usually in sas/output_...
WORD_LABELS_FILE = Path("sas/word_labels_format.sas")

VARID_DIR = Path("factors/var_id")

FILE_IDS = Path("file_ids.txt")
OUTFILE = Path("examples/score_details.txt")

OUTFILE.parent.mkdir(exist_ok=True)

# ------------------------------------------------------------
# Validate required inputs
# ------------------------------------------------------------
if not SCORES_FILE.exists():
    raise FileNotFoundError(f"Scores file not found: {SCORES_FILE}")

if not WORD_LABELS_FILE.exists():
    raise FileNotFoundError(f"Word labels file not found: {WORD_LABELS_FILE}")

if not FILE_IDS.exists():
    raise FileNotFoundError(f"File ID mapping not found: {FILE_IDS}")

if not VARID_DIR.exists():
    raise FileNotFoundError(f"Factor var_id directory not found: {VARID_DIR}")

# ------------------------------------------------------------
# Load SAS factor scores
# ------------------------------------------------------------
scores = pd.read_csv(SCORES_FILE, sep="\t")

if "filename" not in scores.columns:
    raise ValueError("Required column missing from scores file: filename")

scores["filename"] = scores["filename"].astype(str).str.strip()

# ------------------------------------------------------------
# Detect factor columns
# ------------------------------------------------------------
factor_cols = [c for c in scores.columns if re.fullmatch(r"fac\d+", c)]
factor_cols = sorted(factor_cols, key=lambda c: int(c.replace("fac", "")))

if not factor_cols:
    raise ValueError("No factor columns found. Expected columns named fac1, fac2, etc.")

factor_nums = [int(c.replace("fac", "")) for c in factor_cols]

print(f"Detected factors: {', '.join(factor_cols)}")

# ------------------------------------------------------------
# Load SAS variable lexicon: varID → word
# ------------------------------------------------------------
lex = {}
label_text = WORD_LABELS_FILE.read_text(encoding="utf-8")

for vid, word in re.findall(r'"(v\d{6})"\s*=\s*"([^"]+)"', label_text):
    lex[vid] = word

if not lex:
    raise ValueError(f"No variable labels found in {WORD_LABELS_FILE}")

# ------------------------------------------------------------
# Extract variable IDs that belong to positive/negative poles
# IDs outside parentheses = main contributors
# ------------------------------------------------------------
def load_var_ids(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Factor var_id file not found: {path}")

    text = path.read_text(encoding="utf-8")

    all_ids = re.findall(r"v\d{6}", text)

    inside = set()
    for block in re.findall(r"\([^)]*\)", text):
        inside.update(re.findall(r"v\d{6}", block))

    outside = [vid for vid in all_ids if vid not in inside]

    # Preserve order and remove duplicates.
    seen = set()
    final = []

    for vid in outside:
        if vid not in seen:
            seen.add(vid)
            final.append(vid)

    return final

# ------------------------------------------------------------
# Load var IDs for factors
# ------------------------------------------------------------
varlist_pos = {}
varlist_neg = {}

for f in factor_nums:
    posfile = VARID_DIR / f"f{f}_pos_var_id.txt"
    negfile = VARID_DIR / f"f{f}_neg_var_id.txt"

    varlist_pos[f] = load_var_ids(posfile)
    varlist_neg[f] = load_var_ids(negfile)

# ------------------------------------------------------------
# Load file_ids.txt mapping
# ------------------------------------------------------------
id_map = {}

with open(FILE_IDS, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        fid, fname = line.split(maxsplit=1)
        id_map[fid.strip()] = fname.strip()

# ------------------------------------------------------------
# Main output
# ------------------------------------------------------------
with open(OUTFILE, "w", encoding="utf-8") as out:
    for _, row in scores.iterrows():
        fid = str(row["filename"]).strip()
        fname = id_map.get(fid, "UNKNOWN")

        out.write(f"text ID: {fid}\n")
        out.write(f"filename: {fname}\n\n")

        for f in factor_nums:
            fac_col = f"fac{f}"

            score = row[fac_col]
            out.write(f"f{f} score: {score}\n")

            # POS
            pos_ids = varlist_pos[f]
            pos_used_ids = [vid for vid in pos_ids if row.get(vid, 0) != 0]
            pos_words = [lex.get(vid, vid) for vid in pos_used_ids]

            out.write(
                f"f{f} pos words (N={len(pos_used_ids)}): "
                f"{', '.join(pos_words)}\n"
            )

            # NEG
            neg_ids = varlist_neg[f]
            neg_used_ids = [vid for vid in neg_ids if row.get(vid, 0) != 0]
            neg_words = [lex.get(vid, vid) for vid in neg_used_ids]

            out.write(
                f"f{f} neg words (N={len(neg_used_ids)}): "
                f"{', '.join(neg_words)}\n\n"
            )

        out.write("=============================================\n\n")

print(f"\n✓ Finished. Output written to:\n  {OUTFILE}\n")