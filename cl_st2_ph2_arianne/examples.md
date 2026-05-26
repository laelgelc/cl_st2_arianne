## `examples.py` Reverse-engineered development specification

### Programme name

**Factor-score example extractor and LaTeX generator**

A possible descriptive name:

> **Generate factor-pole text examples from SAS factor scores**

---

## 1. Purpose

The programme generates representative text examples for each factor dimension and factor pole in a corpus-based study.

It uses:

- factor scores exported from SAS,
- group-level mean factor scores,
- manually/externally prepared factor-pole keyword or lemma lists,
- a mapping between statistical file IDs and real corpus filenames,
- tagged corpus files organised by source/model.

For each factor, the programme selects texts with the strongest positive and negative factor scores, annotates relevant lexical items, and writes the selected examples as LaTeX files.

It also builds a master LaTeX document that includes all generated examples.

---

## 2. Main objective

Given a set of factor-analysis outputs, the programme should:

1. Detect all available factor-score columns.
2. For each factor:
   - identify the positive pole;
   - identify the negative pole.
3. Rank groups according to their mean factor score.
4. Select high-scoring or low-scoring texts from the relevant groups.
5. Locate the corresponding tagged corpus files.
6. Highlight factor-relevant lemmas in the text.
7. Export each example as an individual LaTeX `textsample` environment.
8. Generate a master `examples.tex` file including all examples.
9. Report missing corpus files, if any.

---

## 3. Expected inputs

### 3.1 Factor scores file

Path:

```text
sas/output_cl_st2_ph2_arianne/cl_st2_ph2_arianne_scores_only.tsv
```

Format:

- TSV file.
- Must contain at least the following columns:

```text
filename
group
source
model
fac1
fac2
...
```

The number of factor columns is not hard-coded. The programme detects columns matching:

```text
fac<number>
```

Examples:

```text
fac1
fac2
fac3
fac4
```

---

### 3.2 Group means files

For each factor `n`, the programme expects a file:

```text
sas/output_cl_st2_ph2_arianne/means_group_f<n>.tsv
```

Examples:

```text
sas/output_cl_st2_ph2_arianne/means_group_f1.tsv
sas/output_cl_st2_ph2_arianne/means_group_f2.tsv
sas/output_cl_st2_ph2_arianne/means_group_f3.tsv
sas/output_cl_st2_ph2_arianne/means_group_f4.tsv
```

Each file must contain:

```text
group
Mean fac<n>
```

For example, `means_group_f1.tsv` must contain:

```text
group
Mean fac1
```

These files are used to decide which group is most representative of the positive or negative pole of each factor.

---

### 3.3 Factor-pole lemma files

For each factor and pole, the programme expects:

```text
factors/f<n>_pos.txt
factors/f<n>_neg.txt
```

Examples:

```text
factors/f1_pos.txt
factors/f1_neg.txt
factors/f2_pos.txt
factors/f2_neg.txt
```

Expected format:

- First line is treated as a header and skipped.
- Remaining lines contain comma-separated lexical entries.
- Each lexical entry is expected to include a lemma followed by parenthesised information.

Example conceptual format:

```text
lemma (...)
another_lemma (...)
```

The programme extracts the lemma before the opening parenthesis.

---

### 3.4 File ID mapping

Path:

```text
file_ids.txt
```

Purpose:

Maps statistical file IDs to actual tagged corpus filenames.

Expected format:

```text
t000001 t001_gemini.txt
t000002 t002_gemini.txt
t000003 t003_gemini.txt
```

The first field corresponds to the `filename` value in the SAS scores file.

The second field corresponds to the actual filename in the tagged corpus folders.

---

### 3.5 Tagged corpus files

The programme expects tagged corpus files under:

```text
corpus/07_tagged/
```

With subfolders:

```text
corpus/07_tagged/gemini
corpus/07_tagged/gpt
corpus/07_tagged/grok
corpus/07_tagged/human
```

Each tagged file is expected to contain one token per line, with at least three whitespace-separated columns:

```text
wordform tag lemma
```

Example:

```text
The DT the
story NN story
continues VBZ continue
```

Only the first and third columns are essential for the current programme:

- `wordform` is used in the reconstructed text.
- `lemma` is checked against the factor-pole lemma list.

---

### 3.6 LaTeX header

The programme expects a LaTeX preamble/header file:

