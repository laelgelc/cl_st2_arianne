#!/usr/bin/env python3
import os
import re
import random
from pathlib import Path

# -------------------------------------------
# CONFIG
# -------------------------------------------
DIR_BACKGROUND = Path("corpus/02_extracted")
DIR_SUMMARY    = Path("corpus/03_summary")
DIR_OUT        = Path("corpus/04_prompt_persona")

DIR_OUT.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = (
    "You are a person living during the COVID-19 pandemic in the USA.\n"
    "You're being interviewed for an oral history project.\n"
)

USER_PROMPT = (
    "I want you to answer the questions below. Use the Answer Summary provided for "
    "each question as guidance and do not treat it as a script. "
    "It is only meant to shape the content of your response, not determine it. "
    "Output the exact question as given, followed immediately by your answer. "
    "Use the word 'Question' to label each question, and the word 'Answer' to label each answer. "
    "Adopt the persona described at the top of the text under 'Interviewee Background.' "
    "Respond to every question in order. Do not add new questions, and do not omit any.\n"
)

# -------------------------------------------
# HELPERS
# -------------------------------------------

def extract_background(text):
    """Extract Interviewee Background paragraph from 02_extracted."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("interviewee background"):
            start = i
            break
    if start is None:
        return None

    collected = [lines[start].strip()]
    for j in range(start + 1, len(lines)):
        if lines[j].strip() == "":
            break
        collected.append(lines[j].strip())

    return "\n".join(collected)

def extract_questions_and_summaries(text):
    """
    Extracts all Questions and their corresponding Answer Summary bullet points
    from a summary file, handling all formats:

    Formats handled:
      A. Answer Summary:
         - bullet
         - bullet

      B. Answer Summary: - bullet

      C. Multiple Answer Summary blocks per question

      D. Strange spacing / indentation

    Returns a list:
       [(question_text, [bullet1, bullet2, ...]), ...]
    """

    lines = text.splitlines()
    q_and_a = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # --- DETECT QUESTION ---
        if line.startswith("Question:"):
            question = line
            bullets = []
            i += 1

            # --- FOLLOWING BLOCKS UNTIL NEXT QUESTION OR EOF ---
            while i < len(lines) and not lines[i].strip().startswith("Question:"):
                cur = lines[i].strip()

                # --- DETECT "Answer Summary" line ---
                if cur.startswith("Answer Summary"):

                    # CASE B: bullets on same line
                    inline = re.findall(r"[•\-\*]\s+(.+)", cur)
                    for b in inline:
                        bullets.append(b.strip())

                    # CASE A/C: bullets on subsequent lines
                    j = i + 1
                    while j < len(lines) and lines[j].strip().startswith(("-", "•", "*")):
                        bullets.append(lines[j].lstrip("•-* ").strip())
                        j += 1

                    i = j
                    continue

                i += 1

            q_and_a.append((question, bullets))
            continue

        i += 1

    return q_and_a


# -------------------------------------------
# MAIN
# -------------------------------------------

def main():
    index_entries = []
    counter = 1

    for bg_file in sorted(DIR_BACKGROUND.glob("*_extracted.txt")):
        base = bg_file.stem.split("_")[0]

        # Load background
        bg_text = bg_file.read_text(encoding="utf-8", errors="ignore")
        background = extract_background(bg_text)
        if not background:
            continue

        summary_file = DIR_SUMMARY / f"{base}_extracted_summarized.txt"
        if not summary_file.exists():
            continue

        summary_text = summary_file.read_text(encoding="utf-8", errors="ignore")
        q_and_a = extract_questions_and_summaries(summary_text)
        if not q_and_a:
            continue

        # BUILD THE FULL PROMPT
        full_prompt = (
            f"SYSTEM PROMPT:\n{SYSTEM_PROMPT}\n"
            f"USER PROMPT:\n{USER_PROMPT}\n"
            f"{background}\n\n"
        )

        for (question, bullets) in q_and_a:
            full_prompt += f"{question}\n\n"
            full_prompt += "Answer Summary Points:\n"
            selected = random.sample(bullets, min(3, len(bullets))) if bullets else []
            for b in selected:
                full_prompt += f"- {b}\n"
            full_prompt += "\n"

        # Save to tXXX.txt
        out_name = f"t{counter:03d}.txt"
        (DIR_OUT / out_name).write_text(full_prompt, encoding="utf-8")

        index_entries.append(f"{out_name} {base}")
        counter += 1

    Path("file_index.txt").write_text("\n".join(index_entries), encoding="utf-8")
    print(f"Done. Created {counter-1} prompts.")


if __name__ == "__main__":
    main()
