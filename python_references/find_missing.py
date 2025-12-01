#!/usr/bin/env python3
import argparse
from pathlib import Path
import shutil

def base(fname: str) -> str:
    """Return filename portion before first underscore."""
    return fname.split("_")[0]

def main():
    parser = argparse.ArgumentParser(
        description="Find files missing in folder B when compared to folder A, "
                    "using only the filename portion before the first underscore."
    )
    parser.add_argument("folderA", type=str, help="Folder to compare FROM")
    parser.add_argument("folderB", type=str, help="Folder to compare TO")
    args = parser.parse_args()

    folderA = Path(args.folderA)
    folderB = Path(args.folderB)
    outdir = Path("corpus/temp/to_process")
    outdir.mkdir(parents=True, exist_ok=True)

    # List files
    filesA = list(folderA.glob("*"))
    filesB = list(folderB.glob("*"))

    # Compute base names
    basesA = {base(f.name): f for f in filesA}
    basesB = {base(f.name): f for f in filesB}

    # Find missing
    missing = [basesA[b] for b in basesA.keys() if b not in basesB]

    if not missing:
        print("No missing files found.")
        return

    # Copy missing files
    for f in missing:
        dest = outdir / f.name
        shutil.copy2(f, dest)
        print(f"Copied: {f} -> {dest}")

    print(f"Done. {len(missing)} missing files copied.")

if __name__ == "__main__":
    main()

