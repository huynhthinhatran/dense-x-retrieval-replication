# S1b: Conditional question generation (paper §3.3)

Owner: Huynh Thi Nha Tran

## Script
`scripts/s1b_gen_questions.py`, two stages:
* `gen`: for each candidate span (round-robin over shuffled articles, up to 2,400), Qwen2.5-14B-Instruct-AWQ (vLLM, tensor parallel 2, temperature 0, max 512 tokens) writes a JSON object with `question`, `answer` and `answer_if_condition_ignored`. One worked example is given in the prompt.
* `select`: keeps items that pass 7 checks (`json_ok`, `q_form`, `cond_in_answer`, `rule_in_answer`, `no_copy`, `ignored_differs`, `short_answer`) and selects 1,200 from the first round.

Run inside `notebooks/lp_prop_v2_nb1_questions.ipynb`.

## Results
* `results/gen_stats.json`: 1,909 of 2,400 items (79.5%) pass all checks; failures per check: 4 / 37 / 207 / 21 / 144 / 133 / 3.
* `results/sample_questions.md`: 20 random questions used for the case studies and the limitations.
* Final set: 1,200 questions on 1,200 articles (937 With-Condition, 210 Except, 49 But-Must, 4 Not-Applicable).
