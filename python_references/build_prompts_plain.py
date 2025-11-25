#!/usr/bin/env python3
import os
import re
from pathlib import Path

# -------------------------------------------
# CONFIG
# -------------------------------------------
DIR_BACKGROUND = Path("corpus/02_extracted")
DIR_SUMMARY    = Path("corpus/03_summary")
DIR_OUT        = Path("corpus/04_prompt_plain")

DIR_OUT.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = (
    "You are a person living during the COVID-19 pandemic in the USA.\n"
    "You're being interviewed for an oral history project.\n"
)

USER_PROMPT = (
    "I want you to answer the questions below. "
    "Output the exact question as given, followed immediately by your answer. "
    "Use the word 'Question' to label each question, and the word 'Answer' to label each answer. "
    "Respond to every question in order. Do not add new questions, and do not omit any.\n"
)

# -------------------------------------------
# HELPERS
# -------------------------------------------

def extract_questions(text):
    """
    Extracts all Questions from a summary file.
    Ignores Answer Summary sections entirely.
    Returns a list:
        ["Question: ...", "Question: ...", ...]
    """
    questions = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("Question:"):
            questions.append(line)
    return questions


# -------------------------------------------
# MAIN
# -------------------------------------------

def main():
    index_entries = []
    counter = 1

    for bg_file in sorted(DIR_BACKGROUND.glob("*_extracted.txt")):
        base = bg_file.stem.split("_")[0]

        # load summary file
        summary_file = DIR_SUMMARY / f"{base}_extracted_summarized.txt"
        if not summary_file.exists():
            continue

        summary_text = summary_file.read_text(encoding="utf-8", errors="ignore")
        questions = extract_questions(summary_text)
        if not questions:
            continue

        # BUILD FINAL PROMPT (only system and user prompt + questions)
        full_prompt = (
            f"SYSTEM PROMPT:\n{SYSTEM_PROMPT}\n"
            f"USER PROMPT:\n{USER_PROMPT}\n"
        )

        for q in questions:
            full_prompt += f"{q}\n\n"

        # Save to tXXX.txt
        out_name = f"t{counter:03d}.txt"
        (DIR_OUT / out_name).write_text(full_prompt, encoding="utf-8")

        index_entries.append(f"{out_name} {base}")
        counter += 1

    Path("file_index.txt").write_text("\n".join(index_entries), encoding="utf-8")
    print(f"Done. Created {counter-1} prompts in corpus/04_prompt_plain.")


if __name__ == "__main__":
    main()
