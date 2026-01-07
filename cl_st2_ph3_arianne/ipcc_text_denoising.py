import os
import re
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

# Load environment variables
load_dotenv("env/.env")

# Configuration
INPUT_DIR = Path("corpus/01_ipcc_scraped")
OUTPUT_DIR = Path("corpus/02_ipcc_cleaned")
MODEL = "gpt-5.1"
CHUNK_SIZE = 1800  # Number of words per chunk
OVERLAP = 150      # Number of words to overlap

# Denoising System Prompt
SYSTEM_PROMPT = (
    "You are a text restoration specialist. The provided text is a raw OCR extraction from a "
    "1990s PDF. It contains artifacts: broken words (suc-cessful), character misrecognition "
    "(incoфorate), and 'braided' text where two-column layout lines are interleaved.\n\n"
    "RESTORE the text to its original intended flow without altering the content:\n"
    "1. Rejoin split words and fix OCR character swaps.\n"
    "2. Restore paragraph flow and un-braid columns into logical sequences.\n"
    "3. Remove page numbers or header fragments if they interrupt sentences.\n\n"
    "STRICT CONSTRAINT: Do not summarize. Do not change the author's wording or grammar. "
    "Output ONLY the cleaned text with no introductory or concluding remarks."
)

def call_api(client: OpenAI, user_prompt: str) -> str:
    """Standard API call structure based on your project conventions."""
    response = client.chat.completions.create( # Using standard chat completions
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,  # Deterministic output for fidelity
    )
    return response.choices[0].message.content

def process_file(file_path: Path, client: OpenAI):
    """Processes a single file using a rolling window."""
    with open(file_path, 'r', encoding='utf-8') as f:
        words = f.read().split()

    cleaned_parts = []
    i = 0
    while i < len(words):
        # Calculate chunk boundaries
        chunk_words = words[i : i + CHUNK_SIZE]
        user_prompt = " ".join(chunk_words)

        # Call API
        try:
            cleaned_text = call_api(client, user_prompt)

            # If this isn't the first chunk, we trim the overlap to avoid duplication
            # In a more advanced version, you'd fuzzy-match the overlap
            if i > 0:
                # Basic overlap trimming: skip the roughly first N words
                words_in_cleaned = cleaned_text.split()
                # We skip the overlap portion that the previous chunk already handled
                cleaned_text = " ".join(words_in_cleaned[OVERLAP // 2:])

            cleaned_parts.append(cleaned_text)
        except Exception as e:
            print(f"Error processing {file_path.name} at word {i}: {e}")
            break

        i += (CHUNK_SIZE - OVERLAP)

    # Save cleaned file
    output_path = OUTPUT_DIR / file_path.name
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path.write_text(" ".join(cleaned_parts), encoding='utf-8')

def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment.")

    client = OpenAI(api_key=api_key)

    files = sorted(INPUT_DIR.glob("*.txt"))
    print(f"Found {len(files)} files to denoise.")

    for file_path in tqdm(files, desc="Denoising IPCC Corpus"):
        process_file(file_path, client)

if __name__ == "__main__":
    main()
