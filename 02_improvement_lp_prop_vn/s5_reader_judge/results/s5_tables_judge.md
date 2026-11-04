# Tầng 3 — Reader: Qwen/Qwen2.5-7B-Instruct-AWQ | Judge: Qwen/Qwen2.5-14B-Instruct-AWQ (v4)

- Kiểm tra judge (ĐẠT): ca dương — 4234 câu trả lời chứa ≥80% cụm từ của điều kiện, judge chấm 'có' = **99.6%** (cần ≥ 85%); ca âm — 506 câu trả lời gần như không có điều kiện, judge chấm 'có' = **11.9%** (cần ≤ 15%); câu trả lời 'không đủ thông tin' bị chấm đúng = 27.4% (nên ≈ 0%).

## Toàn bộ 1200 câu cond (%)

| Hệ | Budget | Accuracy | Cond. kept | Cond-Acc | Over-general | Abstain | CondCov (từ) | CondCov (cụm) | n | judge lỗi |
|---|---|---|---|---|---|---|---|---|---|---|
| passage | B100 | 54.8 | 53.4 | 46.0 | 9.1 | 29.2 | 62.7 | 33.6 | 1200 | 0 |
| std | B100 | 73.5 | 72.1 | 63.6 | 8.7 | 15.6 | 74.5 | 47.9 | 1200 | 0 |
| lp_noptr | B100 | 72.8 | 68.6 | 60.4 | 11.1 | 16.1 | 72.2 | 44.3 | 1200 | 0 |
| lp_out | B100 | 74.9 | 71.1 | 62.7 | 8.4 | 15.8 | 75.6 | 47.5 | 1200 | 0 |
| lp | B100 | 70.9 | 66.7 | 58.7 | 9.5 | 17.8 | 70.9 | 44.3 | 1200 | 0 |
| passage | B500 | 79.1 | 77.6 | 69.2 | 8.8 | 6.3 | 80.7 | 54.9 | 1200 | 0 |
| std | B500 | 78.8 | 77.1 | 67.1 | 8.8 | 5.8 | 80.1 | 53.7 | 1200 | 0 |
| lp_noptr | B500 | 78.3 | 74.2 | 65.1 | 10.7 | 6.6 | 78.2 | 51.7 | 1200 | 0 |
| lp_out | B500 | 80.7 | 78.9 | 70.2 | 8.8 | 7.0 | 80.6 | 54.7 | 1200 | 0 |
| lp | B500 | 80.9 | 79.1 | 69.9 | 9.5 | 6.7 | 81.2 | 54.4 | 1200 | 0 |
| oracle | Bfull | 90.1 | 87.4 | 81.8 | 7.3 | 3.4 | 88.1 | 67.8 | 1200 | 0 |

## 1200 câu mà điều kiện xuất hiện trong đáp án chuẩn (%)

| Hệ | Budget | Accuracy | Cond. kept | Cond-Acc | Over-general | Abstain | CondCov (từ) | CondCov (cụm) | n | judge lỗi |
|---|---|---|---|---|---|---|---|---|---|---|
| passage | B100 | 54.8 | 53.4 | 46.0 | 9.1 | 29.2 | 62.7 | 33.6 | 1200 | 0 |
| std | B100 | 73.5 | 72.1 | 63.6 | 8.7 | 15.6 | 74.5 | 47.9 | 1200 | 0 |
| lp_noptr | B100 | 72.8 | 68.6 | 60.4 | 11.1 | 16.1 | 72.2 | 44.3 | 1200 | 0 |
| lp_out | B100 | 74.9 | 71.1 | 62.7 | 8.4 | 15.8 | 75.6 | 47.5 | 1200 | 0 |
| lp | B100 | 70.9 | 66.7 | 58.7 | 9.5 | 17.8 | 70.9 | 44.3 | 1200 | 0 |
| passage | B500 | 79.1 | 77.6 | 69.2 | 8.8 | 6.3 | 80.7 | 54.9 | 1200 | 0 |
| std | B500 | 78.8 | 77.1 | 67.1 | 8.8 | 5.8 | 80.1 | 53.7 | 1200 | 0 |
| lp_noptr | B500 | 78.3 | 74.2 | 65.1 | 10.7 | 6.6 | 78.2 | 51.7 | 1200 | 0 |
| lp_out | B500 | 80.7 | 78.9 | 70.2 | 8.8 | 7.0 | 80.6 | 54.7 | 1200 | 0 |
| lp | B500 | 80.9 | 79.1 | 69.9 | 9.5 | 6.7 | 81.2 | 54.4 | 1200 | 0 |
| oracle | Bfull | 90.1 | 87.4 | 81.8 | 7.3 | 3.4 | 88.1 | 67.8 | 1200 | 0 |


