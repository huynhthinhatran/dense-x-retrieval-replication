# Tier 3 re-scored

Questions: 1200 (held-out: 1100, calibration: 100). Abstentions: 1563, judged correct: 429.

`_f`: abstention forced to incorrect.

## all (1200 questions, %)

| Budget | System | Acc | Acc_f | Kept | Cond-Acc | Cond-Acc_f | Over-gen | Abstain |
|---|---|---|---|---|---|---|---|---|
| B100 | passage | 54.8 | 52.1 | 53.4 | 46.0 | 43.9 | 9.1 | 29.2 |
| B100 | std | 73.5 | 68.6 | 72.1 | 63.6 | 59.5 | 8.7 | 15.6 |
| B100 | lp_noptr | 72.8 | 67.8 | 68.6 | 60.4 | 56.6 | 11.1 | 16.1 |
| B100 | lp_out | 74.9 | 70.1 | 71.1 | 62.7 | 59.1 | 8.4 | 15.8 |
| B100 | lp | 70.9 | 66.5 | 66.7 | 58.7 | 55.8 | 9.5 | 17.8 |
| B500 | passage | 79.1 | 77.1 | 77.6 | 69.2 | 67.4 | 8.8 | 6.3 |
| B500 | std | 78.8 | 76.4 | 77.1 | 67.1 | 65.2 | 8.8 | 5.8 |
| B500 | lp_noptr | 78.3 | 76.0 | 74.2 | 65.1 | 63.6 | 10.7 | 6.6 |
| B500 | lp_out | 80.7 | 78.2 | 78.9 | 70.2 | 68.2 | 8.8 | 7.0 |
| B500 | lp | 80.9 | 77.8 | 79.1 | 69.9 | 67.5 | 9.5 | 6.7 |
| Bfull | oracle | 90.1 | 88.5 | 87.4 | 81.8 | 80.2 | 7.3 | 3.4 |

| Metric | Ranking (best first) |
|---|---|
| acc|B100 | lp_out > std > lp_noptr > lp > passage |
| acc|B500 | lp > lp_out > passage > std > lp_noptr |
| acc_f|B100 | lp_out > std > lp_noptr > lp > passage |
| acc_f|B500 | lp_out > lp > passage > std > lp_noptr |
| cacc|B100 | std > lp_out > lp_noptr > lp > passage |
| cacc|B500 | lp_out > lp > passage > std > lp_noptr |
| cacc_f|B100 | std > lp_out > lp_noptr > lp > passage |
| cacc_f|B500 | lp_out > lp > passage > std > lp_noptr |

| Comparison | Diff | 95% CI | Sig. |
|---|---|---|---|
| acc@B100: lp - passage | +16.1 | [+12.5, +19.5] | * |
| acc@B100: lp - std | -2.6 | [-5.4, +0.3] |  |
| acc@B100: lp - lp_noptr | -1.8 | [-4.2, +0.6] |  |
| acc@B100: lp - lp_out | -4.0 | [-6.2, -1.6] | * |
| acc@B500: lp - passage | +1.8 | [-0.8, +4.7] |  |
| acc@B500: lp - std | +2.1 | [-0.7, +4.7] |  |
| acc@B500: lp - lp_noptr | +2.6 | [+0.0, +4.9] |  |
| acc@B500: lp - lp_out | +0.2 | [-2.1, +2.4] |  |
| acc_f@B100: lp - passage | +14.4 | [+10.9, +17.8] | * |
| acc_f@B100: lp - std | -2.1 | [-5.1, +1.1] |  |
| acc_f@B100: lp - lp_noptr | -1.2 | [-3.8, +1.5] |  |
| acc_f@B100: lp - lp_out | -3.6 | [-5.8, -1.2] | * |
| acc_f@B500: lp - passage | +0.8 | [-2.1, +3.7] |  |
| acc_f@B500: lp - std | +1.4 | [-1.6, +4.2] |  |
| acc_f@B500: lp - lp_noptr | +1.8 | [-0.7, +4.3] |  |
| acc_f@B500: lp - lp_out | -0.4 | [-2.7, +1.9] |  |
| cacc@B100: lp - passage | +12.7 | [+9.0, +16.1] | * |
| cacc@B100: lp - std | -4.9 | [-8.1, -2.1] | * |
| cacc@B100: lp - lp_noptr | -1.8 | [-4.4, +1.0] |  |
| cacc@B100: lp - lp_out | -4.0 | [-6.2, -1.7] | * |
| cacc@B500: lp - passage | +0.8 | [-2.6, +3.9] |  |
| cacc@B500: lp - std | +2.8 | [-0.1, +5.6] |  |
| cacc@B500: lp - lp_noptr | +4.8 | [+2.1, +7.3] | * |
| cacc@B500: lp - lp_out | -0.3 | [-2.8, +2.1] |  |
| cacc_f@B100: lp - passage | +11.9 | [+8.3, +15.3] | * |
| cacc_f@B100: lp - std | -3.7 | [-6.9, -0.8] | * |
| cacc_f@B100: lp - lp_noptr | -0.8 | [-3.5, +2.0] |  |
| cacc_f@B100: lp - lp_out | -3.2 | [-5.5, -0.8] | * |
| cacc_f@B500: lp - passage | +0.1 | [-3.0, +3.0] |  |
| cacc_f@B500: lp - std | +2.3 | [-0.7, +5.2] |  |
| cacc_f@B500: lp - lp_noptr | +3.9 | [+1.2, +6.5] | * |
| cacc_f@B500: lp - lp_out | -0.8 | [-3.2, +1.8] |  |

