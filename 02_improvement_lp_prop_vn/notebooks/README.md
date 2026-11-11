# Kaggle Notebooks & Datasets

Run on Kaggle (GPU T4 ×2, Internet on) with **Save Version → Save & Run All**.

## 🔗 Public Kaggle Links

### Datasets
* **Stage 1 & Corpus Data:** [`lp-prop-work-d1`](https://www.kaggle.com/datasets/thohintrnhngc/lp-prop-work-d1)
* **Stage 2 Propositionizer Data:** [`lp-prop-pipeline-s2`](https://www.kaggle.com/datasets/khhanhlinh/lp-prop-pipeline-s2)
* **Stage 3 Precomputed Embeddings:** [`lp-prop-pipeline-s3`](https://www.kaggle.com/datasets/<username>/lp-prop-pipeline-s3)

### Notebooks
| Notebook | Steps | Inputs | Link |
|---|---|---|---|
| `lp_prop_v2_nb1_questions.ipynb` | S1 + S1b | `lp-prop-work-d1`, `lp-prop-pipeline-s2` | [Kaggle Notebook](https://www.kaggle.com/code/thnhtranhuynh/lp-prop-q) |
| `lp_prop_v2_nb2_eval.ipynb` | S3 + S5 + S6 | output of NB1, `lp-prop-pipeline-s3` | [Kaggle Notebook](https://www.kaggle.com/code/nghgb0101/notebook54de2b7712) |
| `lp_prop_v2_nb3_feedback_fixes.ipynb` | Review Fixes & Ablation | `data_v2`, `work_s5` | [Chạy Local] |