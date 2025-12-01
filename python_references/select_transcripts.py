#!/usr/bin/env python3
"""
Select all transcripts that:
  1. Contain a line beginning with 'Transcript' (case-insensitive), and
  2. Have at least N total words (default: 4000)

Word count is computed on the *entire file* — no extraction is done.

Detection is robust:
 - Matches "Transcript", "Transcript:", "Transcript of...", 
   uppercase versions, leading spaces, etc.

Process:
 1. Check for transcript header.
 2. Count all words in the file.
 3. Keep files with >= 4000 words.
 4. Copy original files to output folder.
"""

import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil
import re


# ------------------------------------------------------------
# Worker: detect transcript header AND count all words
# ------------------------------------------------------------
def check_and_count_words(file_path: Path, minwords: int):
    """
    Return (file_path, word_count) if file contains a transcript header.
    If no transcript header, return (file_path, -1) to skip.
    """
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()

        # robust transcript header pattern
        header_pattern = re.compile(r"^\s*transcript\b", re.IGNORECASE)

        found_header = any(header_pattern.match(line) for line in lines)

        if not found_header:
            return file_path, -1  # reject file entirely

        # Count ALL words in the entire file
        total_words = len(text.split())

        if total_words >= minwords:
            return file_path, total_words
        else:
            return file_path, -1  # below threshold, reject

    except Exception:
        return file_path, -1


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Select transcript files with >= MIN words and a transcript header."
    )
    parser.add_argument("--input", required=True, help="Input folder with .txt files")
    parser.add_argument("--output", required=True, help="Output folder")
    parser.add_argument("--workers", type=int, default=4, help="Number of worker threads")
    parser.add_argument("--minwords", type=int, default=4000,
                        help="Minimum total words required (default: 4000)")

    args = parser.parse_args()

    input_dir = Path(args.input).resolve()
    output_dir = Path(args.output).resolve()

    if not input_dir.exists():
        print("ERROR: Input directory does not exist.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    # Gather files
    files = list(input_dir.glob("*.txt"))
    total = len(files)
    print(f"Found {total} text files.\n")

    # ---------------- PARALLEL PROCESSING ---------------- #
    print(f"Checking transcript headers and counting words using {args.workers} workers...\n")

    kept = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(check_and_count_words, f, args.minwords): f for f in files
        }

        for future in as_completed(futures):
            file_path, count = future.result()
            if count >= 0:
                kept.append((file_path, count))

    print(f"Files meeting criteria (header + >= {args.minwords} words): {len(kept)}\n")

    if len(kept) == 0:
        print("No transcripts meet the minimum requirements.")
        return

    # ---------------- COPY ORIGINAL FILES ---------------- #
    print("Copying selected files...\n")

    for file_path, _ in kept:
        shutil.copy(file_path, output_dir / file_path.name)

    print(f"Done. {len(kept)} files written to: {output_dir}\n")


# ------------------------------------------------------------
if __name__ == "__main__":
    main()
