# Báo cáo kết quả — Dense X Retrieval Replication (SEG301)

**Paper:** [Dense X Retrieval: What Retrieval Granularity Should We Use?](https://arxiv.org/abs/2312.06648) (Chen et al., EMNLP 2024)
**Notebook:** [`notebooks/densex_replication_run1,2.ipynb`](notebooks/) · **Kết quả:** [`results/`](results/) · **Setup:** [PLAN.md](PLAN.md)
**So sánh với paper:** [`analysis/compare_with_paper.py`](analysis/compare_with_paper.py) → `results/paper_vs_ours.csv`, `results/trend_summary.csv`

## Tóm tắt

- **Retrieval (Table 3):** proposition có Recall cao hơn passage ở **14/16 ô** (NQ, SQuAD × 4 retriever × R@5/R@20). Thứ tự đầy đủ Proposition > Sentence > Passage giữ ở **11/16 ô** (paper: 14/16). Dấu của Δ(proposition − passage) **trùng với paper ở cả 16/16 ô**, kể cả 2 ô proposition thua (DPR trên NQ), nơi paper cũng thua.
- **Kiểm định thống kê:** proposition thắng passage **có ý nghĩa (McNemar p < 0.05) ở 11/16 ô** Recall và **10/16 ô** FiD EM. **Không có ô nào** passage thắng proposition có ý nghĩa.
- **QA:** proposition > passage ở 13/16 ô với FiD (Table 4) và 13/16 ô với LLaMA-2-7B (Table 5). Mọi cấu hình có retrieval đều vượt closed-book.
- **Khác paper:** Recall và EM tuyệt đối cao hơn paper khoảng 5–20 điểm, do corpus chỉ có 8,000 pages. Vì vậy chỉ so sánh **xu hướng**, không so số tuyệt đối.
- **Kết luận:** xu hướng chính của paper được tái hiện. Proposition giúp nhiều nhất với retriever **unsupervised** (SimCSE, Contriever) và trên dữ liệu **chưa thấy** (SQuAD), gần như không đổi với retriever supervised trên NQ. Xu hướng **không** giữ ở 100% ô, và paper cũng không giữ 100%.

## 1. Setup thực tế

| | Giá trị |
|---|---|
| Corpus | 8,000 pages FactoidWiki = 537 gold pages (SQuAD 45, NQ 492) + 7,463 distractor random (pool 2.2M pages, 367 shards) |
| Units | passage 78,537 · sentence 224,133 · proposition 506,413 |
| Độ dài trung bình | passage 62.5 từ (paper 58.5) · sentence 21.9 (21.0) · proposition 11.5 (11.2) |
| Câu hỏi | 500 SQuAD v1.1 dev + 500 NQ-open test, seed 42 |
| Gold title | match 93.8% (SQuAD), 93.3% (NQ); title thiếu được liệt kê trong `missing_titles_*.csv` |
| Answer có trong corpus | NQ 90.0% · SQuAD 90.2% (`answer_coverage.csv`) |
| Chống leak | bỏ 8 câu SQuAD dev trùng train; NQ không trùng; title SQuAD dev ∩ train = ∅ |
| Sanity FiD | oracle EM trên 100 câu NQ = 57.0 (`fid_sanity.json`) → checkpoint nạp đúng |

**Vì sao chọn 8,000 pages:** corpus đầy đủ của paper có 6M pages, 257M propositions. Encode 4 retriever × 3 granularity cho cỡ đó vượt xa quota GPU Kaggle (T4×2, 30h/tuần) và dung lượng đĩa. Với 8,000 pages, ~506k propositions × 4 retriever fp16 ≈ 3 GB, và toàn bộ pipeline chạy trong 2 session.

## 2. Retrieval — Table 3 (Passage Recall@k)

Số liệu: `table3_recall.csv`, `trend_check.csv`, `paper_vs_ours.csv`

| Retriever | Granularity | NQ R@5 | NQ R@20 | SQuAD R@5 | SQuAD R@20 |
|---|---|---|---|---|---|
| SimCSE | passage | 39.0 | 57.6 | 45.2 | 58.6 |
| | sentence | 47.4 | 65.0 | 53.6 | 65.6 |
| | proposition | **55.2** | **71.0** | **55.0** | **67.8** |
| Contriever | passage | 48.4 | 71.2 | 62.8 | 76.8 |
| | sentence | 52.8 | 75.0 | 66.2 | 76.6 |
| | proposition | **55.6** | **75.8** | **69.8** | **77.6** |
| DPR | passage | 73.4 | 81.4 | 49.6 | 63.2 |
| | sentence | **74.2** | **81.8** | 52.4 | 66.2 |
| | proposition | 71.6 | 80.8 | **56.6** | **68.6** |
| GTR | passage | 74.2 | 81.2 | 67.6 | 75.8 |
| | sentence | 73.0 | 81.2 | 73.0 | 78.4 |
| | proposition | **74.8** | **81.6** | **75.2** | **81.8** |

**Δ(proposition − passage), paper vs nhóm:**

| Retriever | NQ R@5 | NQ R@20 | SQuAD R@5 | SQuAD R@20 |
|---|---|---|---|---|
| SimCSE | +12.3 / **+16.2** | +14.6 / **+13.4** | +9.2 / **+9.8** | +8.4 / **+9.2** |
| Contriever | +7.6 / **+7.2** | +6.2 / **+4.6** | +9.9 / **+7.0** | +7.9 / **+0.8** |
| DPR | −0.6 / **−1.8** | −0.3 / **−0.6** | +3.1 / **+7.0** | +3.3 / **+5.4** |
| GTR | +0.2 / **+0.6** | +1.2 / **+0.4** | +8.9 / **+7.6** | +6.9 / **+6.0** |

(paper / **nhóm**)

**Nhận xét:**

1. **Unsupervised retriever hưởng lợi nhiều nhất.** SimCSE tăng 9–16 điểm và giữ đủ thứ tự Prop > Sent > Pass ở 4/4 ô. Contriever giữ ở 3/4 ô; riêng SQuAD R@20 thì 3 granularity gần như bằng nhau (76.6–77.6).
2. **Supervised retriever trên NQ: gần như không khác biệt.** DPR (train trên NQ) và GTR (fine-tune có NQ) có Δ trong khoảng ±2 điểm. Paper cũng ghi nhận điều này: *"all supervised retrievers demonstrate comparable performance across three levels of retrieval granularity in NQ, TQA, and WebQ"*, và giải thích là các retriever này đã được train trên cặp query–passage. Hai ô DPR/NQ mà proposition thua là **tái hiện đúng paper**, không phải lỗi.
3. **Trên SQuAD, proposition thắng ở cả 4 retriever** (+6 đến +10 điểm ở R@5), kể cả với supervised retriever. Kết quả này khớp với lập luận của paper rằng proposition giúp retriever **generalize** tốt hơn sang phân phối câu hỏi khác.
4. **Kết quả thô:** thứ tự đầy đủ giữ ở 11/16 ô (paper 14/16), proposition > passage ở 14/16 ô, dấu Δ trùng paper 16/16. 3 ô "mất" thứ tự so với paper (GTR/NQ ×2, Contriever/SQuAD R@20) đều có chênh lệch giữa các granularity ≤ 1.2 điểm, nhỏ hơn độ rộng CI ở mục 5.

Các metric phụ ủng hộ cùng kết luận: MRR@100 (`mrr.csv`) với SimCSE NQ đi từ 26.7 → 35.0 → 41.1 (pass → sent → prop), và Recall@1 (`recall_all_k.csv`) với GTR SQuAD đi từ 48.8 → 56.6 → 60.8.

## 3. Mật độ thông tin — Recall@l words (Figure 4/7)

Số liệu: `recall_at_words.csv` · Hình:

![Recall@words](results/recall_at_words.png)

Metric này đo việc câu trả lời có xuất hiện trong **l từ đầu tiên** của các unit được truy xuất hay không. Đây là phép so sánh công bằng hơn Recall@k, vì cùng một ngân sách từ thì chứa được nhiều proposition (11.5 từ) hơn passage (62.5 từ).

| Retriever | Dataset | Passage @100 | Prop @100 | Δ | Passage @500 | Prop @500 | Δ |
|---|---|---|---|---|---|---|---|
| SimCSE | NQ | 26.0 | 35.6 | +9.6 | 49.4 | 55.4 | +6.0 |
| SimCSE | SQuAD | 30.0 | 45.8 | +15.8 | 50.0 | 61.0 | +11.0 |
| Contriever | NQ | 27.2 | 35.6 | +8.4 | 54.8 | 60.8 | +6.0 |
| Contriever | SQuAD | 44.2 | 54.2 | +10.0 | 66.6 | 67.2 | +0.6 |
| DPR | NQ | 58.4 | 60.4 | +2.0 | 75.8 | 73.0 | −2.8 |
| DPR | SQuAD | 32.8 | 44.8 | +12.0 | 53.6 | 60.6 | +7.0 |
| GTR | NQ | 55.0 | 63.0 | +8.0 | 76.4 | 76.4 | 0.0 |
| GTR | SQuAD | 52.0 | 66.6 | +14.6 | 70.2 | 74.2 | +4.0 |

- Ở **100 từ**, proposition hơn passage ở **8/8** cấu hình, kể cả DPR/NQ (+2.0) và GTR/NQ (+8.0), là những nơi Recall@k không thấy khác biệt.
- Khi ngân sách tăng lên **500 từ**, khoảng cách thu hẹp (8/8 → 6/8 ô dương). Điều này khớp với phân tích của paper: proposition có lợi nhất khi ngân sách context nhỏ, vì mỗi từ được truy xuất đều liên quan tới câu hỏi. Passage dài chứa nhiều thông tin thừa, nên chỉ "đuổi kịp" khi ngân sách lớn.

## 4. QA downstream

### 4.1 FiD T5-large — Table 4

Số liệu: `table4_fid_em.csv`, `table4_fid_mcnemar.csv`. Với mỗi granularity, top-5/top-20 **passage** được đưa vào FiD, giống paper.

| Retriever | Granularity | NQ top5 | NQ top20 | SQuAD top5 | SQuAD top20 |
|---|---|---|---|---|---|
| SimCSE | passage → prop | 27.6 → **36.8** | 38.0 → **47.4** | 28.2 → **36.0** | 34.6 → **40.8** |
| Contriever | passage → prop | 32.8 → **38.2** | 47.2 → **48.8** | 41.0 → **46.4** | **48.8** → 48.4 |
| DPR | passage → prop | **50.8** → 48.4 | 52.8 → **53.6** | 31.0 → **35.8** | 38.0 → **42.4** |
| GTR | passage → prop | 51.0 → **52.2** | **53.4** → 53.2 | 43.8 → **50.2** | 46.6 → **50.8** |

- Proposition > passage ở **13/16 ô**. Thắng có ý nghĩa (McNemar) ở 10/16 ô; không có ô nào thua có ý nghĩa.
- Cải thiện retrieval truyền sang QA rõ nhất với SimCSE (+6 đến +9 EM) và trên SQuAD.
- Mẫu hình giống Table 3: DPR/NQ top5 là ô duy nhất proposition thua khá rõ (−2.4, p = 0.096, không có ý nghĩa). Paper cũng có −1.4 ở ô này.

### 4.2 LLaMA-2-7B 4-shot — Table 5

Số liệu: `table5_em.csv`, `qa_contains_answer.csv`. Context bị cắt theo ngân sách 100 / 500 token.

| Retriever | Granularity | NQ @100 | NQ @500 | SQuAD @100 | SQuAD @500 |
|---|---|---|---|---|---|
| SimCSE | passage → prop | 31.8 → **37.0** | 33.6 → **39.8** | 20.4 → **28.4** | 28.4 → **33.4** |
| Contriever | passage → prop | **36.4** → 36.2 | **40.6** → 39.2 | 24.2 → **35.2** | 38.0 → **39.8** |
| DPR | passage → prop | 40.6 → **42.2** | 44.8 → **45.4** | 20.8 → **27.2** | 30.0 → **31.8** |
| GTR | passage → prop | 38.8 → **42.0** | **45.0** → 44.4 | 27.6 → **40.2** | 37.4 → **39.0** |
| Closed-book | — | 25.8 | 25.8 | 14.6 | 14.6 |

- **Ngân sách 100 token:** proposition > passage ở **7/8** ô. Lợi thế trên SQuAD rất lớn: +6.4 đến +12.6 EM.
- **Ngân sách 500 token:** proposition > passage ở 6/8 ô, chênh lệch nhỏ hơn (SQuAD chỉ +1.6 đến +5.0). Kết quả này cùng chiều với mục 3: ngân sách càng nhỏ, mật độ thông tin của proposition càng có giá trị.
- Thứ tự đầy đủ Prop > Sent > Pass chỉ giữ ở 8/16 ô (paper 13/16). Sentence và proposition thường sát nhau (chênh < 2 EM), nên với 500 câu hỏi, thứ tự giữa hai mức này dễ đảo do nhiễu.
- Mọi cấu hình có retrieval đều vượt closed-book: +6 đến +20 EM trên NQ, +6 đến +26 EM trên SQuAD.

## 5. Kiểm định thống kê

Paper chỉ báo cáo điểm trung bình. Bản replication bổ sung hai kiểm định để biết chênh lệch là thật hay chỉ là nhiễu do mẫu 500 câu.

### 5.1 McNemar test (paired, cùng 500 câu hỏi)

Số liệu: `mcnemar_win_loss.csv` (Recall), `table4_fid_mcnemar.csv` (FiD EM). Với mỗi cặp granularity, đếm số câu A đúng – B sai (*wins*) và A sai – B đúng (*losses*), rồi kiểm định xem wins ≠ losses có ý nghĩa không.

| So sánh (Recall@k) | Thắng có ý nghĩa | Không có ý nghĩa | Thua có ý nghĩa |
|---|---|---|---|
| proposition vs passage | **11/16** | 5/16 | **0/16** |
| sentence vs passage | 10/16 | 6/16 | 0/16 |
| proposition vs sentence | 6/16 | 10/16 | 0/16 |

Ví dụ điển hình (SimCSE, NQ, R@5): proposition đúng – passage sai **109 câu**, ngược lại chỉ **28 câu**, p < 0.0001.

5 ô không có ý nghĩa gồm 4 ô supervised retriever trên NQ (DPR, GTR) và Contriever SQuAD R@20, cũng chính là các ô có Δ nhỏ ở mục 2. **Không có ô nào cho thấy passage tốt hơn proposition một cách có ý nghĩa thống kê.**

### 5.2 Bootstrap 95% CI

Số liệu: `bootstrap_ci.csv`. CI có độ rộng khoảng ±4 điểm (ví dụ SimCSE NQ R@5: passage 39.0 [34.8, 43.2] so với proposition 55.2 [51.0, 59.6]). Hai CI **không chồng nhau** với SimCSE trên NQ (cả R@5 và R@20), nhưng chồng nhau gần như hoàn toàn ở DPR/GTR trên NQ. Điều này giải thích vì sao với n = 500, chênh lệch dưới ~3 điểm không thể kết luận được.

## 6. Phân tích thêm

### 6.1 Câu trả lời hiếm (long-tail) — Figure 3 chuyển thể

Số liệu: `recall_by_answer_frequency.csv`, `recall_by_answer_frequency.png`. Paper dùng tần suất entity (EntityQuestions). Ở đây dùng **số passage trong corpus chứa câu trả lời** làm proxy.

| SimCSE, R@20 | answer xuất hiện 1–2 lần | ≥ 30 lần |
|---|---|---|
| NQ: passage → proposition | 53.7 → 76.5 (**+22.8**) | 76.7 → 84.7 (+8.0) |

Với SimCSE trên NQ, lợi ích của proposition lớn gấp ~3 lần khi câu trả lời hiếm. Đây đúng là hiện tượng paper mô tả: *"retrieving by proposition shows a much larger advantage … with questions targeting less common entities"*. Tuy vậy, hiệu ứng này **không rõ** với các retriever và dataset khác (ví dụ SimCSE/SQuAD: +11.5 vs +11.2), nên chỉ xem là tái hiện **một phần**. Bin "0" (~10% câu) là các câu có answer không nằm trong corpus thu nhỏ, nên Recall = 0 ở mọi granularity.

### 6.2 Theo loại câu hỏi

Số liệu: `recall_by_question_type.csv` (R@20, trung bình trên 4 retriever). Proposition giúp rõ nhất ở các câu hỏi **factoid hẹp**: *when* (SQuAD 65.0 → 75.0), *where* (66.1 → 74.2), *who* (NQ 72.8 → 79.2). Câu *how/other* gần như không đổi. Điều này hợp lý, vì proposition là "một fact tối giản" nên khớp tốt với câu hỏi hỏi đúng một fact.

### 6.3 Error analysis — Table 6/7

Số liệu: `error_cases_top1.csv`: 568 câu mà top-1 của 3 granularity cho kết quả khác nhau (Contriever + GTR).

| Mẫu (passage / sentence / proposition) | Số câu |
|---|---|
| ✗✓✓ chỉ passage sai | 156 |
| ✗✗✓ **chỉ proposition đúng** | 132 |
| ✓✗✗ **chỉ passage đúng** | 82 |
| ✓✓✗ chỉ proposition sai | 82 |
| ✓✗✓ / ✗✓✗ | 61 / 55 |

Tổng cộng proposition đúng – passage sai **288 câu**, passage đúng – proposition sai **164 câu**.

Ví dụ cụ thể từng câu xem trong `error_cases_top1.csv`.

### 6.4 Chi phí index

Số liệu: `efficiency.csv`. Proposition có số unit gấp **6.45 lần** passage. Index fp16 tăng từ 115 MB lên 742 MB, và thời gian encode tăng ~2×. Paper ít nhắc tới đánh đổi hiệu năng – chi phí này, nhưng đây là điểm quan trọng khi triển khai thật: ở quy mô 6M pages, con số là 257M vectors so với 41M.

## 7. Vì sao số tuyệt đối cao hơn paper

Ví dụ SimCSE NQ R@5 passage: nhóm 39.0, paper 28.8. GTR NQ R@5: nhóm 74.2, paper 66.3. FiD và LLaMA EM cũng cao hơn 5–15 điểm.

1. **Ít distractor hơn rất nhiều:** 8,000 pages so với 6M (~0.13%). Retriever chỉ phải phân biệt gold với ~7.5k trang khác thay vì hàng triệu.
2. **Gold pages chiếm tỉ lệ lớn:** 32–35% số unit đến từ gold pages (`corpus_stats.csv`). Trong Wikipedia đầy đủ, tỉ lệ này gần như bằng 0.
3. **Không phải lỗi pipeline:** độ dài unit khớp paper (62.5 / 21.9 / 11.5 từ so với 58.5 / 21.0 / 11.2), sanity check oracle FiD đạt 57 EM, và quan trọng nhất là dấu của Δ trùng paper ở 16/16 ô Table 3.

Vì vậy báo cáo chỉ dùng **xu hướng tương đối giữa các granularity** để kết luận, không dùng số tuyệt đối.

## 8. Limitations

- **Quy mô nhỏ:** 500 câu/dataset, nên CI có độ rộng khoảng ±4 điểm và chênh lệch < 3 điểm không thể kết luận (mục 5). Corpus thu nhỏ làm bài toán dễ hơn thực tế, nên có thể đánh giá thấp lợi thế của proposition. Paper lập luận lợi thế này lớn hơn khi có nhiều distractor, nhưng nhóm chưa kiểm chứng được.
- **Chỉ 2/5 dataset** (NQ, SQuAD). Không có TQA, WebQ, EntityQuestions, nên Figure 3 chỉ được chuyển thể bằng proxy tần suất answer, và cột "Avg" của paper không so trực tiếp được.
- **Lệch phiên bản Wikipedia:** SQuAD (2016) và NQ (2018) so với FactoidWiki (2021). ~6–7% gold title không match, ~10% answer không còn trong corpus.
- **Distractor** chỉ lấy từ 367 shard chứa gold page, nên có thể không đại diện cho toàn bộ Wikipedia.
- **DPR-multiset đã thấy train split của NQ và SQuAD** (seen distribution). Paper cũng có vấn đề này: coi SQuAD là "unseen" dù DPR đã fine-tune trên SQuAD.
- **FiD** dùng checkpoint gốc nạp vào transformers mới (code gốc cần transformers 3.0.2), nên có thể lệch nhỏ.
- **Không tự chạy Propositionizer:** dùng sẵn proposition của tác giả, nên không đánh giá được chất lượng hay lỗi của bước tách proposition (Fig 5).

## 9. Kết luận

Trên corpus thu nhỏ 8,000 pages, bản replication **tái hiện được xu hướng chính** của Dense X Retrieval:

- Proposition ≥ passage ở hầu hết cấu hình retrieval (14/16) và QA (13/16 FiD, 13/16 LLaMA), không có trường hợp nào passage thắng có ý nghĩa thống kê.
- Lợi ích tập trung ở **unsupervised retriever**, **dữ liệu chưa thấy (SQuAD)**, **ngân sách context nhỏ** và **câu trả lời hiếm**. Với supervised retriever trên NQ, ba granularity gần như ngang nhau, đúng như paper.

Thứ tự đầy đủ Proposition > Sentence > Passage **không đúng ở mọi ô** (11/16 retrieval, 12/16 FiD, 8/16 LLaMA), chủ yếu do sentence và proposition sát nhau, chênh lệch nằm trong biên nhiễu của mẫu 500 câu.
