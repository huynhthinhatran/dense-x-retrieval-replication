# Kaggle notebooks

Run on Kaggle (GPU T4 ×2, Internet on) with **Save Version → Save & Run All**.

| Notebook | Steps | Inputs | Time |
|---|---|---|---|
| S2 notebook (in `s2_propositionizer/`) | S2 | `lp-prop-work-d1` | see S2 README |
| `lp_prop_v2_nb1_questions.ipynb` | S1 + S1b | Kaggle datasets `lp-prop-work-d1`, `lp-prop-pipeline-s2` | ~1–1.5 h |
| `lp_prop_v2_nb2_eval.ipynb` | S3 + S5 + S6 | output of notebook 1, `lp-prop-pipeline-s3` (optional, old embeddings) | ~6–7.5 h |

Each notebook writes the step scripts with `%%writefile`; they are identical to the copies in the step folders. Notebook 2 zips its outputs into `lp_prop_v2_results.zip` (tables in this repository; raw reader/judge outputs are kept outside git).
