python summarise_blog_posts.py \
    --input corpus/02_extracted \
    --output corpus/03_summary \
    --model grok-4 \
    --workers 6

python3 find_missing.py corpus/02_extracted corpus/03_summary
# output: corpus/temp/to_process

python summarise_blog_posts.py \
    --input corpus/temp/to_process \
    --output corpus/03_summary \
    --model grok-4 \
    --workers 8

python build_prompts.py

python generate_gpt.py \
    --input corpus/04_prompt \
    --output corpus/05_gpt \
    --model gpt-5.1 \
    --workers 4

python generate_grok.py \
    --input corpus/04_prompt \
    --output corpus/05_grok \
    --model grok-4 \
    --workers 4

python generate_gemini.py \
    --input corpus/04_prompt \
    --output corpus/05_gemini \
    --model gemini-2.5-pro \
    --workers 4

python clean_answers_human.py
# output: corpus/05_human

python tag.py
# output: corpus/07_tagged

python keylemmas.py \
    --input corpus/07_tagged \
    --output corpus/08_keylemmas \
    --cutoff 3