## heldout (1100 questions, %)

| Budget | System | Acc | Acc_f | Kept | Cond-Acc | Cond-Acc_f | Over-gen | Abstain |
|---|---|---|---|---|---|---|---|---|
| B100 | passage | 54.8 | 52.1 | 53.5 | 45.9 | 43.9 | 9.0 | 28.5 |
| B100 | std | 73.1 | 68.0 | 71.1 | 62.8 | 58.5 | 9.0 | 15.5 |
| B100 | lp_noptr | 73.0 | 68.3 | 68.1 | 60.2 | 56.6 | 11.1 | 15.5 |
| B100 | lp_out | 75.5 | 70.9 | 70.9 | 63.0 | 59.5 | 8.5 | 15.1 |
| B100 | lp | 71.7 | 67.4 | 66.8 | 59.1 | 56.4 | 9.5 | 17.0 |
| B500 | passage | 79.2 | 77.2 | 77.5 | 69.3 | 67.5 | 8.9 | 6.4 |
| B500 | std | 78.9 | 76.4 | 76.7 | 66.9 | 64.9 | 8.7 | 5.7 |
| B500 | lp_noptr | 78.0 | 75.6 | 73.6 | 64.4 | 62.8 | 11.2 | 6.7 |
| B500 | lp_out | 80.5 | 78.3 | 78.5 | 69.7 | 68.0 | 9.2 | 6.7 |
| B500 | lp | 80.9 | 78.0 | 78.7 | 69.6 | 67.5 | 9.9 | 6.5 |
| Bfull | oracle | 90.2 | 88.5 | 87.3 | 81.8 | 80.2 | 7.4 | 3.5 |

| Metric | Ranking (best first) |
|---|---|
| acc|B100 | lp_out > std > lp_noptr > lp > passage |
| acc|B500 | lp > lp_out > passage > std > lp_noptr |
| acc_f|B100 | lp_out > lp_noptr > std > lp > passage |
| acc_f|B500 | lp_out > lp > passage > std > lp_noptr |
| cacc|B100 | lp_out > std > lp_noptr > lp > passage |
| cacc|B500 | lp_out > lp > passage > std > lp_noptr |
| cacc_f|B100 | lp_out > std > lp_noptr > lp > passage |
| cacc_f|B500 | lp_out > passage > lp > std > lp_noptr |

| Comparison | Diff | 95% CI | Sig. |
|---|---|---|---|
| acc@B100: lp - passage | +16.9 | [+13.4, +20.3] | * |
| acc@B100: lp - std | -1.4 | [-4.1, +1.6] |  |
| acc@B100: lp - lp_noptr | -1.3 | [-3.8, +1.4] |  |
| acc@B100: lp - lp_out | -3.8 | [-6.2, -1.3] | * |
| acc@B500: lp - passage | +1.7 | [-1.0, +4.8] |  |
| acc@B500: lp - std | +2.0 | [-0.7, +4.9] |  |
| acc@B500: lp - lp_noptr | +2.9 | [+0.3, +5.5] | * |
| acc@B500: lp - lp_out | +0.5 | [-1.8, +2.6] |  |
| acc_f@B100: lp - passage | +15.3 | [+11.6, +19.0] | * |
| acc_f@B100: lp - std | -0.6 | [-3.7, +2.5] |  |
| acc_f@B100: lp - lp_noptr | -0.9 | [-3.7, +1.8] |  |
| acc_f@B100: lp - lp_out | -3.5 | [-6.0, -1.0] | * |
| acc_f@B500: lp - passage | +0.8 | [-2.1, +3.7] |  |
| acc_f@B500: lp - std | +1.6 | [-1.2, +4.9] |  |
| acc_f@B500: lp - lp_noptr | +2.4 | [-0.3, +4.9] |  |
| acc_f@B500: lp - lp_out | -0.3 | [-2.6, +2.1] |  |
| cacc@B100: lp - passage | +13.2 | [+9.5, +16.6] | * |
| cacc@B100: lp - std | -3.7 | [-6.6, -0.6] | * |
| cacc@B100: lp - lp_noptr | -1.1 | [-3.8, +1.7] |  |
| cacc@B100: lp - lp_out | -3.9 | [-6.4, -1.5] | * |
| cacc@B500: lp - passage | +0.4 | [-3.2, +3.5] |  |
| cacc@B500: lp - std | +2.7 | [-0.2, +5.8] |  |
| cacc@B500: lp - lp_noptr | +5.3 | [+2.5, +8.2] | * |
| cacc@B500: lp - lp_out | -0.1 | [-2.7, +2.5] |  |
| cacc_f@B100: lp - passage | +12.5 | [+8.7, +16.0] | * |
| cacc_f@B100: lp - std | -2.2 | [-5.4, +0.7] |  |
| cacc_f@B100: lp - lp_noptr | -0.3 | [-3.2, +2.6] |  |
| cacc_f@B100: lp - lp_out | -3.2 | [-5.5, -0.7] | * |
| cacc_f@B500: lp - passage | -0.1 | [-3.5, +3.1] |  |
| cacc_f@B500: lp - std | +2.5 | [-0.5, +5.8] |  |
| cacc_f@B500: lp - lp_noptr | +4.6 | [+1.6, +7.5] | * |
| cacc_f@B500: lp - lp_out | -0.5 | [-3.1, +2.0] |  |

