import os
import re
import time
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

# Load environment variables from the project's env folder
load_dotenv("env/.env")

# =============================================================================
# CONFIGURATION
# =============================================================================
# Using the paths relative to your project root as shown in Project View
INPUT_DIR = Path("corpus/01_ipcc_scraped")
OUTPUT_DIR = Path("corpus/02_ipcc_cleaned")
LOG_FILE = Path("ipcc_text_denoising.log")

MODEL = "gpt-5.1"
CHUNK_SIZE = 1800  # Number of words per LLM request
OVERLAP = 150      # Context overlap between chunks to maintain continuity

# =============================================================================
# LOGGING SETUP
# =============================================================================
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# =============================================================================
# DENOISING PROMPT
# =============================================================================
SYSTEM_PROMPT = (
    "You are a text restoration specialist. The provided text is a raw OCR extraction from a "
    "1990s PDF. It contains artifacts: broken words (suc-cessful), character misrecognition "
    "(incoфorate), and 'braided' text where two-column layout lines are interleaved.\n\n"
    "RESTORE the text to its original intended flow without altering the content:\n"
    "1. Rejoin split words and fix OCR character swaps (e.g., Cyrillic 'ф' to 'p').\n"
    "2. Restore paragraph flow and un-braid columns into logical sequences.\n"
    "3. Remove page numbers or header fragments if they interrupt sentences.\n\n"
    "STRICT CONSTRAINT: Do not summarize. Do not change the author's wording or grammar. "
    "Output ONLY the cleaned text with no introductory or concluding remarks."
)

def call_api(client: OpenAI, user_prompt: str) -> str:
    """Standard API call structure using Chat Completions."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,  # Ensure high fidelity/low creativity
    )
    return response.choices[0].message.content

def process_file(file_path: Path, client: OpenAI):
    """Processes a single file using a rolling window to handle context limits."""
    start_time = time.time()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            words = f.read().split()

        cleaned_parts = []
        i = 0
        while i < len(words):
            # Extract chunk
            chunk_words = words[i : i + CHUNK_SIZE]
            user_prompt = " ".join(chunk_words)

            # Process chunk
            cleaned_text = call_api(client, user_prompt)

            # If not the first chunk, trim the overlap to avoid duplicated text
            if i > 0:
                words_in_cleaned = cleaned_text.split()
                # Skip the first portion that overlaps with the previous chunk
                cleaned_text = " ".join(words_in_cleaned[OVERLAP // 2:])

            cleaned_parts.append(cleaned_text)

            # Increment window by (size - overlap)
            i += (CHUNK_SIZE - OVERLAP)

        # Assemble and write output
        output_path = OUTPUT_DIR / file_path.name
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path.write_text(" ".join(cleaned_parts), encoding='utf-8')

        duration_min = (time.time() - start_time) / 60
        logging.info(f"FILE: {file_path.name} | DURATION: {duration_min:.2f} min | STATUS: Success")

    except Exception as e:
        duration_min = (time.time() - start_time) / 60
        logging.error(f"FILE: {file_path.name} | DURATION: {duration_min:.2f} min | STATUS: Error | MSG: {e}")

def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logging.critical("OPENAI_API_KEY not found in environment.")
        print("Error: OPENAI_API_KEY not found.")
        return

    client = OpenAI(api_key=api_key)

    # Ensure directory exists and find files
    if not INPUT_DIR.exists():
        logging.critical(f"Input directory {INPUT_DIR} does not exist.")
        return

    files = sorted(INPUT_DIR.glob("*.txt"))

    # Detect if running in an interactive terminal or nohup
    is_interactive = sys.stdout.isatty()

    print(f"Processing {len(files)} files. Logging to {LOG_FILE}")
    if not is_interactive:
        print("Non-interactive terminal detected. Progress bar disabled for clean logs.")

    logging.info(f"--- Starting Batch Denoising: {len(files)} files ---")

    # The 'disable' parameter hides the bar if we are running in the background (nohup)
    for file_path in tqdm(files, desc="Denoising IPCC Corpus", disable=not is_interactive):
        process_file(file_path, client)

    logging.info("--- Batch Process Finished ---")
    print("Denoising complete. Check ipcc_text_denoising.log for details.")

if __name__ == "__main__":
    main()
