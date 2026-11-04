# LP-Prop: Logic-Preserving Proposition Retrieval for Condition-Sensitive Vietnamese Legal QA

Proposition-level retrieval (Dense X) can separate a statutory rule from the condition or exception that limits it. A reader that receives only the rule then gives a fluent but **over-general** answer. LP-Prop links propositions with typed rule→condition **pointers** and follows them when the context is filled under a word budget.

This folder holds the code, notebooks and results behind the paper. All numbers below are copied from the `results/` folders.

## Pipeline

Steps are numbered as in the code. There is no S4 in the final pipeline.

| Step | What it does | Code | Main output | Paper | Owner |
|---|---|---|---|---|---|
| S1 | Clean the corpus (drafts, heading fragments, duplicates), statute-level split, span audit | `s1_data_curation/` | `stats_v2.json`, span audit | §3.1–3.2, App. A | Hien |
| S1b | Generate 1,200 conditional questions with 7 automatic checks | `s1b_question_generation/` | `gen_stats.json` | §3.3 | Nha Tran |
| S2 | Propositions and condition pointers (Qwen2.5-7B-AWQ), pointer refinement, proposition repair | `s2_propositionizer/` | `props_*.jsonl` | §4.1–4.2, App. B | Bao |
| S3 | BGE-M3 + FAISS retrieval for 8 systems, `fill_budget` at B = 100 and 500 words | `s3_retrieval/` | `contexts_*.jsonl` | §4.3 | Bao |
| S5 | Reader (Qwen2.5-7B-AWQ), LLM judge (Qwen2.5-14B-AWQ), phrase-match check, bootstrap | `s5_reader_judge/` | `s5_tables_judge.md` | §5.4 (Tier 3), §6 | Nha Tran |
| S6 | Tier 1 (propositionizer), Tier 2 (Recall, CCR, Orphan), paired bootstrap | `s6_evaluation/` | `s6_tables.md` | §5.2–5.3 | Bao |

Systems: `passage`, `std_raw`, `std`, `lp_raw`, `lp_edge_only`, and three systems on the final LP-Prop propositions that differ only in expansion mode: `lp_noptr` (none), `lp_out` (rule→condition) and `lp` (both directions). An `oracle` reader receives the full article.

## Data: LegalCond-7.4K

* Source: [`thangvip/vietnamese-legal-qa`](https://huggingface.co/datasets/thangvip/vietnamese-legal-qa), 9,715 articles.
* Removed: 2,316 draft articles, 5 heading fragments, 3 duplicate pairs → **7,391 articles from 107 statutes**, 12,425 passages.
* Split by statute: eval 93 statutes / 6,468 articles; dev 14 statutes / 923 articles (held out, not used in any reported result).
* 3,063 gold rule–condition spans on eval; 1,200 conditional questions (937 With-Condition, 210 Except, 49 But-Must, 4 Not-Applicable) and 19,404 generic questions.

Large data files (`*.jsonl`, `*.npy`) are not stored in git. They are in the Kaggle datasets and notebook outputs listed in `notebooks/README.md`.

## Main results (1,200 conditional questions)

| | `passage` | `std` | `lp_noptr` | `lp_out` | `lp` |
|---|---|---|---|---|---|
| CCR@B500 (%) | 83.3 | 86.9 | 83.6 | 88.6 | **89.2** |
| Orphan@B500 (%) | **1.4** | 7.8 | 10.7 | 5.9 | 5.2 |
| Cond-Acc B100 (%) | 46.0 | **63.6** | 60.4 | 62.7 | 58.7 |
| Cond-Acc B500 (%) | 69.2 | 67.1 | 65.1 | **70.2** | 69.9 |

Oracle (full article): Cond-Acc 81.8%. Significance (paired bootstrap, 1,000 resamples): at B500, `lp` beats `lp_noptr` in Cond-Acc (+4.8 points, 95% CI [+2.1, +7.3]) and `std` in CCR (+2.3, [+0.3, +4.4]); it is not significantly better than `std`, `passage` or `lp_out` in Cond-Acc. At B100, `std` and `lp_out` are significantly better than `lp`. Full tables: `s5_reader_judge/results/` and `s6_evaluation/results/`.

## Reproduce

Run on Kaggle with 2×T4 GPUs and Internet on, using **Save Version → Save & Run All**:

1. S2 (propositionizer): see `s2_propositionizer/README.md`.
2. `notebooks/lp_prop_v2_nb1_questions.ipynb`: S1 + S1b (about 1–1.5 h).
3. `notebooks/lp_prop_v2_nb2_eval.ipynb`: S3 + S5 + S6 (about 6–7.5 h).

Each notebook writes the scripts it runs with `%%writefile`; the copies in the step folders are the same code.

Language: documentation is in English. Code comments, log messages and notebook notes are in Vietnamese and are kept exactly as they were run; prompts are in Vietnamese because the data is Vietnamese.

## Folder layout

```text
02_improvement_lp_prop_vn/
├── s1_data_curation/        {scripts, results}
├── s1b_question_generation/ {scripts, results}
├── s2_propositionizer/      {scripts, notebook, results}
├── s3_retrieval/            {scripts, results}
├── s5_reader_judge/         {scripts, results}
├── s6_evaluation/           {scripts, results}
├── notebooks/               Kaggle notebooks (S1+S1b, S3+S5+S6)
└── docs/                    planning documents (archive, in Vietnamese)
```
