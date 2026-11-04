# S6: Tier 1, Tier 2 and bootstrap (paper §5.2–5.3)

Owner: Nguyen Huu Gia Bao

`scripts/s6_evaluate.py` reads the S2 propositions and the S3 ranks and contexts (no re-encoding).
* Coverage: a text covers a span if ≥ 60% of the span's word tokens (lower-cased, NFC, without 17 Vietnamese function words) appear in it.
* Tier 1 (3,063 gold spans): Condition Drop, Unconditional Rule, Pointer Retention (rule and condition in one proposition, or in two propositions linked by a pointer), propositions and pointers per article.
* Tier 2 (1,200 conditional + 19,404 generic questions): Recall@5 and MRR (duplicate-aware), HeadRecall, CCR and Orphan at B = 100 and 500.
* Paired bootstrap, 1,000 resamples, seed 0, 95% percentile CI.

Run inside `notebooks/lp_prop_v2_nb2_eval.ipynb`. Results: `results/s6_tables.md`, `results/s6_results.json`.
