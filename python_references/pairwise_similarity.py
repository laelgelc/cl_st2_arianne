#!/usr/bin/env python3
"""
FAST pairwise text similarity using difflib with multiprocessing.
Workers read files themselves — no large IPC transfers.

Usage:
    python pairwise_similarity_fast.py \
        --input corpus/01_selected \
        --output similarities.tsv \
        --workers 6
"""

import argparse
from pathlib import Path
import difflib
import itertools
import csv
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm


# ---------------- Worker function ----------------
def compare_pair(args):
    f1, f2 = args
    try:
        t1 = Path(f1).read_text(encoding="utf-8", errors="ignore")
        t2 = Path(f2).read_text(encoding="utf-8", errors="ignore")
        ratio = difflib.SequenceMatcher(None, t1, t2).ratio()
        return f1, f2, ratio
    except Exception as e:
        return f1, f2, f"ERROR: {e}"


# ---------------- Main ----------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    input_dir = Path(args.input)
    out_file = Path(args.output)

    files = sorted(input_dir.glob("*.txt"))
    print(f"Found {len(files)} text files.")

    # Prepare filename pairs only
    pairs = [(str(f1), str(f2)) for f1, f2 in itertools.combinations(files, 2)]
    total = len(pairs)

    print(f"Total comparisons: {total}")
    print(f"Using {args.workers} workers...\n")

    with ProcessPoolExecutor(max_workers=args.workers) as pool, \
            out_file.open("w", encoding="utf-8", newline="") as out:

        writer = csv.writer(out, delimiter="\t")
        writer.writerow(["file1", "file2", "similarity"])

        for f1, f2, ratio in tqdm(
            pool.map(compare_pair, pairs),
            total=total,
            desc="Comparisons",
            smoothing=0.01
        ):
            writer.writerow([Path(f1).name, Path(f2).name, ratio])

    print(f"\nDone. Saved to {out_file}")


if __name__ == "__main__":
    main()
