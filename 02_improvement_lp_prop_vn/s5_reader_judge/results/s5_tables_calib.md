# Tầng 3 — Reader: Qwen/Qwen2.5-7B-Instruct-AWQ | Judge: Qwen/Qwen2.5-14B-Instruct-AWQ (v4)

- Kiểm tra judge (ĐẠT): ca dương — 367 câu trả lời chứa ≥80% cụm từ của điều kiện, judge chấm 'có' = **99.7%** (cần ≥ 85%); ca âm — 39 câu trả lời gần như không có điều kiện, judge chấm 'có' = **12.8%** (cần ≤ 15%); câu trả lời 'không đủ thông tin' bị chấm đúng = 25.3% (nên ≈ 0%).

## Toàn bộ 100 câu cond (%)

| Hệ | Budget | Accuracy | Cond. kept | Cond-Acc | Over-general | Abstain | CondCov (từ) | CondCov (cụm) | n | judge lỗi |
|---|---|---|---|---|---|---|---|---|---|---|
| passage | B100 | 55.0 | 53.0 | 47.0 | 10.0 | 36.0 | 64.0 | 32.0 | 100 | 0 |
| std | B100 | 78.0 | 83.0 | 72.0 | 5.0 | 17.0 | 81.0 | 54.0 | 100 | 0 |
| lp_noptr | B100 | 70.0 | 74.0 | 63.0 | 11.0 | 23.0 | 79.0 | 50.0 | 100 | 0 |
| lp_out | B100 | 68.0 | 73.0 | 59.0 | 8.0 | 23.0 | 80.0 | 49.0 | 100 | 0 |
| lp | B100 | 62.0 | 65.0 | 54.0 | 10.0 | 27.0 | 69.0 | 40.0 | 100 | 0 |
| passage | B500 | 78.0 | 79.0 | 68.0 | 8.0 | 6.0 | 86.0 | 57.0 | 100 | 0 |
| std | B500 | 78.0 | 81.0 | 69.0 | 9.0 | 7.0 | 84.0 | 63.0 | 100 | 0 |
| lp_noptr | B500 | 82.0 | 81.0 | 73.0 | 5.0 | 5.0 | 83.0 | 64.0 | 100 | 0 |
| lp_out | B500 | 83.0 | 83.0 | 76.0 | 4.0 | 10.0 | 84.0 | 63.0 | 100 | 0 |
| lp | B500 | 81.0 | 83.0 | 73.0 | 5.0 | 9.0 | 85.0 | 60.0 | 100 | 0 |
| oracle | Bfull | 89.0 | 89.0 | 82.0 | 7.0 | 3.0 | 86.0 | 61.0 | 100 | 0 |

## 100 câu mà điều kiện xuất hiện trong đáp án chuẩn (%)

| Hệ | Budget | Accuracy | Cond. kept | Cond-Acc | Over-general | Abstain | CondCov (từ) | CondCov (cụm) | n | judge lỗi |
|---|---|---|---|---|---|---|---|---|---|---|
| passage | B100 | 55.0 | 53.0 | 47.0 | 10.0 | 36.0 | 64.0 | 32.0 | 100 | 0 |
| std | B100 | 78.0 | 83.0 | 72.0 | 5.0 | 17.0 | 81.0 | 54.0 | 100 | 0 |
| lp_noptr | B100 | 70.0 | 74.0 | 63.0 | 11.0 | 23.0 | 79.0 | 50.0 | 100 | 0 |
| lp_out | B100 | 68.0 | 73.0 | 59.0 | 8.0 | 23.0 | 80.0 | 49.0 | 100 | 0 |
| lp | B100 | 62.0 | 65.0 | 54.0 | 10.0 | 27.0 | 69.0 | 40.0 | 100 | 0 |
| passage | B500 | 78.0 | 79.0 | 68.0 | 8.0 | 6.0 | 86.0 | 57.0 | 100 | 0 |
| std | B500 | 78.0 | 81.0 | 69.0 | 9.0 | 7.0 | 84.0 | 63.0 | 100 | 0 |
| lp_noptr | B500 | 82.0 | 81.0 | 73.0 | 5.0 | 5.0 | 83.0 | 64.0 | 100 | 0 |
| lp_out | B500 | 83.0 | 83.0 | 76.0 | 4.0 | 10.0 | 84.0 | 63.0 | 100 | 0 |
| lp | B500 | 81.0 | 83.0 | 73.0 | 5.0 | 9.0 | 85.0 | 60.0 | 100 | 0 |
| oracle | Bfull | 89.0 | 89.0 | 82.0 | 7.0 | 3.0 | 86.0 | 61.0 | 100 | 0 |