## Paired Bootstrap (1000 lần)

| So sánh | Chênh lệch (điểm %) | CI 95% | n | Có ý nghĩa |
|---|---|---|---|---|
| cond_acc@B100: lp - passage | +12.67 | [+9.00, +16.08] | 1200 | ✓ |
| cond_acc@B500: lp - passage | +0.75 | [-2.58, +3.92] | 1200 |  |
| cond_acc@B100: lp - std | -4.92 | [-8.08, -2.08] | 1200 | ✓ |
| cond_acc@B500: lp - std | +2.83 | [-0.08, +5.58] | 1200 |  |
| cond_acc@B100: lp - lp_noptr | -1.75 | [-4.42, +1.00] | 1200 |  |
| cond_acc@B500: lp - lp_noptr | +4.83 | [+2.08, +7.33] | 1200 | ✓ |
| cond_acc@B100: lp - lp_out | -4.00 | [-6.25, -1.67] | 1200 | ✓ |
| cond_acc@B500: lp - lp_out | -0.33 | [-2.75, +2.08] | 1200 |  |
| correct@B100: lp - passage | +16.08 | [+12.50, +19.50] | 1200 | ✓ |
| correct@B500: lp - passage | +1.83 | [-0.83, +4.67] | 1200 |  |
| correct@B100: lp - std | -2.58 | [-5.42, +0.33] | 1200 |  |
| correct@B500: lp - std | +2.08 | [-0.67, +4.67] | 1200 |  |
| correct@B100: lp - lp_noptr | -1.83 | [-4.25, +0.58] | 1200 |  |
| correct@B500: lp - lp_noptr | +2.58 | [+0.00, +4.92] | 1200 |  |
| correct@B100: lp - lp_out | -4.00 | [-6.17, -1.58] | 1200 | ✓ |
| correct@B500: lp - lp_out | +0.25 | [-2.08, +2.42] | 1200 |  |
| overgeneralized@B100: lp - passage | +0.42 | [-1.83, +2.75] | 1200 |  |
| overgeneralized@B500: lp - passage | +0.67 | [-1.42, +2.83] | 1200 |  |
| overgeneralized@B100: lp - std | +0.83 | [-1.17, +2.67] | 1200 |  |
| overgeneralized@B500: lp - std | +0.75 | [-1.00, +2.58] | 1200 |  |
| overgeneralized@B100: lp - lp_noptr | -1.58 | [-3.67, +0.33] | 1200 |  |
| overgeneralized@B500: lp - lp_noptr | -1.17 | [-3.08, +0.67] | 1200 |  |
| overgeneralized@B100: lp - lp_out | +1.08 | [-0.42, +2.50] | 1200 |  |
| overgeneralized@B500: lp - lp_out | +0.75 | [-1.08, +2.42] | 1200 |  |
| cond_cov_lex@B100: lp - passage | +8.25 | [+5.25, +11.25] | 1200 | ✓ |
| cond_cov_lex@B500: lp - passage | +0.58 | [-1.92, +3.25] | 1200 |  |
| cond_cov_lex@B100: lp - std | -3.58 | [-6.17, -0.92] | 1200 | ✓ |
| cond_cov_lex@B500: lp - std | +1.17 | [-1.08, +3.42] | 1200 |  |
| cond_cov_lex@B100: lp - lp_noptr | -1.25 | [-3.50, +1.08] | 1200 |  |
| cond_cov_lex@B500: lp - lp_noptr | +3.08 | [+1.17, +5.00] | 1200 | ✓ |
| cond_cov_lex@B100: lp - lp_out | -4.67 | [-6.50, -2.83] | 1200 | ✓ |
| cond_cov_lex@B500: lp - lp_out | +0.67 | [-1.08, +2.33] | 1200 |  |
| cond_phrase@B100: lp - passage | +10.75 | [+7.33, +13.92] | 1200 | ✓ |
| cond_phrase@B500: lp - passage | -0.50 | [-3.67, +2.83] | 1200 |  |
| cond_phrase@B100: lp - std | -3.58 | [-6.58, -0.83] | 1200 | ✓ |
| cond_phrase@B500: lp - std | +0.75 | [-2.17, +3.58] | 1200 |  |
| cond_phrase@B100: lp - lp_noptr | +0.00 | [-2.58, +2.58] | 1200 |  |
| cond_phrase@B500: lp - lp_noptr | +2.75 | [+0.33, +5.42] | 1200 | ✓ |
| cond_phrase@B100: lp - lp_out | -3.17 | [-5.50, -1.08] | 1200 | ✓ |
| cond_phrase@B500: lp - lp_out | -0.25 | [-2.42, +2.08] | 1200 |  |
