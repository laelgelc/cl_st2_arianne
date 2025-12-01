#!/usr/bin/env python3

import shutil
from pathlib import Path

SOURCE = Path("corpus/00_source")
TXT = Path("corpus/00_txt")
REMOVED = Path("corpus/temp/removed")

def main():
    REMOVED.mkdir(parents=True, exist_ok=True)

    # Stems (filenames without extension) in source folder
    source_stems = {f.stem for f in SOURCE.glob("*.*")}

    # Iterate over all files in 00_txt
    for f in TXT.glob("*.*"):
        if f.stem not in source_stems:
            print(f"[REMOVE] {f.name}")
            shutil.move(str(f), REMOVED / f.name)
        else:
            print(f"[KEEP]   {f.name}")

    print("\nDone.")

if __name__ == "__main__":
    main()
