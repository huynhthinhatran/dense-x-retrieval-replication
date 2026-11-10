# Analysis: checks requested in the review of the first version

Owner: Huynh Thi Nha Tran

These scripts recompute results from the saved outputs of S2, S3 and S5. They need no GPU and run in a few minutes on a CPU. They import `fill_budget`, `ccr_item`, `tier1`, `bootstrap_diff` and the judge parsers from the step folders, so the numbers use exactly the same code as the paper.

| Script | Question | Paper | Result |
|---|---|---|---|
| `scripts/ablation_attached_pointers.py` | Do the 3,063 attached pointers come from the gold spans? Rebuilds the `lp` / `lp_out` contexts without them. | §4.2, Table 4 | `results/ablation_attached_pointers.md` |
| `scripts/tier3_rescore.py` | Tier 3 with abstentions counted as incorrect, and on the 1,100 questions not used to refine the judge prompt. | Tables 5–6, §5.4, App. B | `results/tier3_rescore.md` |
| `scripts/tier1_dev.py` | Tier 1 on the held-out dev split, with τ = 0.5 / 0.6 / 0.7. | Table 3, §5.2 | `results/tier1_dev.md` |

## Main findings

* **Attached pointers.** They are not derived from the gold spans: 355 of them are on the dev split, 1,942 lie in articles without any gold span, and 3,013 are With-Condition (gold: 2,468 / 435 / 148 / 12). 2,243 have no cue; the rest use connective cues such as *trường hợp* and *nếu*. Without them, `lp` reaches 88.7% CCR@B500 (89.2% with them) and still beats `lp_noptr` by +5.1 points [+3.5, +6.6]. The rebuilt contexts reproduce the saved `lp` and `lp_out` contexts for 1,200 / 1,200 questions.
* **Proposition repair** depends on cues: 179 of the 316 repaired propositions contain a gold condition, so the Tier 1 gain from repair is partly by construction (stated in the paper's limitations).
* **Abstention = incorrect.** The judge marked 429 of 1,563 abstentions (27.4%) as correct. Counting them as incorrect lowers Accuracy by 2–5 points; the order of the systems in Cond-Acc does not change at either budget. `lp` − `lp_noptr` at B500: +3.9 [+1.2, +6.5].
* **1,100 held-out questions.** All conclusions hold (`lp` − `lp_noptr` at B500: +4.6 [+1.6, +7.5]) except that `lp` − `std` at B100 is no longer significant (−2.2 [−5.4, +0.7]).
* **Dev split.** Repair lowers Condition Drop from 7.4% to 3.6% (LP-Prop) and from 4.2% to 1.2% (standard propositions), as on eval, and does so at all three values of τ.

## Run

Inputs are the Kaggle outputs listed in `notebooks/README.md`: `data_v2/` (S1 + S2), `work_s3v2/` (S3), `work_s5/` (S5) and the 1,200-question file from S1b.

```bash
cd 02_improvement_lp_prop_vn/analysis
python scripts/ablation_attached_pointers.py --data data_v2 --s3 work_s3v2 \
    --cond cond_questions_v2_eval_1200.jsonl --out results
python scripts/tier3_rescore.py --work work_s5 --cond cond_questions_v2_eval_1200.jsonl --out results
python scripts/tier1_dev.py --data data_v2 --out results
```

`--scripts` (default `../..`) points to the folder that contains `s3_retrieval/`, `s5_reader_judge/` and `s6_evaluation/`.
