#!/usr/bin/env python3
"""
extract_interview_info_grok.py

Reads all .txt files from corpus/01_selected (or another input directory you pass),
sends each file to Grok with a fixed prompt requesting:
  - interviewee background
  - ten Q&A about feelings, subjectivity, and daily life (no objective pandemic facts)

Writes results to the output directory you specify.

Parallel processing enabled via workers.

Usage:
    python extract_interview_info_grok.py \
        --input corpus/01_selected \
        --output extracted_interviews \
        --model grok-4 \
        --workers 4
"""

import argparse
import os
import sys
import json
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract interview information using Grok."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Folder with selected .txt files (e.g., corpus/01_selected)."
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Folder to save Grok outputs."
    )
    parser.add_argument(
        "--model", "-m",
        default="grok-4",
        help="Grok model to use."
    )
    parser.add_argument(
        "--max-output-tokens", "-t",
        type=int,
        default=5000,
        help="Maximum output tokens."
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers."
    )
    return parser.parse_args()


# ------------------------------------------------------------
# I/O Helpers
# ------------------------------------------------------------

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ------------------------------------------------------------
# Prompt
# ------------------------------------------------------------

FIXED_USER_PROMPT = """I want you to read the file below and extract:

-the background information on the interviewee.
-ten questions and their answers where they are talking about the feelings, daily life, and subjectivity of the interviewee in relation to the pandemic. Do NOT select questions or answers where they give objective facts on the pandemic or report on the current state of it. DON'T EVER MAKE UP ANSWERS. OUTPUT THE EXACT WORDING OF THE ANSWERS.

Respond like this:

Interviewee Background:
Question:
Answer:
Question:
Answer:
... (10 times)

--------- FILE BELOW ---------
"""


def build_system_prompt() -> str:
    return (
        "You are an expert assistant that reads interview transcripts "
        "and extracts background details and subjective Q&A content."
    )


def build_user_prompt(file_text: str) -> str:
    return FIXED_USER_PROMPT + file_text


# ------------------------------------------------------------
# Grok API
# ------------------------------------------------------------

def grok_api_call(model: str, system_prompt: str, user_prompt: str,
                  max_output_tokens: int) -> str:

    url = "https://api.x.ai/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['XAI_API_KEY']}",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": max_output_tokens,
        "temperature": 0.0
    }

    resp = requests.post(url, headers=headers, data=json.dumps(payload))

    if resp.status_code != 200:
        raise RuntimeError(f"Grok API error {resp.status_code}: {resp.text}")

    data = resp.json()
    return data["choices"][0]["message"]["content"]


# ------------------------------------------------------------
# Worker
# ------------------------------------------------------------

def process_file(
    file_path: Path,
    output_dir: Path,
    model: str,
    max_tokens: int,
):
    try:
        print(f"[WORKER] Processing: {file_path.name}")

        file_text = read_text(file_path)
        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(file_text)

        output = grok_api_call(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_output_tokens=max_tokens,
        )

        outname = f"{file_path.stem}_extracted.txt"
        outpath = output_dir / outname

        write_text(outpath, output)
        print(f"[WORKER] Saved → {outpath}")

        return True

    except Exception as e:
        print(f"[ERROR] {file_path.name}: {e}")
        return False


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():
    args = parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if "XAI_API_KEY" not in os.environ:
        print("ERROR: Please set environment variable XAI_API_KEY.")
        sys.exit(1)

    files = sorted(input_dir.glob("*.txt"))
    if not files:
        print("No .txt files found in input.")
        sys.exit(0)

    print(f"Processing {len(files)} files with {args.workers} workers...\n")

    futures = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for f in files:
            futures.append(
                pool.submit(
                    process_file,
                    f,
                    output_dir,
                    args.model,
                    args.max_output_tokens,
                )
            )

        for fut in as_completed(futures):
            fut.result()

    print("\nCompleted extracting interview information using Grok.")


if __name__ == "__main__":
    main()
