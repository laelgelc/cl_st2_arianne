#!/usr/bin/env python3
"""
generate_gemini.py

Reads prompt files (tXXX.txt) from an input directory,
extracts SYSTEM and USER prompts, sends them to Google Gemini,
and saves the model output to corpus/05_gemini with the SAME filename.

Supports parallel workers.

Usage:
    python generate_gemini.py \
        --input corpus/04_prompt \
        --output corpus/05_gemini \
        --model gemini-2.5-pro \
        --workers 4
"""

import argparse
import os
import sys
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Load environment variables from env/.env
env_path = Path(__file__).resolve().parent / "env" / ".env"
load_dotenv(dotenv_path=env_path)


# ---------------------------------------------
# API
# ---------------------------------------------
try:
    import google.generativeai as genai
except ImportError:
    print("Error: Install with: conda install openai")
    sys.exit(1)


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(
        description="Send persona oral-history prompts to Gemini."
    )
    p.add_argument("--input", "-i", required=True,
                  help="Directory with tXXX prompt files.")
    p.add_argument("--output", "-o", required=True,
                  help="Output directory (e.g., corpus/05_persona_gemini).")
    p.add_argument("--model", "-m", default="gemini-1.5-pro",
                  help="Gemini model to use.")
    p.add_argument("--workers", type=int, default=4,
                  help="Parallel workers.")
    p.add_argument("--max-output-tokens", type=int, default=6000)
    return p.parse_args()


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def extract_system_and_user(full_text: str):
    """
    Extract system prompt and user prompt from a tXXX.txt file.

    Expected format:

    SYSTEM PROMPT:
    <system>

    USER PROMPT:
    <user>
    """

    sys_match = re.search(
        r"SYSTEM PROMPT:\s*(.+?)\nUSER PROMPT:",
        full_text,
        re.DOTALL
    )
    if not sys_match:
        raise ValueError("SYSTEM PROMPT block not found.")
    system_prompt = sys_match.group(1).strip()

    user_match = re.search(
        r"USER PROMPT:\s*(.+)",
        full_text,
        re.DOTALL
    )
    if not user_match:
        raise ValueError("USER PROMPT block not found.")
    user_prompt = user_match.group(1).strip()

    return system_prompt, user_prompt


# ------------------------------------------------------------
# Gemini API
# ------------------------------------------------------------
def gemini_call(model: str, system_prompt: str, user_prompt: str,
                max_output_tokens: int):

    if "GEMINI_API_KEY" not in os.environ:
        raise RuntimeError("ERROR: Set GEMINI_API_KEY in environment.")

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    # System prompt must be merged into the generation config
    # because Gemini uses a single "prompt" rather than GPT-style roles.
    full_input = f"SYSTEM:\n{system_prompt}\n\nUSER:\n{user_prompt}"

    model_obj = genai.GenerativeModel(model)

    response = model_obj.generate_content(
        full_input,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=max_output_tokens,
            temperature=0.7,
        )
    )

    return response.text


# ------------------------------------------------------------
# Worker
# ------------------------------------------------------------
def process_prompt(path: Path, output_dir: Path, model: str,
                   max_tokens: int):
    try:
        print(f"[WORKER] Reading {path.name}")
        full_text = read_text(path)

        system_prompt, user_prompt = extract_system_and_user(full_text)

        print(f"[WORKER] Calling Gemini for {path.name} ...")
        result = gemini_call(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_output_tokens=max_tokens,
        )

        # --- changed part: add _gemini suffix ---
        stem = path.stem          # "t001"
        outname = f"{stem}_gemini.txt"
        outpath = output_dir / outname

        write_text(outpath, result)
        print(f"[WORKER] Saved → {outpath}")
        return True

    except Exception as e:
        print(f"[ERROR] {path.name}: {e}")
        return False

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    args = parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True, parents=True)

    files = sorted(input_dir.glob("t*.txt"))
    if not files:
        print("No tXXX prompt files found.")
        sys.exit(0)

    print(f"Processing {len(files)} prompts with {args.workers} workers…\n")

    futures = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for f in files:
            futures.append(
                pool.submit(
                    process_prompt,
                    f,
                    output_dir,
                    args.model,
                    args.max_output_tokens,
                )
            )

        for fut in as_completed(futures):
            fut.result()

    print("\nAll prompts processed successfully with Gemini.")


if __name__ == "__main__":
    main()

