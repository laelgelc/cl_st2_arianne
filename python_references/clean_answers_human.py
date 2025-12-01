#!/usr/bin/env python3
import re
from pathlib import Path

# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
DIR_IN = Path("corpus/02_extracted")
DIR_OUT = Path("corpus/06_clean_human")
INDEX_FILE = Path("file_index.txt")

DIR_OUT.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Load file_index.txt mapping
# ---------------------------------------------------------
def load_index_map(index_path):
    """
    Reads file_index.txt which has lines like:
        t001.txt 00204690045c0943bbf20e39a31b8f298e0e9529
    Returns dict:
        { "00204690045c0943bbf20e39a31b8f298e0e9529" : "t001" }
    """
    mapping = {}
    for line in index_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        fname, hashval = line.split()
        stem = Path(fname).stem  # t001
        mapping[hashval] = stem
    return mapping


# ---------------------------------------------------------
# Extract answers from one file
# ---------------------------------------------------------
def extract_answers(text):
    """
    Extracts all Answer: sections.
    Accepts:
      Answer: <text here>
      Answer:
      <text here>
      <more text>
    Stops extraction at next "Question:" or EOF.
    Returns one string containing all answers (separated by blank lines).
    """

    answers = []
    lines = text.splitlines()
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i].strip()

        if line.startswith("Answer:"):
            # Case 1: Answer on same line
            after = line[7:].strip()

            if after:
                # Same-line answer
                collected = [after]
                i += 1

            else:
                # Answer content begins on next line(s)
                collected = []
                i += 1

            # Continue collecting until next Question or EOF
            while i < n and not lines[i].strip().startswith("Question:"):
                collected.append(lines[i].rstrip())
                i += 1

            # Clean trailing empty lines
            while collected and not collected[-1].strip():
                collected.pop()

            answers.append("\n".join(collected))

        else:
            i += 1

    return "\n\n".join(answers)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():
    # Load the hash → tXXX mapping
    mapping = load_index_map(INDEX_FILE)

    # Process each extracted file
    for infile in sorted(DIR_IN.glob("*_extracted.txt")):
        stem = infile.stem.replace("_extracted", "")  # the hash
        if stem not in mapping:
            print(f"[WARN] No mapping for {infile.name}")
            continue

        tname = mapping[stem]  # t001, t002, ...
        outname = f"{tname}_human.txt"
        outfile = DIR_OUT / outname

        text = infile.read_text(encoding="utf-8", errors="ignore")
        answers = extract_answers(text)

        outfile.write_text(answers + "\n", encoding="utf-8")
        print(f"[OK] {infile.name} → {outfile.name}")


if __name__ == "__main__":
    main()
