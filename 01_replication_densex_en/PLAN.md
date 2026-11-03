# Replication Plan — Dense X Retrieval (SEG301)

**Paper:** [Dense X Retrieval: What Retrieval Granularity Should We Use?](https://arxiv.org/abs/2312.06648) (Chen et al., EMNLP 2024)
**Repo tác giả:** [chentong0/factoid-wiki](https://github.com/chentong0/factoid-wiki) — chỉ gồm data (FactoidWiki) và Propositionizer, **không có code evaluation**. Phần đánh giá được viết lại theo Sec 4.3, Sec 5 và Appendix của paper.

**Mục tiêu:** kiểm chứng xu hướng tương đối **Proposition > Sentence > Passage**, không khớp số tuyệt đối. Corpus nhỏ hơn nhiều nên Recall tuyệt đối sẽ cao hơn paper.

## 1. So sánh setup

| Hạng mục | Paper | Replicate |
|---|---|---|
| Corpus | Wikipedia 2021-10-13 (FactoidWiki), 6M pages | **8,000 pages** lấy nguyên từ FactoidWiki = gold pages + distractor ngẫu nhiên (không trùng gold) |
| Granularity | passage (41M) / sentence (114M) / proposition (257M) | cùng 3 loại, dùng đúng unit của tác giả (không tự chạy Propositionizer) |
| Dataset | NQ, TQA, WebQ, SQuAD, EQ (full test) | **SQuAD v1.1 dev** + **NQ-open test**, mỗi dataset **500 câu** random (seed 42) |
| Gold title | — | SQuAD: field `title` · NQ: join câu hỏi với official NQ dev → `document.title` |
| Chống leak | — | dùng test split như paper; loại câu test trùng train; demo 4-shot lấy từ train; distractor ∩ gold = ∅ |
| Retriever | SimCSE, Contriever (unsupervised) · DPR, GTR (supervised) | giữ nguyên 4 retriever, đúng checkpoint HF trong Appendix |
| Map unit → passage | score passage = max score các unit thuộc passage | giống paper |
| Retrieval metric | Passage Recall@5/20 (Table 3), Recall@l words (Fig 4/7) | giống paper + Recall@1…100, MRR, gold-page recall |
| QA reader 1 | FiD T5-large `nq_reader_large`, top-5/20 passages (Table 4) | giống paper (checkpoint gốc, nạp vào transformers mới) |
| QA reader 2 | LLaMA-2-7B 4-shot, EM@100/500 tokens (Table 5) | giống paper (vLLM, greedy) + baseline closed-book |
| Phân tích khác | Fig 3 (entity frequency, EQ), Table 6/7 (error cases) | Fig 3 chuyển thể (độ hiếm của answer), Table 6/7, bootstrap 95% CI, McNemar test, theo loại câu hỏi, chi phí index |
| Không làm | — | train Propositionizer (Fig 5); TQA / WebQ / EQ |

## 2. Test set và gold title

| | SQuAD | NQ |
|---|---|---|
| Test set (giống paper / DPR) | SQuAD v1.1 dev (10,570 câu) — SQuAD không công bố test | NQ-open test (3,610 câu) = `nq_open` split `validation` |
| Nguồn HF | `rajpurkar/squad` | `google-research-datasets/nq_open` |
| Gold title | field `title` (48 bài) | join theo question text với `google-research-datasets/natural_questions` (dev) → `document.title` |
| Lấy mẫu | 500 câu random, seed 42 | 500 câu random, seed 42 |

Retriever chỉ dùng để đánh giá (không train / fine-tune). DPR-multiset đã được train trên train split của NQ và SQuAD — không trùng câu với test, chỉ "quen phân phối"; paper cũng đánh dấu các ô này trong Table 3.

## 3. Corpus thu nhỏ

| | Ước tính |
|---|---|
| Gold pages (SQuAD ~48 + NQ ~430–480) | ~480–530 |
| Distractor pages (random, loại gold) | ~7,470–7,520 |
| **Tổng** | **8,000 pages** |
| Units (passage / sentence / proposition) | ~80k / ~220k / ~500k |
| Embedding 4 retriever (fp16) | ~5 GB |

Số chính xác được notebook in ra khi chạy (`corpus_stats.csv`, `title_mapping_report.csv`).

## 4. Các stage

| Stage | Nội dung | Máy | Thời gian ước tính | Output chính |
|---|---|---|---|---|
| `data` | tải câu hỏi, check leak, verify title, dựng corpus 8,000 pages | CPU/GPU, Internet ON | 1.5–3h | `corpus/`, `questions.jsonl`, `corpus_meta.json` |
| `retrieval` | encode + search 4 retriever × 3 granularity | GPU T4×2 | 1–2h | `ranked/*.npz`, `efficiency.csv` |
| `fid` | Table 4 — FiD trên top-5/20 passages | GPU T4×2 | 1–2h | `fid_predictions.csv` |
| `qa` | Table 5 — LLaMA-2-7B (vLLM), session riêng | GPU T4×2 | 1–2h | `qa_predictions.csv` |
| `analysis` | bảng, hình, kiểm định thống kê | CPU/GPU | vài phút | `results/*.csv`, `*.png`, `summary.json` |

Chạy trên Kaggle 2 lần (tổng ~5–8h GPU, trong quota 30h/tuần):

1. **run1** = `data + retrieval + fid + analysis` → Table 3, Table 4, Fig 4/7, phân tích thống kê.
2. **run2** = `qa + analysis` (session mới, cần quyền `meta-llama/Llama-2-7b-hf`) → Table 5.

## 5. Kết quả sẽ báo cáo

| Paper | File kết quả |
|---|---|
| Table 1 — thống kê unit | `corpus_stats.csv` |
| Table 3 — Recall@5/20 | `table3_recall.csv`, `trend_check.csv` |
| Table 4 — EM FiD | `table4_fid_em.csv` |
| Table 5 — EM@l LLaMA-2-7B | `table5_em.csv` |
| Figure 4/7 — Recall@l words | `recall_at_words.csv/.png` |
| Figure 3 (chuyển thể) | `recall_by_answer_frequency.csv/.png` |
| Table 6/7 — error cases | `error_cases_top1.csv` |
| Phân tích thêm | `bootstrap_ci.csv`, `mcnemar_win_loss.csv`, `recall_all_k.csv`, `mrr.csv`, `gold_page_recall.csv`, `recall_by_question_type.csv` |

## 6. Limitations

- 500 câu/dataset và corpus 8,000 pages (~0.13% Wikipedia) → Recall tuyệt đối cao hơn paper; chỉ so sánh xu hướng giữa các granularity.
- Chỉ 2/5 dataset; cột "Avg" của paper là trung bình 5 dataset nên chỉ so từng cột NQ và SQuAD.
- Distractor lấy từ các shard chứa gold page.
- Lệch phiên bản Wikipedia (SQuAD 2016, NQ 2018 vs FactoidWiki 2021) → một số title bị miss, một số answer không còn trong bài.
- FiD chạy bằng checkpoint gốc nạp vào transformers mới (code FiD gốc yêu cầu transformers 3.0.2) → có thể lệch nhỏ.