```text
examples/top_header
```

This file is copied into the beginning of the master LaTeX output.

---

## 4. Expected outputs

### 4.1 Individual LaTeX examples

The programme writes individual `.tex` files into:

```text
examples/f<n>_pos/
examples/f<n>_neg/
```

Examples:

```text
examples/f1_pos/f1_pos_001.tex
examples/f1_pos/f1_pos_002.tex
examples/f1_neg/f1_neg_001.tex
examples/f2_pos/f2_pos_001.tex
```

Each file contains one LaTeX `textsample` environment.

Conceptual output:

```latex
\begin{textsample}{POS Dim 1 – group_name – Score 2.35 – filename.txt}  \label{ex:f1_pos_001}
Text with \textbf{highlighted} factor-relevant words.

% matched lemmas: lemma1, lemma2, lemma3
\end{textsample}
```

---

### 4.2 Master LaTeX file

The programme creates:

```text
examples/examples.tex
```

This file:

1. Includes the contents of `examples/top_header`.
2. Starts the LaTeX document.
3. Adds title and table of contents.
4. Creates one section per factor pole.
5. Includes all generated individual example files.

---

### 4.3 Missing-file report

If some expected tagged corpus files cannot be found, the programme writes:

```text
missing_files.txt
```

Each line records diagnostic information, including:

- statistical filename ID,
- mapped corpus filename,
- group,
- source,
- model,
- attempted path.

If no files are missing and an old `missing_files.txt` exists, it is removed.

---

## 5. Selection logic

### 5.1 Factor detection

The programme detects all factor columns in the scores file using the naming pattern:

```text
fac<number>
```

The detected columns are sorted numerically.

Example:

```text
fac1, fac2, fac3, fac4
```

The total number of detected factor columns determines how many factors are processed.

---

### 5.2 Pole logic

For each factor, two poles are processed:

| Pole | Sorting direction | Interpretation |
|---|---:|---|
| Positive | Descending | Highest factor scores first |
| Negative | Ascending | Lowest factor scores first |

For factor 1, for example:

- positive pole uses `fac1` sorted descending;
- negative pole uses `fac1` sorted ascending.

---

### 5.3 Group ranking

For each factor, the programme reads the corresponding group means file.

Groups are ranked by their mean score for that factor.

For the positive pole:

- the group with the highest mean is treated as the top group.

For the negative pole:

- the group with the lowest mean is treated as the top group.

---

### 5.4 Example quotas

For each factor pole:

1. Select up to **20 examples** from the top-ranked group.
2. Select up to **10 examples** from each remaining group.

Texts with a factor score of exactly `0` are skipped.

---

## 6. Corpus-file location logic

The programme does not use the statistical `group` value directly as the tagged corpus folder.

Instead:

| Source/model information | Corpus folder |
|---|---|
| `source == "human"` | `corpus/07_tagged/human` |
| AI-generated text | `corpus/07_tagged/<model>` |

For example:

| source | model | folder |
|---|---|---|
| human | blank or other | `human` |
| ai | gemini | `gemini` |
| ai | gpt | `gpt` |
| ai | grok | `grok` |

The actual filename is obtained through `file_ids.txt`.

---

## 7. Text reconstruction and annotation

### 7.1 Reading tagged text

Each tagged file is read line by line.

For each valid token line, the programme extracts:

```text
wordform
lemma
```

The output text is reconstructed by joining wordforms with spaces.

---

### 7.2 Lemma highlighting

If a token’s lemma appears in the current factor-pole lemma list, the wordform is wrapped in LaTeX bold formatting:

```latex
\textbf{wordform}
```

Some lemmas are explicitly excluded from highlighting through a stoplist.

The stoplist contains items such as:

```text
edith
doorbell
michael
recorded
attempt
request
```

---

### 7.3 Text cleanup

The reconstructed text is cleaned before output:

- problematic LaTeX braces and backslashes are removed;
- spacing before punctuation is fixed;
- contractions such as `do n't` are normalised to `don't`;
- selected LaTeX special characters are escaped;
- text is split into paragraph-like sentence groups.

---

## 8. LaTeX formatting requirements

Each generated example must include:

1. A title containing:
   - pole,
   - factor number,
   - group,
   - factor score,
   - source filename.
2. A LaTeX label.
3. The reconstructed and annotated text.
4. A comment listing matched lemmas.

