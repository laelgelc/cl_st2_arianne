#!/usr/bin/env python3
"""
generate_interpretation_gpt.py

Reads files from interpretation/input, sends each full prompt to GPT,
and saves GPT's response to interpretation/output with the same filename.

Usage:
    python generate_interpretation_gpt.py \
        --input interpretation/input \
        --output interpretation/output \
        --model gpt-5.1 \
        --workers 4
"""

import argparse
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

# Load environment variables from env/.env
env_path = Path(__file__).resolve().parent / "env" / ".env"
load_dotenv(dotenv_path=env_path)

# ------------------------------------------------------------
# API
# ------------------------------------------------------------
try:
    from openai import OpenAI
except ImportError:
    print("Error: Install with: conda install openai")
    sys.exit(1)

# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send LMDA interpretation prompts to GPT."
    )

    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Directory containing prompt files."
    )

    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Directory for GPT responses."
    )

    parser.add_argument(
        "--model", "-m",
        default="gpt-5.1",
        help="Model to use."
    )

    parser.add_argument(
        "--max-output-tokens", "-t",
        type=int,
        default=9000,
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
# Helpers
# ------------------------------------------------------------
def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def call_api(
        client: OpenAI,
        model: str,
        full_prompt: str,
        max_output_tokens: int,
) -> str:
    """
    Send the entire interpretation prompt as a single user message.
    """
    response = client.responses.create(
        model=model,
        input=[
            {"role": "user", "content": full_prompt},
        ],
        max_output_tokens=max_output_tokens,
        temperature=0.0,
    )

    out = response.output_text

    if not out:
        raise RuntimeError("API returned empty output.")

    return out

# ------------------------------------------------------------
# Worker
# ------------------------------------------------------------
def process_prompt(
        path: Path,
        output_dir: Path,
        client: OpenAI,
        model: str,
        max_tokens: int,
) -> tuple[bool, str]:
    try:
        print(f"[WORKER] Reading {path.name}")
        full_prompt = read_text(path)

        if not full_prompt.strip():
            raise ValueError("Prompt file is empty.")

        print(f"[WORKER] Sending to GPT: {path.name}")

        result = call_api(
            client=client,
            model=model,
            full_prompt=full_prompt,
            max_output_tokens=max_tokens,
        )

        outpath = output_dir / path.name
        write_text(outpath, result)

        print(f"[WORKER] Saved → {outpath}")

        return True, path.name

    except Exception as e:
        print(f"[ERROR] {path.name}: {e}")
        return False, path.name

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main() -> None:
    args = parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        print(f"Error: input directory does not exist: {input_dir}")
        sys.exit(1)

    files = sorted(input_dir.glob("*.txt"))

    if not files:
        print(f"No prompt files found in {input_dir}.")
        sys.exit(0)

    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        print("Error: OPENAI_API_KEY not set.")
        print(f"Checked environment and {env_path}")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    print(f"Submitting {len(files)} prompts using {args.workers} workers…")

    failures = []

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [
            pool.submit(
                process_prompt,
                f,
                output_dir,
                client,
                args.model,
                args.max_output_tokens,
            )
            for f in files
        ]

        for fut in as_completed(futures):
            ok, name = fut.result()
            if not ok:
                failures.append(name)

    if failures:
        print("\n⚠ Some prompts failed:")
        for name in failures:
            print(f"  - {name}")
        sys.exit(1)

    print("\n✓ All prompts processed successfully.")

if __name__ == "__main__":
    main()