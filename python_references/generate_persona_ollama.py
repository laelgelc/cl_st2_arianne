#!/usr/bin/env python3
"""
send_prompts_ollama.py

Reads persona prompt files (t001.txt, t002.txt, ...),
extracts SYSTEM PROMPT and USER PROMPT blocks,
sends them to a local Ollama model,
and saves output as t001_<tag>.txt (e.g., t001_ollama.txt).

Usage:
    python generate_persona_ollama.py \
        --input corpus/04_prompt_persona \
        --output corpus/05_persona_ollama \
        --model llama3:8b \
        --tag ollama \
        --workers 1
"""

import argparse
import os
import sys
import re
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(
        description="Send persona oral-history prompts to an Ollama model."
    )
    p.add_argument("--input", "-i", required=True,
                  help="Directory with tXXX prompt files.")
    p.add_argument("--output", "-o", required=True,
                  help="Output directory for completed interviews.")
    p.add_argument("--model", "-m", default="llama3:70b",
                  help="Ollama model to use (default: llama3:70b).")
    p.add_argument("--tag", "-g", default="ollama",
                  help="Tag appended to output filenames (default: ollama).")
    p.add_argument("--workers", type=int, default=1,
                  help="Parallel workers (local models → use 1).")
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
    """Extract SYSTEM PROMPT and USER PROMPT blocks from a tXXX.txt file."""

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
# Ollama API
# ------------------------------------------------------------
def call_ollama(model: str, system_prompt: str, user_prompt: str,
                max_output_tokens: int):

    # Format for Ollama
    full_prompt = f"""<|system|>
{system_prompt}

<|user|>
{user_prompt}

<|assistant|>

>>>>config
temperature: 0.7
num_predict: {max_output_tokens}
<<<<
"""

    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=full_prompt,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=dict(os.environ, OLLAMA_NO_TTY="1"),
        )
    except Exception as e:
        raise RuntimeError(f"Ollama call failed: {e}")

    if result.returncode != 0:
        raise RuntimeError(f"Ollama error output:\n{result.stderr}")

    output = result.stdout.strip()
    if not output:
        raise RuntimeError("Ollama returned empty output.")
    return output


# ------------------------------------------------------------
# Worker
# ------------------------------------------------------------
def process_prompt(
    path: Path,
    output_dir: Path,
    model: str,
    tag: str,
    max_tokens: int,
):
    try:
        print(f"[WORKER] Reading {path.name}")
        full_text = read_text(path)

        system_prompt, user_prompt = extract_system_and_user(full_text)

        print(f"[WORKER] Querying Ollama model {model} for {path.name} …")
        result = call_ollama(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_output_tokens=max_tokens,
        )

        stem = path.stem        # "t001"
        outname = f"{stem}_{tag}.txt"
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

    in_dir = Path(args.input)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(in_dir.glob("t*.txt"))
    if not files:
        print("No tXXX prompt files found.")
        sys.exit(0)

    print(f"\nUsing model: {args.model}")
    print(f"Output tag: {args.tag}")
    print(f"Processing {len(files)} prompts with {args.workers} workers…\n")

    futures = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for f in files:
            futures.append(
                pool.submit(
                    process_prompt,
                    f,
                    out_dir,
                    args.model,
                    args.tag,
                    args.max_output_tokens,
                )
            )

        for fut in as_completed(futures):
            fut.result()

    print("\nAll prompts processed with Ollama.")


if __name__ == "__main__":
    main()
