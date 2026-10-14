# Kết Quả Huấn Luyện Propositionizer (Replicate Figure 5)

Thư mục này chứa kết quả huấn luyện (fine-tuning) mô hình **Flan-T5-base** thành **Propositionizer** học sinh (Student Model) chưng cất từ **Flan-T5-large** (Teacher Model của tác giả Chen et al., 2024).

---

## 1. Danh sách file và ý nghĩa

| Tên file | Mô tả & Ý nghĩa khoa học |
| :--- | :--- |
| `figure5_propositionizer.png` | **Biểu đồ sao chép Figure 5 trong bài báo gốc**: Thể hiện F1-score (rescaled) và chất lượng output (JSON parsing rate, % trùng lặp) khi tăng số lượng mẫu train từ 0 (Zero-shot) -> 500 -> 1,000 -> 2,000 -> 4,000 mẫu so với Teacher Flan-T5-large. |
| `propositionizer_eval.csv` | **Bảng số liệu chi tiết đánh giá định lượng**: Gồm Raw P/R/F1, Rescaled P/R/F1, tỷ lệ JSON parse hợp lệ (`json_ok_%`), số lượng propositions trung bình sinh ra (`avg_#props`), tỷ lệ câu lặp (`dup_props_%`), và thời gian huấn luyện (`train_min`). |
| `propositionizer_train_loss.csv` | **Lịch sử hàm mất mát (Loss curve)** qua các epoch/steps khi train trên Kaggle GPU T4. |
| `propositionizer_examples_for_manual_check.csv` | **File kiểm định định tính (Qualitative Check)**: So sánh trực tiếp từng passage: câu gốc, proposition do Teacher sinh ra, và proposition do Student Flan-T5-base sinh ra ở các checkpoint. |
| `propositionizer_meta.json` | Metadata cấu hình huấn luyện: base model, batch size, learning rate, checkpoint paths. |

---

## 2. Kết quả chính (So sánh theo Figure 5 bài báo gốc)

| Hệ thống / Mô hình | Số mẫu train | F1 (Raw) | F1 (Rescaled) | JSON Hợp lệ (%) | TB số props/passage | Tỷ lệ trùng (%) | Thời gian train |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline: Copy Passage** | 0 | 0.9087 | 0.4488 | 100% | 1.00 | 0.00% | - |
| **Baseline: Tách câu (NLTK)** | 0 | 0.9376 | 0.6230 | 100% | 2.66 | 0.00% | - |
| **Zero-shot Flan-T5-base** | 0 | 0.8371 | 0.1558 | **0.0%** (lỗi format) | 1.11 | 0.31% | - |
| **Fine-tune @ 500 mẫu** | 500 | 0.9485 | 0.6782 | 70.4% | 8.01 | 25.38% | 2.7 phút |
| **Fine-tune @ 1000 mẫu** | 1,000 | 0.9577 | 0.7405 | 79.6% | 6.83 | 11.84% | 5.5 phút |
| **Fine-tune @ 2000 mẫu** | 2,000 | 0.9641 | 0.7823 | 88.8% | 5.93 | 6.27% | 11.1 phút |
| **Fine-tune @ 4000 mẫu** | 4,000 | **0.9701** | **0.8202** | **96.3%** | **5.50** | **2.04%** | 22.3 phút |
| **Teacher: Flan-T5-large** | 42,857 | **0.9997** | **0.9981** | **99.8%** | **6.02** | **0.01%** | - |

### Kết luận quan trọng cho bài báo cáo:
1. **Zero-shot thất bại hoàn toàn**: Flan-T5-base không biết cấu trúc JSON và không thể phân rã nếu không có fine-tuning (JSON format accuracy = 0%).
2. **Khả năng chưng cất (Distillation Efficiency)**: Chỉ cần **4,000 mẫu** (~9.3% dữ liệu của tác giả), mô hình nhỏ Flan-T5-base đã đạt Rescaled F1 = **0.8202**, định dạng JSON chuẩn **96.3%**, số proposition trung bình là **5.50** (rất gần mốc 6.0 của tác giả).
