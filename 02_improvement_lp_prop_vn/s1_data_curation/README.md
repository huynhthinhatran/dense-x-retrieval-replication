# S1: Data curation and span audit (paper §3.1–3.2, Appendix A)

Owner: Trinh Ngoc Thao Hien

## Scripts
* `scripts/s1_clean.py`: removes draft articles, heading fragments (body < 5 words) and verbatim duplicates (MD5 of whitespace-normalized text); filters passages, gold spans, generic QA and S2 propositions to the kept articles; writes `stats_v2.json`. Run inside `notebooks/lp_prop_v2_nb1_questions.ipynb`.
* `scripts/s1c_sample_span_review.py`: draws the 100-span audit sample (seed 2026; quota 55 / 25 / 15 / 5 by type, at most 4 spans per statute).

## Results
* `results/stats_v2.json`: 9,715 → 7,391 articles (2,316 drafts, 5 heading fragments, 3 duplicates removed), 107 statutes, 12,425 passages, 3,063 eval gold spans, 22,173 generic QA.
* `results/s1_clean.log`: run log on Kaggle.
* `results/span_review_v2/`: the audit sample (`sample_meta.json`) and labels.

## Split
Statute-level: eval 93 statutes / 6,468 articles; dev 14 statutes / 923 articles. No statute is in both splits.

## Span audit
100 spans from 51 statutes, oversampling the rarer types. One annotator labelled each span valid / minor / invalid: 95 valid, 5 minor, 0 invalid. With a single annotator no agreement score is reported.
