#!/usr/bin/env python3
"""
send_prompts_grok.py

Reads persona-prompt files (tXXX.txt) from an input directory,
extracts SYSTEM and USER prompts from the file text,
submits them to the XAI Grok API,
and saves the model output to corpus/05_persona_grok with the SAME filename.

Parallel workers included.

Usage:
python generate_persona_grok.py \
    --input corpus/04_prompt_persona \
    --output corpus/05_persona_grok \
    --model grok-4 \
    --workers 4
"""

import argparse
import os
import sys
import json
import requests
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send oral-history persona prompts to XAI Grok."
    )
    parser.add_argument("--input", "-i", required=True,
                        help="Directory containing tXXX prompt files (e.g., corpus/04_prompt).")
    parser.add_argument("--output", "-o", required=True,
                        help="Output directory (e.g., corpus/05_persona_grok).")
    parser.add_argument("--model", "-m", default="grok-4",
                        help="Grok model to use (default: grok-4).")
    parser.add_argument("--max-output-tokens", "-t", type=int, default=6000,
                        help="Maximum number of output tokens.")
    parser.add_argument("--workers", type=int, default=4,
                        help="Parallel workers.")
    return parser.parse_args()


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def extract_system_and_user(full_text: str):
    """
    Extract system prompt and user prompt from a tXXX.txt file.

    Expected format:

    SYSTEM PROMPT:
    <system>

    USER PROMPT:
    <user ... to end of file>
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
# Grok API call
# ------------------------------------------------------------
def grok_api_call(model: str, system_prompt: str, user_prompt: str,
                  max_output_tokens: int) -> str:

    url = "https://api.x.ai/v1/chat/completions"

    if "XAI_API_KEY" not in os.environ:
        raise RuntimeError("ERROR: Set environment variable XAI_API_KEY.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['XAI_API_KEY']}",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        "max_tokens": max_output_tokens,
        "temperature": 0.7,
    }

    resp = requests.post(url, headers=headers, data=json.dumps(payload))

    if resp.status_code != 200:
        raise RuntimeError(f"Grok API error {resp.status_code}: {resp.text}")

    data = resp.json()

    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        raise RuntimeError("Malformed Grok response:\n" +
                           json.dumps(data, indent=2))


# ------------------------------------------------------------
# Worker
# ------------------------------------------------------------
def process_prompt(path: Path, output_dir: Path, model: str,
                   max_tokens: int):
    try:
        print(f"[WORKER] Reading {path.name}")
        full_text = read_text(path)

        system_prompt, user_prompt = extract_system_and_user(full_text)

        print(f"[WORKER] Calling Grok for {path.name} ...")
        result = grok_api_call(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_output_tokens=max_tokens,
        )

        # -------------------------
        # NEW: save as t001_grok.txt
        # -------------------------
        stem = path.stem
        outname = f"{stem}_grok.txt"
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
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(input_dir.glob("t*.txt"))
    if not files:
        print("No tXXX prompt files found.")
        sys.exit(0)

    print(f"Processing {len(files)} prompts with {args.workers} workers...\n")

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

        for future in as_completed(futures):
            future.result()

    print("\nAll prompts processed successfully with Grok.")


if __name__ == "__main__":
    main()
