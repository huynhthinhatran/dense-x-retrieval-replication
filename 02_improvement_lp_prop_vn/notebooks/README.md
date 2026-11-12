# Kaggle Notebooks & Datasets

Run on Kaggle (2×T4 GPUs, Internet on) with **Save Version → Save & Run All**. Intermediate data files (`articles_v2.jsonl`, `props_*.jsonl`, `cond_questions_v2_eval_1200.jsonl`, `contexts_*.jsonl`, `reader.shard*.jsonl`, `judge_v4.shard*.jsonl`) are available in the **Input** and **Output** tabs of the public Kaggle links below.

## 🔗 Public Kaggle Links

### Datasets
* **Stage 1 & Corpus Data:** [`lp-prop-work-d1`](https://www.kaggle.com/datasets/thohintrnhngc/lp-prop-work-d1) — raw corpus, initial passages, gold condition spans, generic QA.
* **Stage 2 Propositionizer Data:** [`lp-prop-pipeline-s2`](https://www.kaggle.com/datasets/khhanhlinh/lp-prop-pipeline-s2) — S2 propositions and pointers (`props_lp_raw.jsonl`, `props_lp_edge_only.jsonl`, `props_lp.jsonl`, `props_std_raw.jsonl`, `props_std.jsonl`).

### Notebooks & Intermediate Outputs
| Notebook | Steps | Inputs | Outputs (in Kaggle Output tab) | Link |
|---|---|---|---|---|
| `lp_prop_v2_nb1_questions.ipynb` | S1 + S1b | `lp-prop-work-d1`, `lp-prop-pipeline-s2` | `data_v2/` (cleaned corpus, filtered propositions & spans), `questions_v2/cond_questions_v2_eval_1200.jsonl` | [Kaggle Notebook](https://www.kaggle.com/code/thnhtranhuynh/lp-prop-q) |
| `lp_prop_v2_nb2_eval.ipynb` | S3 + S5 + S6 | output of NB1, `lp-prop-pipeline-s3` (optional cached embeddings) | `work_s3v2/` (`ranks_*.jsonl`, `contexts_*.jsonl`), `work_s5/` (`reader.shard*.jsonl`, `judge_v4.shard*.jsonl`), `results/` | [Kaggle Notebook](https://www.kaggle.com/code/nghgb0101/notebook54de2b7712) |
| `lp_prop_v2_nb3_feedback_fixes.ipynb` | Review Checks & Ablations | `data_v2/`, `work_s5/` (from NB1 & NB2 outputs) | Pre-executed outputs for pointer audit, Tier 1 on dev, strict `abstain=0` re-scoring, and 8-system Tier 2 | In repository (CPU-only, runs on Kaggle or local PC) |