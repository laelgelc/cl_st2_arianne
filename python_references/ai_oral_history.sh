python convert_to_txt.py --input corpus/00_source --output corpus/00_txt --workers 10

python select_transcripts.py --input corpus/00_txt  --output corpus/01_selected  --workers 12

python extract_interview_info_grok.py \
    --input corpus/01_selected \
    --output corpus/02_extracted \
    --model grok-4 \
    --workers 8

python summarize_answers.py \
    --input corpus/02_extracted \
    --output corpus/03_summary \
    --model grok-4 \
    --workers 6

python3 find_missing.py corpus/02_extracted corpus/03_summary 
# output: corpus/temp/to_process

python summarize_answers.py \
    --input corpus/temp/to_process \
    --output corpus/03_summary \
    --model grok-4 \
    --workers 8

python build_prompts_persona.py 
# output: corpus/04_prompt_persona

python generate_gpt.py \
    --input corpus/04_prompt_persona \
    --output corpus/05_persona_gpt \
    --model gpt-5.1 \
    --workers 4

python generate_grok.py \
    --input corpus/04_prompt_persona \
    --output corpus/05_persona_grok \
    --model grok-4 \
    --workers 4

python generate_gemini.py \
    --input corpus/04_prompt_persona \
    --output corpus/05_persona_gemini \
    --model gemini-2.5-pro\
    --workers 4

python build_prompts_plain.py 
# output: corpus/04_prompt_plain

python generate_gpt.py \
    --input corpus/04_prompt_plain \
    --output corpus/05_plain_gpt \
    --model gpt-5.1 \
    --workers 4

python generate_grok.py \
    --input corpus/04_prompt_plain \
    --output corpus/05_plain_grok \
    --model grok-4 \
    --workers 4

python generate_gemini.py \
    --input corpus/04_prompt_plain \
    --output corpus/05_plain_gemini \
    --model gemini-2.5-pro\
    --workers 4

python clean_answers.py
# output: corpus/06_clean*

python clean_answers_human.py
# output: corpus/06_clean_human

python tag.py
# output: corpus/07_tagged

python keylemmas.py \
    --input corpus/07_tagged \
    --output corpus/08_keylemmas \
    --cutoff 3

python select_kws_stratified.py \
    --ceiling 150 \
    --human-weight 2 \
    --max-total 1200
# output: corpus/09_kw_selected
# Total consolidated keywords: 1082 (max allowed: 1200)
"
human           → selected 300/300 keywords
persona_gemini  → selected 94/150 keywords
persona_gpt     → selected 150/150 keywords
persona_grok    → selected 88/150 keywords
plain_gemini    → selected 150/150 keywords
plain_gpt       → selected 150/150 keywords
plain_grok      → selected 150/150 keywords

Total consolidated keywords (incl. duplicates): 1082
Unique keywords (used downstream): 949
Duplicates removed later: 133

Final unique keywords written: 949
"

rm -rf columns columns_clean
python columns.py
# output: columns, columns_clean, file_ids.txt, index_keywords.txt

python merge_columns.py
# output: sas/data.txt

python sas_formats.py
# output: sas/word_labels_format.sas, etc

## RUN SAS
## Tony Person 1 account

python factor_lists.py
# output: factors

python corpus_size.py
# output: corpus_size/corpus_size.tsv 

cd latex_boxplots
# builds boxplots for factor analysis:
python latex_boxplots.py
# output: latex_boxplots

python latex_anova_table.py
# output: latex_tables

python examples.py
# output: examples (LaTEX format)

# sanity check on the scores:
python score_details.py
# output: examples/score_details.txt

# interpretation
# build prompts:
python interpretation_prompts.py 

# submit prompts:
python generate_interpretation_gpt.py \
    --input interpretation/input \
    --output interpretation/output \
    --model gpt-5.1 \
    --workers 4

