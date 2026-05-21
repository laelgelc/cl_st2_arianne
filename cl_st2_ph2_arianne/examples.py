#!/usr/bin/env python3
"""
Generate example text extracts based on highest/lowest factor scores by group.

For each factor:
    - positive pole: groups ranked by descending mean
    - negative pole: groups ranked by ascending mean
    - take top group → 20 examples
    - all other groups → 10 examples each
    - skip any file where the factor score == 0

Requires SAS output:
    sas/output_cl_st2_ph2_arianne/means_group_f<n>.tsv
    sas/output_cl_st2_ph2_arianne/cl_st2_ph2_arianne_scores_only.tsv

Requires:
    factors/f<n>_pos.txt
    factors/f<n>_neg.txt

Requires:
    file_ids.txt mapping t000001 → tagged filename

Expected tagged corpus folders:
    corpus/07_tagged/gemini
    corpus/07_tagged/gpt
    corpus/07_tagged/grok
    corpus/07_tagged/human
"""

import re
from pathlib import Path

import pandas as pd

# =============================================================================
# PATHS
# =============================================================================
BASE = Path("corpus/07_tagged")
FACTOR_FOLDER = Path("factors")
EXAMPLES_DIR = Path("examples")
EXAMPLES_DIR.mkdir(exist_ok=True)

SCORES_FILE = Path("sas/output_cl_st2_ph2_arianne/cl_st2_ph2_arianne_scores_only.tsv")
MEANS_PATTERN = "sas/output_cl_st2_ph2_arianne/means_group_f{dim}.tsv"

FILE_IDS_PATH = Path("file_ids.txt")

# =============================================================================
# STOP WORDS THAT MUST NOT BE BOLD
# =============================================================================
STOPLIST = {"edith", "doorbell", "michael", "recorded", "attempt", "request"}

# =============================================================================
# LOAD FILE-ID → FILENAME MAP
# =============================================================================
id_map = {}

