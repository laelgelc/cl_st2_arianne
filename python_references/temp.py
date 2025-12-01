import difflib

with open("corpus/02_extracted/t000493_extracted.txt") as f1, open("corpus/02_extracted/t000500_extracted.txt") as f2:
    t1 = f1.read()
    t2 = f2.read()

ratio = difflib.SequenceMatcher(None, t1, t2).ratio()
print("Similarity:", ratio)

with open("corpus/01_selected/t000018.txt") as f1, open("corpus/01_selected/t000019.txt") as f2:
    t1 = f1.read()
    t2 = f2.read()

ratio = difflib.SequenceMatcher(None, t1, t2).ratio()
print("Similarity:", ratio)
