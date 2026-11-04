# Kết quả LP-Prop — BGE-M3 (split = eval)

- Câu có điều kiện: **1200** (0 câu thuộc Điều có bản trùng nội dung; chấm dedup-aware)
- Câu generic: **19404** (đã bỏ 0 câu thuộc Điều chỉ có tiêu đề / không có passage)
- Nhóm Điều trùng nội dung trong corpus: 0

## Tầng 1 — Propositionizer

| Hệ | Spans | Condition Drop (%) | Unconditional Rule (%) | Pointer Retention (%) | Props/Điều | Từ/prop | Pointers/Điều |
|---|---|---|---|---|---|---|---|
| std_raw | 3063 | 5.9 | 3.2 | 86.3 | 7.73 | 30.73 | 0.00 |
| std | 3063 | 2.2 | 2.2 | 91.0 | 7.76 | 30.79 | 0.00 |
| lp_raw | 3063 | 7.7 | 5.3 | 85.9 | 7.68 | 29.01 | 3.86 |
| lp_edge_only | 3063 | 7.7 | 5.3 | 86.5 | 7.68 | 29.01 | 2.62 |
| lp | 3063 | 3.3 | 3.3 | 91.7 | 7.72 | 29.15 | 2.62 |

## Tầng 2 — Truy xuất BGE-M3 (%)

| Hệ | Recall@5_cond | Recall@5_cond_strict | Recall@5_generic | MRR@5_generic | HeadRecall@B100 | CCR@B100 | Orphan@B100 | HeadRecall@B500 | CCR@B500 | Orphan@B500 |
|---|---|---|---|---|---|---|---|---|---|---|
| passage | 89.7 | 89.7 | 88.8 | 74.4 | 59.2 | 51.4 | 7.8 | 84.8 | 83.3 | 1.4 |
| std_raw | 95.2 | 95.2 | 87.6 | 71.5 | 82.7 | 70.1 | 12.6 | 93.2 | 83.8 | 9.4 |
| std | 96.1 | 96.1 | 87.7 | 71.6 | 83.8 | 72.5 | 11.2 | 94.8 | 86.9 | 7.8 |
| lp_noptr | 95.3 | 95.3 | 86.5 | 70.0 | 84.8 | 69.1 | 15.7 | 94.2 | 83.6 | 10.7 |
| lp_out | 95.3 | 95.3 | 86.5 | 70.0 | 83.6 | 74.2 | 9.3 | 94.5 | 88.6 | 5.9 |
| lp_raw | 94.3 | 94.3 | 86.4 | 69.9 | 76.1 | 65.2 | 10.8 | 92.2 | 85.4 | 6.8 |
| lp_edge_only | 94.3 | 94.3 | 86.4 | 69.9 | 77.0 | 66.2 | 10.8 | 92.9 | 86.3 | 6.6 |
| lp | 95.3 | 95.3 | 86.5 | 70.0 | 78.8 | 69.3 | 9.5 | 94.4 | 89.2 | 5.2 |

## Paired Bootstrap (1000 lần)

| So sánh | Chênh lệch (điểm %) | CI 95% | n | Có ý nghĩa |
|---|---|---|---|---|
| Recall@5_cond: lp - passage | +5.67 | [+3.83, +7.67] | 1200 | ✓ |
| Recall@5_cond: lp - std | -0.75 | [-1.75, +0.17] | 1200 |  |
| Recall@5_cond: lp - lp_noptr | +0.00 | [+0.00, +0.00] | 1200 |  |
| Recall@5_cond: lp - lp_out | +0.00 | [+0.00, +0.00] | 1200 |  |
| Recall@5_cond: lp - lp_raw | +1.00 | [+0.42, +1.58] | 1200 | ✓ |
| Recall@5_cond: lp - lp_edge_only | +1.00 | [+0.42, +1.58] | 1200 | ✓ |
| CCR@B100: lp - passage | +17.92 | [+14.33, +21.08] | 1200 | ✓ |
| CCR@B100: lp - std | -3.17 | [-5.92, -0.58] | 1200 | ✓ |
| CCR@B100: lp - lp_noptr | +0.25 | [-2.00, +2.67] | 1200 |  |
| CCR@B100: lp - lp_out | -4.92 | [-6.42, -3.42] | 1200 | ✓ |
| CCR@B100: lp - lp_raw | +4.08 | [+2.42, +5.67] | 1200 | ✓ |
| CCR@B100: lp - lp_edge_only | +3.08 | [+2.17, +4.08] | 1200 | ✓ |
| Orphan@B100: lp - passage | +1.75 | [-0.33, +4.00] | 1200 |  |
| Orphan@B100: lp - std | -1.75 | [-3.83, +0.42] | 1200 |  |
| Orphan@B100: lp - lp_noptr | -6.17 | [-8.00, -4.25] | 1200 | ✓ |
| Orphan@B100: lp - lp_out | +0.17 | [-1.00, +1.50] | 1200 |  |
| Orphan@B100: lp - lp_raw | -1.33 | [-2.58, -0.08] | 1200 | ✓ |
| Orphan@B100: lp - lp_edge_only | -1.25 | [-1.83, -0.67] | 1200 | ✓ |
| CCR@B500: lp - passage | +5.92 | [+3.25, +8.50] | 1200 | ✓ |
| CCR@B500: lp - std | +2.33 | [+0.25, +4.42] | 1200 | ✓ |
| CCR@B500: lp - lp_noptr | +5.67 | [+4.08, +7.25] | 1200 | ✓ |
| CCR@B500: lp - lp_out | +0.67 | [-0.17, +1.50] | 1200 |  |
| CCR@B500: lp - lp_raw | +3.83 | [+2.58, +5.08] | 1200 | ✓ |
| CCR@B500: lp - lp_edge_only | +2.92 | [+2.00, +3.83] | 1200 | ✓ |
| Orphan@B500: lp - passage | +3.75 | [+2.42, +5.25] | 1200 | ✓ |
| Orphan@B500: lp - std | -2.67 | [-4.33, -0.83] | 1200 | ✓ |
| Orphan@B500: lp - lp_noptr | -5.50 | [-6.92, -4.17] | 1200 | ✓ |
| Orphan@B500: lp - lp_out | -0.75 | [-1.50, -0.08] | 1200 | ✓ |
| Orphan@B500: lp - lp_raw | -1.58 | [-2.50, -0.67] | 1200 | ✓ |
| Orphan@B500: lp - lp_edge_only | -1.42 | [-2.17, -0.75] | 1200 | ✓ |
