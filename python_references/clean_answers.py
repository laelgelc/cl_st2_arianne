#!/usr/bin/env python3
import re
from pathlib import Path


# --------------------------------------------------------
# Extract all answers from a single file
# --------------------------------------------------------
def extract_answers(text: str) -> str:
    """
    Extracts Answer: blocks.
    Handles:
        Answer: <content>
        Answer:\n<content>
        Multi-line content until next 'Question:' or EOF.
    """

    lines = text.splitlines()
    out = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # detect Answer:
        if line.startswith("Answer:"):
            # CASE 1: answer is on the same line
            parts = line.split("Answer:", 1)
            after = parts[1].strip()

            if after:
                collected = [after]
                i += 1
            else:
                # CASE 2: answer starts on next line(s)
                collected = []
                i += 1

            # collect content until next Question: or EOF
            while i < len(lines) and not lines[i].strip().startswith("Question:"):
                collected.append(lines[i].rstrip())
                i += 1

            answer_text = "\n".join(collected).strip()
            if answer_text:
                out.append(answer_text)

            continue

        i += 1

    return "\n\n".join(out)


# --------------------------------------------------------
# Process a single folder like corpus/05_plain_gpt
# --------------------------------------------------------
def process_folder(folder: Path):
    name = folder.name  # e.g., 05_plain_gpt
    parts = name.split("_")

    # Expecting format: 05_<prompttype>_<model>
    if len(parts) < 3:
        print(f"[SKIP] Folder name not in expected format: {name}")
        return

    prompt_type = parts[1]  # plain | persona
    model = parts[2]        # gpt | gemini | grok

    out_dir = Path(f"corpus/06_clean_{prompt_type}_{model}")
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(folder.glob("t*.txt"))
    if not files:
        print(f"[SKIP] No t*.txt files in {folder}")
        return

    print(f"\nProcessing folder: {folder}")
    print(f"  → Prompt type: {prompt_type}")
    print(f"  → Model: {model}")
    print(f"  → Output dir: {out_dir}")

    for f in files:
        try:
            raw = f.read_text(encoding="utf-8", errors="ignore")
            cleaned = extract_answers(raw)

            out_name = f"{f.stem}_{prompt_type}_{model}.txt"
            out_path = out_dir / out_name
            out_path.write_text(cleaned, encoding="utf-8")

            print(f"[OK] {f.name} → {out_name}")
        except Exception as e:
            print(f"[ERROR] {f.name}: {e}")


# --------------------------------------------------------
# Main: automatically crawl corpus/05_*
# --------------------------------------------------------
def main():
    base_dir = Path("corpus")
    folders = sorted(base_dir.glob("05_*"))

    if not folders:
        print("No folders found matching corpus/05_*")
        return

    for folder in folders:
        if folder.is_dir():
            process_folder(folder)

    print("\nAll folders processed.")


if __name__ == "__main__":
    main()
