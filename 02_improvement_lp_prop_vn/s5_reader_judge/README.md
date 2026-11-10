# S5: Reader, LLM judge and Tier 3 (paper §5.4, §6)

Owner: Huynh Thi Nha Tran

`scripts/s5_reader_judge.py`, three stages:
* `reader`: Qwen2.5-7B-Instruct-AWQ (temperature 0, max 384 tokens) answers each question from the context of 5 systems × 2 budgets, plus an oracle with the full article (≤ 1,500 words): 13,200 answers.
* `judge`: Qwen2.5-14B-Instruct-AWQ (tensor parallel 2, max 256 tokens) in two calls: `correct` + `rule_stated`, then a quote-first few-shot call for `condition_kept`.
* `aggregate`: Accuracy, Cond. kept, Cond-Acc, Over-general, Abstain; phrase-match variant (≥ 50% of condition 4-grams, no abstention); judge sanity check; paired bootstrap (1,000 resamples, seed 0).

Run inside `notebooks/lp_prop_v2_nb2_eval.ipynb`.

## Results
* `results/s5_tables_judge.md`, `s5_results_judge.json`: main Tier 3 table (condition label from the judge).
* `results/s5_tables_phrase.md`, `s5_results_phrase.json`: same with the phrase-match condition label.
* `results/s5_tables_calib.md`: judge check on the first 100 questions, run before the full judge.
* Judge sanity (full run): positive cases 99.6% kept (4,234 answers), negative cases 11.9% (506); 27.4% of the 1,563 abstentions initially judged correct.
* Strict Abstention Enforcement: In the final paper revision (§5.4), answers matching the abstention pattern (`ABSTAIN_PAT`) are strictly overridden to incorrect (`correct = 0, cond_acc = 0`). All system rankings and paired bootstrap significance conclusions hold with 100% consistency across both the 1,200 full evaluation questions and the 1,100 non-calibration subset; verified in `notebooks/lp_prop_v2_nb3_feedback_fixes.ipynb`.
