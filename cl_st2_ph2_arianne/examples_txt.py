#!/usr/bin/env python3
"""
Generate plaintext example files for each factor pole.

This script mirrors the corrected examples.py selection logic:
    - reads the same scores_only table
    - ranks groups using means_group_f<n>.tsv
    - positive pole: groups ranked by descending mean
    - negative pole: groups ranked by ascending mean
    - top group → 20 examples
    - all other groups → 10 examples each
    - skips rows where the factor score == 0
    - uses source/model, not group, to locate corpus folders

Outputs:
    examples_txt/f<n>_<pole>/f<n>_<pole>_001.txt

Also uses:
    examples/score_details.txt

to append loading words for each selected text.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

# ============================================================
# PATHS
# ============================================================
SCORES_FILE = Path("sas/output_cl_st2_ph2_arianne/cl_st2_ph2_arianne_scores_only.tsv")
MEANS_PATTERN = "sas/output_cl_st2_ph2_arianne/means_group_f{dim}.tsv"

FILE_IDS_PATH = Path("file_ids.txt")
SCORE_DETAILS = Path("examples/score_details.txt")

TAGGED_BASE = Path("corpus/07_tagged")
FULLTEXT_ROOT = Path("corpus")
OUT_ROOT = Path("examples_txt")

OUT_ROOT.mkdir(exist_ok=True, parents=True)

# ============================================================
# LOAD FILE-ID → FILENAME MAP
# ============================================================
def load_id_map(path: Path) -> dict[str, str]:
    """
    Load file_ids.txt.

    Expected format:
        t000001 t001_gemini.txt

    Returns:
        {
            "t000001": "t001_gemini.txt",
            ...
        }
    """
    if not path.exists():
        raise SystemExit(f"ERROR: required file missing: {path}")

    out: dict[str, str] = {}

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            file_id, fname = line.split(maxsplit=1)
            out[file_id.strip()] = fname.strip()

    return out


id_map = load_id_map(FILE_IDS_PATH)

# ============================================================
# LOAD SCORES
# ============================================================
if not SCORES_FILE.exists():
    raise SystemExit(f"ERROR: required file missing: {SCORES_FILE}")

scores_df = pd.read_csv(SCORES_FILE, sep="\t")

# Normalize core string fields, matching corrected examples.py behavior.
for c in ("filename", "group", "source", "model"):
    if c in scores_df.columns:
        scores_df[c] = scores_df[c].astype(str).str.strip()
    else:
        raise SystemExit(f"ERROR: expected column '{c}' missing in {SCORES_FILE}")

# ============================================================
# FACTOR COUNT
# ============================================================
factor_cols = [c for c in scores_df.columns if re.fullmatch(r"fac\d+", c)]
factor_cols = sorted(factor_cols, key=lambda c: int(c.replace("fac", "")))

if not factor_cols:
    raise SystemExit(f"ERROR: no factor columns 'fac<n>' found in {SCORES_FILE}")

num_factors = len(factor_cols)
print(f"Detected {num_factors} factors.\n")

# ============================================================
# LOAD LOADING WORDS FROM examples/score_details.txt
# ============================================================
def parse_score_details(path: Path, *, num_factors: int) -> dict[str, dict[str, list[str]]]:
    """
    Parse examples/score_details.txt.

    Returns:
        loading_words[tid]["f<n>_pos" or "f<n>_neg"] -> list[str]

    Important:
        Keep regex matches confined to one line. Do not use \\s* after the
        colon, because \\s can consume newlines and accidentally capture the
        next "f<n> score" line when the loading-word line is empty.
    """
    if not path.exists():
        raise SystemExit(
            f"ERROR: required file missing: {path}\n"
            "Run `python score_details.py` first."
        )

    out: dict[str, dict[str, list[str]]] = {}

    txt = path.read_text(encoding="utf-8")
    blocks = txt.split("=============================================")

    for block in blocks:
        m = re.search(r"^text ID:[ \t]*(t\d+)[ \t]*$", block, flags=re.MULTILINE)
        if not m:
            continue

        tid = m.group(1)
        out[tid] = {}

        for f in range(1, num_factors + 1):
            mp = re.search(
                rf"^f{f} pos words \(N=\d+\):[ \t]*(.*)$",
                block,
                flags=re.MULTILINE,
            )
            mn = re.search(
                rf"^f{f} neg words \(N=\d+\):[ \t]*(.*)$",
                block,
                flags=re.MULTILINE,
            )

            pos = mp.group(1).split(",") if mp else []
            neg = mn.group(1).split(",") if mn else []

            out[tid][f"f{f}_pos"] = [w.strip() for w in pos if w.strip()]
            out[tid][f"f{f}_neg"] = [w.strip() for w in neg if w.strip()]

    return out


loading_words = parse_score_details(SCORE_DETAILS, num_factors=num_factors)
missing_loading_words: set[tuple[str, str]] = set()

# ============================================================
# PATH RESOLUTION
# ============================================================
def corpus_folder_from_row(row: pd.Series) -> str | None:
    """
    Return the real corpus folder name for a score row.

    Important:
        The statistical group may be:
            human
            persona_gemini
            persona_gpt
            persona_grok
            plain_gemini
            plain_gpt
            plain_grok

        But the tagged corpus folders are organised by actual source/model:
            corpus/07_tagged/human
            corpus/07_tagged/gemini
            corpus/07_tagged/gpt
            corpus/07_tagged/grok

    Therefore, do not use row["group"] as the filesystem folder.
    """
    source = str(row["source"]).strip().lower()
    model = str(row["model"]).strip().lower()

    if source == "human":
        return "human"

    if not model or model == "nan":
        return None

    return model


def locate_tagged_text(row: pd.Series) -> Path | None:
    """
    Locate the tagged text file using the same logic as corrected examples.py.
    """
    tid = str(row["filename"]).strip()
    fname = id_map.get(tid)

    if not fname:
        return None

    folder = corpus_folder_from_row(row)

    if not folder:
        return None

    return TAGGED_BASE / folder / Path(fname).name


def locate_fulltext(row: pd.Series) -> Path | None:
    """
    Locate the corresponding full transcript.

    This uses source/model rather than group.

    The current project may contain either:
        corpus/05_gemini
        corpus/05_gpt
        corpus/05_grok
        corpus/05_human

    or, in expanded versions:
        corpus/05_persona_gemini
        corpus/05_plain_gemini
        etc.

    So we try source/model-based candidates first, then group-based candidates as
    fallbacks for full text only.
    """
    tid = str(row["filename"]).strip()
    fname = id_map.get(tid)

    if not fname:
        return None

    fname = Path(fname).name

    source = str(row["source"]).strip().lower()
    model = str(row["model"]).strip().lower()
    group = str(row["group"]).strip().lower()

    if source == "human":
        candidates = [
            FULLTEXT_ROOT / "05_human" / fname,
            FULLTEXT_ROOT / "06_clean_human" / fname,
            ]
    else:
        candidates = [
            FULLTEXT_ROOT / f"05_{model}" / fname,
            FULLTEXT_ROOT / f"06_clean_{model}" / fname,
            FULLTEXT_ROOT / f"05_{group}" / fname,
            FULLTEXT_ROOT / f"06_clean_{group}" / fname,
            ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    # Return most likely candidate even if missing, to make reports informative.
    return candidates[0] if candidates else None

# ============================================================
# OUTPUT HELPERS
# ============================================================
def clear_old_examples(out_dir: Path, label: str) -> None:
    """
    Remove old generated plaintext examples for this label.

    This prevents stale files remaining when a later run writes fewer examples.
    """
    if not out_dir.exists():
        return

    for old_file in out_dir.glob(f"{label}_*.txt"):
        old_file.unlink()


def record_missing_file(
        missing_files: set[str],
        *,
        row: pd.Series,
        kind: str,
        attempted_path: Path | None,
) -> None:
    """
    Store an informative missing-file report entry.
    """
    tid = str(row["filename"]).strip()
    mapped_fname = id_map.get(tid, "<not in file_ids.txt>")

    missing_files.add(
        "\t".join(
            [
                f"kind={kind}",
                f"filename={tid}",
                f"mapped_fname={mapped_fname}",
                f"group={row['group']}",
                f"source={row['source']}",
                f"model={row['model']}",
                f"path={attempted_path}",
            ]
        )
    )


def write_plaintext_example(
        *,
        outfile: Path,
        tid: str,
        group: str,
        source: str,
        model: str,
        fulltext_path: Path,
        label: str,
        score_value,
        lw: list[str],
) -> None:
    """
    Write one plaintext example file.
    """
    header: list[str] = [
        f"Text ID: {tid}",
        f"Group:   {group}",
        f"Source:  {source}",
        f"Model:   {model}",
        f"File:    {fulltext_path}",
        "",
        f"Score ({label}): {score_value}",
        f"Loading words ({label}), N={len(lw)}: {', '.join(lw)}",
        "",
        "============================================================",
        "",
    ]

    body = fulltext_path.read_text(encoding="utf-8", errors="ignore")
    outfile.write_text("\n".join(header) + body, encoding="utf-8")

# ============================================================
# MAIN SELECTION LOGIC
# ============================================================
missing_files: set[str] = set()

for fac_num in range(1, num_factors + 1):
    col = f"fac{fac_num}"

    if col not in scores_df.columns:
        raise SystemExit(f"ERROR: expected factor score column '{col}' missing in {SCORES_FILE}")

    means_file = Path(MEANS_PATTERN.format(dim=fac_num))

    if not means_file.exists():
        raise SystemExit(f"ERROR: required means file missing: {means_file}")

    means_df = pd.read_csv(means_file, sep="\t")

    mean_col = f"Mean fac{fac_num}"

    if "group" not in means_df.columns:
        raise SystemExit(f"ERROR: expected column 'group' missing in {means_file}")

    if mean_col not in means_df.columns:
        raise SystemExit(f"ERROR: expected column '{mean_col}' missing in {means_file}")

    means_df["group"] = means_df["group"].astype(str).str.strip()
    group_means = dict(zip(means_df["group"], means_df[mean_col]))

    for pole, ascending in (("pos", False), ("neg", True)):
        label = f"f{fac_num}_{pole}"
        print(f"→ {label}: selecting by group means (col={col}, ascending={ascending})")

        ranked_groups = sorted(
            group_means.keys(),
            key=lambda g: group_means[g],
            reverse=not ascending,
        )

        if not ranked_groups:
            raise SystemExit(f"ERROR: no groups found in {means_file}")

        top_group = ranked_groups[0]
        other_groups = ranked_groups[1:]

        sorted_df = scores_df.sort_values(by=col, ascending=ascending)

        out_dir = OUT_ROOT / label
        out_dir.mkdir(parents=True, exist_ok=True)
        clear_old_examples(out_dir, label)

        ex_id = 1

        # --------------------------------------------------------
        # TOP GROUP — 20 EXAMPLES
        # --------------------------------------------------------
        tg_df = sorted_df[sorted_df["group"] == top_group]

        for _, row in tg_df.iterrows():
            if row[col] == 0:
                continue

            if ex_id > 20:
                break

            tagged_path = locate_tagged_text(row)
            if not tagged_path or not tagged_path.exists():
                record_missing_file(
                    missing_files,
                    row=row,
                    kind="tagged",
                    attempted_path=tagged_path,
                )
                continue

            fulltext_path = locate_fulltext(row)
            if not fulltext_path or not fulltext_path.exists():
                record_missing_file(
                    missing_files,
                    row=row,
                    kind="fulltext",
                    attempted_path=fulltext_path,
                )
                continue

            tid = str(row["filename"]).strip()

            lw = loading_words.get(tid, {}).get(label)
            if lw is None:
                missing_loading_words.add((tid, label))
                lw = []

            outfile = out_dir / f"{label}_{ex_id:03d}.txt"

            write_plaintext_example(
                outfile=outfile,
                tid=tid,
                group=str(row["group"]).strip(),
                source=str(row["source"]).strip(),
                model=str(row["model"]).strip(),
                fulltext_path=fulltext_path,
                label=label,
                score_value=row[col],
                lw=lw,
            )

            ex_id += 1

        # --------------------------------------------------------
        # OTHER GROUPS — 10 EACH
        # --------------------------------------------------------
        for grp in other_groups:
            grp_df = sorted_df[sorted_df["group"] == grp]

            count = 0

            for _, row in grp_df.iterrows():
                if row[col] == 0:
                    continue

                if count >= 10:
                    break

                tagged_path = locate_tagged_text(row)
                if not tagged_path or not tagged_path.exists():
                    record_missing_file(
                        missing_files,
                        row=row,
                        kind="tagged",
                        attempted_path=tagged_path,
                    )
                    continue

                fulltext_path = locate_fulltext(row)
                if not fulltext_path or not fulltext_path.exists():
                    record_missing_file(
                        missing_files,
                        row=row,
                        kind="fulltext",
                        attempted_path=fulltext_path,
                    )
                    continue

                tid = str(row["filename"]).strip()

                lw = loading_words.get(tid, {}).get(label)
                if lw is None:
                    missing_loading_words.add((tid, label))
                    lw = []

                outfile = out_dir / f"{label}_{ex_id:03d}.txt"

                write_plaintext_example(
                    outfile=outfile,
                    tid=tid,
                    group=str(row["group"]).strip(),
                    source=str(row["source"]).strip(),
                    model=str(row["model"]).strip(),
                    fulltext_path=fulltext_path,
                    label=label,
                    score_value=row[col],
                    lw=lw,
                )

                count += 1
                ex_id += 1

        print(f"  ✓ Wrote {ex_id - 1} examples for {label}\n")

# ============================================================
# REPORTS
# ============================================================
missing_files_path = Path("missing_files_txt.txt")

if missing_files:
    missing_files_path.write_text("\n".join(sorted(missing_files)), encoding="utf-8")
    print(f"⚠ Missing files written to {missing_files_path}")
else:
    if missing_files_path.exists():
        missing_files_path.unlink()
    print("✓ No missing files for plaintext examples.")

missing_loading_words_path = Path("missing_loading_words.txt")

if missing_loading_words:
    missing_loading_words_path.write_text(
        "\n".join(f"{tid}\t{label}" for tid, label in sorted(missing_loading_words)),
        encoding="utf-8",
    )
    print(f"⚠ Missing loading words written to {missing_loading_words_path}")
else:
    if missing_loading_words_path.exists():
        missing_loading_words_path.unlink()
    print("✓ No missing loading-word records.")

print("\n✓ Done! All plaintext examples written to examples_txt/")