Example title format:

```text
POS Dim 1 – group_name – Score 2.35 – filename.txt
```

Example label format:

```text
ex:f1_pos_001
```

---

## 9. Error handling requirements

The programme should raise clear errors if:

1. The factor scores file lacks required columns.
2. No factor-score columns are found.
3. A group means file is missing.
4. A group means file lacks the expected `group` column.
5. A group means file lacks the expected `Mean fac<n>` column.
6. A factor-pole lemma file is missing.
7. The LaTeX header file `examples/top_header` is missing.

The programme should not crash immediately for missing tagged corpus files. Instead, it should record them in `missing_files.txt`.

---

## 10. Directory behaviour

The programme should create the main examples directory if it does not exist:

```text
examples/
```

For each factor pole, it should create:

```text
examples/f<n>_pos/
examples/f<n>_neg/
```

Before writing new examples for a given factor pole, it should remove old generated example files matching that pole’s naming pattern.

This prevents stale files from previous runs being included accidentally.

---

## 11. Functional requirements

### FR1 — Load ID mapping

The programme shall read `file_ids.txt` and create a mapping from statistical file IDs to actual corpus filenames.

---

### FR2 — Load factor scores

The programme shall read the SAS factor-score TSV file into memory.

---

### FR3 — Validate factor-score metadata

The programme shall confirm that the scores file contains:

```text
filename
group
source
model
```

---

### FR4 — Detect factor columns

The programme shall detect all columns named according to the pattern:

```text
fac<number>
```

---

### FR5 — Process all detected factors

The programme shall process every detected factor, without requiring the factor count to be hard-coded.

---

### FR6 — Load group means

For each factor, the programme shall load the corresponding group means file.

---

### FR7 — Rank groups by pole

For each factor pole, the programme shall rank groups according to the factor mean:

- descending for positive poles;
- ascending for negative poles.

---

### FR8 — Load pole lemmas

For each factor pole, the programme shall load the corresponding lemma list from the `factors` directory.

---

### FR9 — Select examples

For each factor pole, the programme shall select:

- up to 20 non-zero-score examples from the top group;
- up to 10 non-zero-score examples from every other group.

---

### FR10 — Locate tagged files

The programme shall locate the tagged text file using:

1. the statistical file ID;
2. the file-ID mapping;
3. the `source` value;
4. the `model` value.

---

### FR11 — Annotate text

The programme shall reconstruct the text from tagged-token lines and bold wordforms whose lemmas match the factor-pole lemma list.

---

### FR12 — Escape LaTeX-sensitive content

The programme shall escape problematic characters in filenames, group labels, and text content before writing LaTeX.

---

### FR13 — Write individual examples

The programme shall write each selected example as an individual `.tex` file.

---

### FR14 — Report missing files

The programme shall record missing or unlocatable tagged files in `missing_files.txt`.

---

### FR15 — Build master LaTeX file

The programme shall generate a master `examples/examples.tex` file that includes all individual example files.

---

## 12. Non-functional requirements

### NFR1 — Reproducibility

The programme should produce deterministic output given the same input files.

---

### NFR2 — Transparency

The programme should print progress messages showing:

- number of detected factors;
- current factor pole being processed;
- number of examples written;
- missing-file status;
- master-file creation status.

---

### NFR3 — Portability

The programme should use relative paths from the project directory so that it can be run from the project root.

---

### NFR4 — Maintainability

Path constants, helper functions, and processing logic should be clearly separated.

---

### NFR5 — Data validation

The programme should fail early when core statistical inputs are malformed or missing.

---

### NFR6 — Corpus robustness

Missing individual corpus files should be reported rather than causing the whole programme to fail.

---

## 13. Implied research workflow

The programme appears to belong to a larger workflow:

1. Collect or generate texts from multiple sources/models.
2. Clean and tag the corpus.
3. Count linguistic features.
4. Run factor analysis and statistical modelling in SAS.
5. Export factor scores, means, ANOVA tables, and related results.
6. Identify salient lexical items for factor poles.
7. Generate representative text examples.
8. Compile selected examples into LaTeX for reporting or publication.

---

## 14. Suggested concise specification title

A suitable development-specification title would be:

> **Specification for Generating LaTeX Text Examples from Factor-Analysis Scores**

Alternative shorter title:

> **Factor-Pole Example Extraction Specification**