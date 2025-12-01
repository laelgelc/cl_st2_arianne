#!/usr/bin/env python3
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

# Libraries required:
# pip install python-docx pdfminer.six

from docx import Document
from pdfminer.high_level import extract_text


def convert_docx(input_file: Path, output_file: Path):
    try:
        doc = Document(input_file)
        text = "\n".join([para.text for para in doc.paragraphs])
        output_file.write_text(text, encoding="utf-8")
    except Exception as e:
        print(f"ERROR converting DOCX {input_file}: {e}")


def convert_pdf(input_file: Path, output_file: Path):
    try:
        text = extract_text(str(input_file))
        output_file.write_text(text, encoding="utf-8")
    except Exception as e:
        print(f"ERROR converting PDF {input_file}: {e}")


def process_file(input_file: Path, output_dir: Path):
    out_file = output_dir / (input_file.stem + ".txt")

    if input_file.suffix.lower() == ".docx":
        convert_docx(input_file, out_file)

    elif input_file.suffix.lower() == ".pdf":
        convert_pdf(input_file, out_file)

    else:
        return f"Skipping unsupported type: {input_file}"

    return f"Converted: {input_file.name}"


def main():
    parser = argparse.ArgumentParser(description="Convert DOCX and PDF to TXT")
    parser.add_argument("--input", required=True, help="Source folder")
    parser.add_argument("--output", required=True, help="Output folder")
    parser.add_argument("--workers", type=int, default=2, help="Number of worker threads")

    args = parser.parse_args()

    input_dir = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()

    if not input_dir.exists():
        print("Input folder does not exist.")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    files = [f for f in input_dir.rglob("*") if f.suffix.lower() in [".pdf", ".docx"]]

    print(f"Found {len(files)} files to process.")

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(process_file, f, output_dir) for f in files]

        for future in as_completed(futures):
            print(future.result())


if __name__ == "__main__":
    main()
