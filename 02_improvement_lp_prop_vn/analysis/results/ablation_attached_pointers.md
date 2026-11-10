# Ablation: removing the attached pointers

Questions: 1200. Reproduced saved contexts: lp_B100 1200/1200, lp_B500 1200/1200, lp_out_B100 1200/1200, lp_out_B500 1200/1200

## Attached pointers

```
{
 "n_attached": 3063,
 "by_split": {
  "dev": 355,
  "eval": 2708
 },
 "in_articles_with_gold_span": 1121,
 "in_articles_without_gold_span": 1942,
 "types": {
  "VỚI_ĐIỀU_KIỆN": 3013,
  "TRỪ_TRƯỜNG_HỢP": 34,
  "KHÔNG_ÁP_DỤNG": 13,
  "NHƯNG_PHẢI": 3
 },
 "empty_cue": 2243,
 "top_cues": {
  "Trường hợp": 419,
  "trường hợp": 121,
  "Nếu": 69,
  "Trong trường hợp": 68,
  "nếu": 66,
  "trong trường hợp": 27,
  "Trừ trường hợp": 12,
  "không áp dụng đối với": 9
 }
}
```

## CCR / Orphan (%)

| System | CCR@B100 | Orphan@B100 | CCR@B500 | Orphan@B500 |
|---|---|---|---|---|
| lp_noptr | 69.1 | 15.7 | 83.6 | 10.7 |
| lp_out | 74.2 | 9.3 | 88.6 | 5.9 |
| lp | 69.3 | 9.5 | 89.2 | 5.2 |
| lp_out_noattach | 73.9 | 9.9 | 88.2 | 6.4 |
| lp_noattach | 69.3 | 10.5 | 88.7 | 5.7 |

## Paired bootstrap (1,000 resamples, points, 95% CI)

| Comparison | Diff | CI |
|---|---|---|
| ccr@B100: lp - lp_noattach | +0.00 | [-0.75, +0.83] |
| orphan@B100: lp - lp_noattach | -1.00 | [-1.75, -0.25] |
| ccr@B100: lp_out - lp_out_noattach | +0.33 | [-0.33, +1.00] |
| orphan@B100: lp_out - lp_out_noattach | -0.58 | [-1.17, -0.08] |
| ccr@B100: lp_noattach - lp_noptr | +0.25 | [-1.92, +2.58] |
| orphan@B100: lp_noattach - lp_noptr | -5.17 | [-7.00, -3.33] |
| ccr@B100: lp - lp_noptr | +0.25 | [-2.00, +2.67] |
| orphan@B100: lp - lp_noptr | -6.17 | [-8.00, -4.25] |
| ccr@B500: lp - lp_noattach | +0.58 | [+0.08, +1.08] |
| orphan@B500: lp - lp_noattach | -0.50 | [-1.00, +0.00] |
| ccr@B500: lp_out - lp_out_noattach | +0.42 | [-0.08, +1.00] |
| orphan@B500: lp_out - lp_out_noattach | -0.50 | [-1.08, +0.00] |
| ccr@B500: lp_noattach - lp_noptr | +5.08 | [+3.50, +6.58] |
| orphan@B500: lp_noattach - lp_noptr | -5.00 | [-6.33, -3.58] |
| ccr@B500: lp - lp_noptr | +5.67 | [+4.08, +7.25] |
| orphan@B500: lp - lp_noptr | -5.50 | [-6.92, -4.17] |