with open(FILE_IDS_PATH, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        file_id, fname = line.split(maxsplit=1)
        id_map[file_id] = fname

# =============================================================================
# LOAD SCORES
# =============================================================================
scores_df = pd.read_csv(SCORES_FILE, sep="\t")

# Ensure columns exist and are clean strings
for required_col in ("filename", "group", "source", "model"):
    if required_col not in scores_df.columns:
        raise ValueError(f"Required column missing from scores file: {required_col}")

scores_df["filename"] = scores_df["filename"].astype(str).str.strip()
scores_df["group"] = scores_df["group"].astype(str).str.strip()
scores_df["source"] = scores_df["source"].astype(str).str.strip()
scores_df["model"] = scores_df["model"].astype(str).str.strip()

# =============================================================================
# FIND FACTOR COUNT
# =============================================================================
factor_cols = [c for c in scores_df.columns if re.fullmatch(r"fac\d+", c)]
factor_cols = sorted(factor_cols, key=lambda c: int(c.replace("fac", "")))

num_factors = len(factor_cols)

if num_factors == 0:
    raise ValueError("No factor columns found. Expected columns named fac1, fac2, etc.")

print(f"Detected {num_factors} factors.\n")

# =============================================================================
# PARSE PRIMARY LEMMAS
# =============================================================================
def load_primary_lemmas(pole_file: Path) -> set[str]:
    """
    Load primary lemmas from a factor pole file.

    The first line is skipped because it is assumed to be a header.
    Entries are expected to contain items like:
        lemma (...)
    """
    if not pole_file.exists():
        raise FileNotFoundError(f"Factor pole file not found: {pole_file}")

    lines = pole_file.read_text(encoding="utf-8").splitlines()[1:]
    items = " ".join(lines).split(",")

    lemmas = set()

    for item in items:
        item = item.strip()
        m = re.match(r"\(?(?P<lem>[A-Za-z0-9_-]+)\s*\(", item)
        if m:
            lemmas.add(m.group("lem"))

    return lemmas

# =============================================================================
# ANNOTATE TEXT
# =============================================================================
def annotate_text(text_path: Path, primary_lemmas: set[str]) -> tuple[list[str], set[str]]:
    """
    Read a tagged text file and return LaTeX-ready paragraphs plus matched lemmas.

    Expected tagged format per line:
        wordform tag lemma

    Only wordforms whose lemma is in primary_lemmas are bolded.
    """
    raw = text_path.read_text(encoding="utf-8")

    # Remove LaTeX-problematic braces/backslashes before token processing.
    raw = raw.replace("{", "").replace("}", "").replace("\\", "")

    tokens = []
    matched = set()

    for line in raw.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue

        wordform, tag, lemma = parts[0], parts[1], parts[2]

        if lemma in primary_lemmas and lemma not in STOPLIST:
            wordform = r"\textbf{" + wordform + "}"
            matched.add(lemma)

        tokens.append(wordform)

    text = " ".join(tokens)

    # Fix spacing issues.
    text = re.sub(r"\b([A-Za-z]+)\s+n['’]t\b", r"\1n't", text)
    text = re.sub(r"\s+([,.!?])", r"\1", text)
    text = re.sub(r'\s+"', '"', text)
    text = re.sub(r'"\s+', '"', text)

    # Escape LaTeX specials.
    for ch, rep in {"$": r"\$", "#": r"\#", "&": r"\&", "_": r"\_"}.items():
        text = text.replace(ch, rep)

    # Break sentences into paragraphs.
    paras = re.split(r"([.!?])\s+(?=[A-Z])", text)
    paras = ["".join(paras[i:i + 2]).strip() for i in range(0, len(paras), 2)]
    paras = [p for p in paras if p]

    return paras, matched

# =============================================================================
# LOCATE TEXT FILE BASED ON SOURCE / MODEL
# =============================================================================
def locate_text(row: pd.Series) -> Path | None:
    """
    Locate the tagged text file for a score row.

    Important:
        The statistical group values may be things like:
            human
            persona_gemini
            persona_gpt
            persona_grok

        But the actual tagged folders are:
            corpus/07_tagged/human
            corpus/07_tagged/gemini
            corpus/07_tagged/gpt
            corpus/07_tagged/grok

        Therefore we do NOT use row["group"] as the folder name.
        We use:
            - human → human
            - AI rows → row["model"]
    """
    fname = id_map.get(row["filename"])
    if not fname:
        return None

    source = str(row["source"]).strip().lower()
    model = str(row["model"]).strip().lower()

    if source == "human":
        group_folder = "human"
    else:
        group_folder = model

    if not group_folder or group_folder == "nan":
        return None

    return BASE / group_folder / fname

# =============================================================================
# OUTPUT HELPERS
# =============================================================================
def latex_escape_filename(fname: str) -> str:
    """Escape underscores in filenames for LaTeX display."""
    return fname.replace("_", r"\_")


def latex_escape_group(group: str) -> str:
    """Escape underscores in group labels for LaTeX display."""
    return group.replace("_", r"\_")


def record_missing(missing_files: set[str], row: pd.Series, tpath: Path | None) -> None:
    """
    Add an informative missing-file record.

    This makes it much easier to diagnose whether files are being searched for in
    the wrong corpus folder.
    """
    mapped_fname = id_map.get(row["filename"], "<not in file_ids.txt>")

    missing_files.add(
        "\t".join(
            [
                f"filename={row['filename']}",
                f"mapped_fname={mapped_fname}",
                f"group={row['group']}",
                f"source={row['source']}",
                f"model={row['model']}",
                f"path={tpath}",
            ]
        )
    )


def write_example(
        out_file: Path,
        env_title: str,
        env_label: str,
        paras: list[str],
        matched: set[str],
) -> None:
    """Write one LaTeX textsample environment."""
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(r"\begin{textsample}{" + env_title + r"}  \label{" + env_label + "}" + "\n")
        f.write("\n".join(paras))
        f.write("\n" * 2)
        f.write("% matched lemmas: " + ", ".join(sorted(matched)) + "\n")
        f.write(r"\end{textsample}" + "\n")


def clear_old_examples(out_dir: Path, label: str) -> None:
    """
    Remove old generated .tex files for this label.

    This prevents stale files from previous runs remaining in the folder if the
    new run writes fewer examples.
    """
    if not out_dir.exists():
        return

    for old_file in out_dir.glob(f"{label}_*.tex"):
        old_file.unlink()

# =============================================================================
# SELECT EXAMPLES
# =============================================================================
missing_files = set()

for fac_num in range(1, num_factors + 1):
    col = f"fac{fac_num}"

    means_file = Path(MEANS_PATTERN.format(dim=fac_num))
    if not means_file.exists():
        raise FileNotFoundError(f"Means file not found: {means_file}")

    means_df = pd.read_csv(means_file, sep="\t")

    mean_col = f"Mean fac{fac_num}"
    if "group" not in means_df.columns:
        raise ValueError(f"'group' column missing from means file: {means_file}")
    if mean_col not in means_df.columns:
        raise ValueError(f"'{mean_col}' column missing from means file: {means_file}")

    means_df["group"] = means_df["group"].astype(str).str.strip()
    group_means = dict(zip(means_df["group"], means_df[mean_col]))

    # =========================================================================
    # TWO POLES: POSITIVE DESCENDING, NEGATIVE ASCENDING
    # =========================================================================
    for pole, ascending in (("pos", False), ("neg", True)):
        label = f"f{fac_num}_{pole}"
        print(f"→ {label}: selecting by group means (col={col}, ascending={ascending})")

        # Rank groups by their factor mean.
        ranked_groups = sorted(
            group_means.keys(),
            key=lambda g: group_means[g],
            reverse=not ascending,
        )

        top_group = ranked_groups[0]
        other_groups = ranked_groups[1:]

        # Load primary lemmas for this pole.
        primary_lemmas = load_primary_lemmas(FACTOR_FOLDER / f"{label}.txt")

        # Sort entire scores dataframe by factor score in the relevant direction.
        sorted_df = scores_df.sort_values(by=col, ascending=ascending)

        out_dir = EXAMPLES_DIR / label
        out_dir.mkdir(parents=True, exist_ok=True)
        clear_old_examples(out_dir, label)

        ex_id = 1

        # ---------------------------------------------------------------------
        # TOP GROUP — 20 EXAMPLES
        # ---------------------------------------------------------------------
        tg_df = sorted_df[sorted_df["group"] == top_group]

        for _, row in tg_df.iterrows():
            if row[col] == 0:
                continue

            if ex_id > 20:
                break

            tpath = locate_text(row)

            if not tpath or not tpath.exists():
                record_missing(missing_files, row, tpath)
                continue

            paras, matched = annotate_text(tpath, primary_lemmas)

            raw_fname = id_map.get(row["filename"], row["filename"])
            latex_fname = latex_escape_filename(raw_fname)
            group_latex = latex_escape_group(top_group)

            env_title = (
                f"{pole.upper()} Dim {fac_num} – {group_latex} – "
                f"Score {row[col]:.2f} – {latex_fname}"
            )
            env_label = f"ex:{label}_{ex_id:03d}"

            out_file = out_dir / f"{label}_{ex_id:03d}.tex"

            write_example(
                out_file=out_file,
                env_title=env_title,
                env_label=env_label,
                paras=paras,
                matched=matched,
            )

            ex_id += 1

        # ---------------------------------------------------------------------
        # OTHER GROUPS — 10 EXAMPLES EACH
        # ---------------------------------------------------------------------
        for grp in other_groups:
            grp_df = sorted_df[sorted_df["group"] == grp]

            count = 0

            for _, row in grp_df.iterrows():
                if row[col] == 0:
                    continue

                if count >= 10:
                    break

                tpath = locate_text(row)

                if not tpath or not tpath.exists():
                    record_missing(missing_files, row, tpath)
                    continue

                paras, matched = annotate_text(tpath, primary_lemmas)

                raw_fname = id_map.get(row["filename"], row["filename"])
                latex_fname = latex_escape_filename(raw_fname)
                group_latex = latex_escape_group(grp)

                env_title = (
                    f"{pole.upper()} Dim {fac_num} – {group_latex} – "
                    f"Score {row[col]:.2f} – {latex_fname}"
                )
                env_label = f"ex:{label}_{ex_id:03d}"

                out_file = out_dir / f"{label}_{ex_id:03d}.tex"

                write_example(
                    out_file=out_file,
                    env_title=env_title,
                    env_label=env_label,
                    paras=paras,
                    matched=matched,
                )

                count += 1
                ex_id += 1

        print(f"  ✓ Wrote {ex_id - 1} examples for {label}\n")

# =============================================================================
# MISSING FILE REPORT
# =============================================================================
missing_path = Path("missing_files.txt")

if missing_files:
    missing_path.write_text("\n".join(sorted(missing_files)), encoding="utf-8")
    print("⚠ Missing files written to missing_files.txt")
else:
    if missing_path.exists():
        missing_path.unlink()
    print("✓ No missing files.")

# =============================================================================
# BUILD MASTER LATEX FILE
# =============================================================================
top_header_path = EXAMPLES_DIR / "top_header"

if not top_header_path.exists():
    raise FileNotFoundError(
        "examples/top_header is missing. Create examples/top_header before compiling LaTeX."
    )

master = EXAMPLES_DIR / "examples.tex"

with open(top_header_path, "r", encoding="utf-8") as f:
    preamble = f.read()

with open(master, "w", encoding="utf-8") as out:
    out.write(preamble + "\n\n")
    out.write(r"\begin{document}" + "\n\n")
    out.write(r"\maketitle" + "\n\n")
    out.write(r"\tableofcontents" + "\n\n")

    for fac_num in range(1, num_factors + 1):
        for pole in ("pos", "neg"):
            label = f"f{fac_num}_{pole}"
            out.write(r"\section{" + f"{pole.upper()} Dim {fac_num}" + "}\n\n")

            for tex in sorted((EXAMPLES_DIR / label).glob("*.tex")):
                out.write(r"\input{" + str(tex.resolve()) + "}\n")

    out.write("\n" + r"\end{document}" + "\n")

print("✓ Created examples/examples.tex")