## Paired Bootstrap (1000 lần)

| So sánh | Chênh lệch (điểm %) | CI 95% | n | Có ý nghĩa |
|---|---|---|---|---|
| cond_acc@B100: lp - passage | +7.00 | [-5.00, +20.00] | 100 |  |
| cond_acc@B500: lp - passage | +5.00 | [-6.00, +16.00] | 100 |  |
| cond_acc@B100: lp - std | -18.00 | [-29.00, -7.00] | 100 | ✓ |
| cond_acc@B500: lp - std | +4.00 | [-5.00, +13.00] | 100 |  |
| cond_acc@B100: lp - lp_noptr | -9.00 | [-19.00, +2.00] | 100 |  |
| cond_acc@B500: lp - lp_noptr | +0.00 | [-7.00, +7.00] | 100 |  |
| cond_acc@B100: lp - lp_out | -5.00 | [-14.00, +5.00] | 100 |  |
| cond_acc@B500: lp - lp_out | -3.00 | [-10.00, +4.00] | 100 |  |
| correct@B100: lp - passage | +7.00 | [-4.00, +20.00] | 100 |  |
| correct@B500: lp - passage | +3.00 | [-8.00, +13.00] | 100 |  |
| correct@B100: lp - std | -16.00 | [-27.00, -4.00] | 100 | ✓ |
| correct@B500: lp - std | +3.00 | [-6.00, +13.00] | 100 |  |
| correct@B100: lp - lp_noptr | -8.00 | [-18.00, +2.00] | 100 |  |
| correct@B500: lp - lp_noptr | -1.00 | [-8.00, +6.00] | 100 |  |
| correct@B100: lp - lp_out | -6.00 | [-15.00, +3.00] | 100 |  |
| correct@B500: lp - lp_out | -2.00 | [-9.00, +5.00] | 100 |  |
| overgeneralized@B100: lp - passage | +0.00 | [-9.00, +8.00] | 100 |  |
| overgeneralized@B500: lp - passage | -3.00 | [-10.00, +4.00] | 100 |  |
| overgeneralized@B100: lp - std | +5.00 | [+0.00, +11.00] | 100 |  |
| overgeneralized@B500: lp - std | -4.00 | [-10.00, +2.00] | 100 |  |
| overgeneralized@B100: lp - lp_noptr | -1.00 | [-7.00, +5.00] | 100 |  |
| overgeneralized@B500: lp - lp_noptr | +0.00 | [-5.00, +5.00] | 100 |  |
| overgeneralized@B100: lp - lp_out | +2.00 | [-4.00, +8.00] | 100 |  |
| overgeneralized@B500: lp - lp_out | +1.00 | [-3.00, +6.00] | 100 |  |
| cond_cov_lex@B100: lp - passage | +5.00 | [-6.00, +15.00] | 100 |  |
| cond_cov_lex@B500: lp - passage | -1.00 | [-8.00, +7.00] | 100 |  |
| cond_cov_lex@B100: lp - std | -12.00 | [-19.00, -4.00] | 100 | ✓ |
| cond_cov_lex@B500: lp - std | +1.00 | [-4.00, +6.00] | 100 |  |
| cond_cov_lex@B100: lp - lp_noptr | -10.00 | [-18.00, -2.00] | 100 | ✓ |
| cond_cov_lex@B500: lp - lp_noptr | +2.00 | [-4.00, +7.00] | 100 |  |
| cond_cov_lex@B100: lp - lp_out | -11.00 | [-18.00, -4.00] | 100 | ✓ |
| cond_cov_lex@B500: lp - lp_out | +1.00 | [-5.00, +7.00] | 100 |  |
| cond_phrase@B100: lp - passage | +8.00 | [-2.00, +18.00] | 100 |  |
| cond_phrase@B500: lp - passage | +3.00 | [-7.00, +13.00] | 100 |  |
| cond_phrase@B100: lp - std | -14.00 | [-24.00, -4.00] | 100 | ✓ |
| cond_phrase@B500: lp - std | -3.00 | [-12.00, +6.00] | 100 |  |
| cond_phrase@B100: lp - lp_noptr | -10.00 | [-20.00, +0.00] | 100 |  |
| cond_phrase@B500: lp - lp_noptr | -4.00 | [-11.00, +3.00] | 100 |  |
| cond_phrase@B100: lp - lp_out | -9.00 | [-19.00, +0.00] | 100 |  |
| cond_phrase@B500: lp - lp_out | -3.00 | [-11.00, +5.00] | 100 |  |
