# Hướng Dẫn Replicate Và Báo Cáo Chuẩn Hóa Thực Nghiệm Huấn Luyện Propositionizer

Tài liệu này thuộc khuôn khổ đồ án môn học **SEG301 - Search Engines**, phục vụ việc tái hiện (replication) bài báo khoa học:
> **Dense X Retrieval: What Retrieval Granularity Should We Use?**  
> *Tong Chen, Hongwei Wang, Sihao Chen, Wenhao Yu, Kaixin Ma, Xinran Zhao, Hongming Zhang, Dong Yu.*  
> EMNLP 2024. arXiv: [2312.06648](https://arxiv.org/abs/2312.06648).

Trọng tâm của thư mục này là module **Propositionizer** (Section 3, Figure 5, Appendix B) — mô hình phân rã đoạn văn bản (*passage*) thành tập hợp các mệnh đề độc lập, nguyên tử (*propositions*).

---

## 1. Cấu Trúc Thư Mục Notebooks

Trong thư mục `notebooks/`, các tệp thực nghiệm bao gồm:

| Tệp tin | Mô tả và vai trò |
|---|---|
| `densex_replication_run1,2.ipynb` | Toàn bộ pipeline retrieval chính thu nhỏ (Corpus 8,000 trang, đánh giá 4 retriever SimCSE, Contriever, DPR, GTR trên 3 độ hạt Passage, Sentence, Proposition; bộ đọc FiD và LLaMA-2-7B). |
| `Propositionizer_training.ipynb` | Phiên bản thực nghiệm ban đầu do cá nhân tự triển khai (v1), tập trung vào việc dựng pipeline huấn luyện nhanh `flan-t5-base`. |
| `Propositionizer_training_v2.ipynb` | Phiên bản chuẩn hóa sau khi thống nhất với nhóm (v2), khắc phục toàn bộ các lỗi phương pháp luận khoa học, đo lường theo đúng chuẩn bài báo gốc và tái hiện đường cong Scaling Law trong Figure 5. |

---

## 2. Quá Trình Thay Đổi: Từ Triển Khai Cá Nhân (v1) Đến Thống Nhất Nhóm (v2)

Trong giai đoạn đầu, notebook `Propositionizer_training.ipynb` được hoàn thành với mục tiêu cá nhân là kiểm chứng tính khả thi của việc fine-tune mô hình Seq2Seq. Tuy nhiên, qua các buổi thảo luận, review chéo mã nguồn và đối chiếu nghiêm ngặt với phương pháp luận trong bài báo gốc, nhóm đã nhận diện nhiều điểm bất cập mang tính phương pháp luận (methodological flaws) trong phiên bản đầu. Notebook `Propositionizer_training_v2.ipynb` ra đời để chuẩn hóa toàn bộ quy trình.

### 2.1. Bảng so sánh tổng hợp giữa hai phiên bản

| Tiêu chí | Phiên bản cá nhân ban đầu (`v1`) | Phiên bản chuẩn hóa cùng nhóm (`v2`) | Cơ sở học thuật & Mục đích thay đổi |
|---|---|---|---|
| **Phương thức đọc dữ liệu** | Đọc file parquet cục bộ từ Kaggle Input (`corpus_passage.parquet`) bằng DuckDB. | Đọc luồng trực tiếp (`streaming`) từ Hugging Face Hub thông qua `HfFileSystem` và `ThreadPoolExecutor`. | Tránh phụ thuộc vào đường dẫn cục bộ cá nhân; giúp các thành viên trong nhóm có thể chạy lại độc lập mà không cần tải hàng gigabyte dữ liệu về đĩa. |
| **Phân chia Train / Dev** | Trích xuất ngẫu nhiên (Reservoir sampling) 4,000 passage độc lập, chia 3,500 train / 500 dev. | Phân chia tách biệt theo Shard bài viết Wikipedia (`N_TRAIN_SHARDS=24`, `N_DEV_SHARDS=4`), chia 6,477 train / 1,000 dev. | **Chống rò rỉ dữ liệu (Data Leakage):** Ở v1, các đoạn văn thuộc cùng một trang Wikipedia (`page_id`) xuất hiện ở cả tập train và dev. Ở v2, tỷ lệ trang trùng lặp bị chặn triệt để bằng `assert` (`page_overlap = 0`). |
| **Chọn lọc dữ liệu (Selection Bias)** | Lọc điều kiện nhân tạo `HAVING len(prop_list) >= 2 AND len(prop_list) <= 10`. | Giữ toàn bộ phân phối tự nhiên của passage; chỉ loại các mẫu có nhãn vượt quá 512 token (`tgt_len > MAX_TGT`). | Ở v1, việc gán cứng số mệnh đề 2-10 làm sai lệch phân phối thực tế. Ở v2, chỉ loại mẫu quá dài để mô hình không học sinh JSON bị ngắt cụt. |
| **Độ lớn tập Dev** | 500 mẫu. | 1,000 mẫu. | Khớp chuẩn quy mô đánh giá tập Dev được công bố trong bài báo gốc. |
| **Phương pháp tính Metric** | Nối toàn bộ proposition thành một chuỗi duy nhất: `" ".join(props)` rồi chấm BERTScore text-to-text. | **Set-based F1**: Bipartite matching ma trận tương đồng pairwise BERTScore giữa từng $\hat{p}$ dự đoán và $p$ tham chiếu. | Nối chuỗi (v1) làm điểm F1 bị thổi phồng ảo (do cùng ngữ cảnh đoạn văn). v2 đo lường đúng năng lực phân tách từng mệnh đề rời rạc theo công thức Section 3 bài báo. |
| **Thang điểm đo lường** | Chỉ đo BERTScore gốc (Raw). | Báo cáo đồng thời cả **BERTScore Raw** và **BERTScore Rescaled** (rescale with baseline). | `roberta-large` có điểm Raw nền rất cao (~0.85-0.90 ngay cả với văn bản ít liên quan). Điểm Rescaled làm rõ độ cải thiện thực chất của mô hình. |
| **Hệ thống Baseline đối chứng** | Không có baseline đối chứng nào. | Tích hợp 4 mốc so sánh: (1) Copy Passage, (2) Tách câu bằng regex, (3) Zero-shot Flan-T5, (4) Teacher model gốc của tác giả. | Có mốc tham chiếu khoa học: chứng minh việc fine-tune thực sự vượt trội hơn các phương pháp ngây thơ (heuristic) hay zero-shot. |
| **Phạm vi tái hiện Figure 5** | Chỉ chạy 1 điểm dữ liệu đơn lẻ (Flan-T5-base trên 3,500 mẫu). | Chạy thực nghiệm lưới dữ liệu đa mức: $N \in \{500, 1000, 2000, 4000\}$. | Tái hiện đúng **Scaling Law** của Figure 5: thể hiện rõ tương quan giữa kích thước tập dữ liệu huấn luyện và chất lượng mô hình. |
| **Kiểm soát tính hợp lệ cấu trúc** | Chỉ kiểm tra bằng cách thử decode 1 câu mẫu ở cuối notebook. | Bổ sung 3 chỉ số tự động: tỷ lệ JSON hợp lệ (`json_ok_%`), số mệnh đề trung bình (`avg_#props`), tỷ lệ mệnh đề lặp (`dup_props_%`). | Đánh giá toàn diện các lỗi sinh văn bản thực tế (lỗi cú pháp JSON, sinh lặp vô hạn). |
| **Đánh giá định tính (Human Evaluation)** | Không có. | Xuất file mẫu 30 câu ngẫu nhiên (`propositionizer_examples_for_manual_check.csv`) theo Table 2 bài báo. | Cho phép các thành viên trong nhóm chấm chéo 3 tiêu chí cốt lõi: *Faithful* (Trung thực), *Minimal* (Nguyên tử), *Stand-alone* (Độc lập ngữ cảnh). |

---

### 2.2. Chi tiết các cải tiến phương pháp luận cốt lõi

#### A. Khắc phục lỗi rò rỉ dữ liệu (Data Leakage)
Trong `Propositionizer_training.ipynb`, câu lệnh SQL lấy mẫu dữ liệu:
```sql
SELECT ... FROM passages p JOIN grouped_props g ON p.id = g.passage_id USING SAMPLE 4000
```
Phương thức này chọn ngẫu nhiên ở cấp độ từng `passage_id`. Vì một bài viết Wikipedia thường có nhiều đoạn văn liên tiếp (chung tiền tố 15 ký tự đầu của `id`), tập huấn luyện và tập kiểm định vô tình chứa các đoạn văn từ cùng một nguồn ngữ cảnh.  
Trong `Propositionizer_training_v2.ipynb`, dữ liệu được chia theo shard ngay từ đầu: 24 shard đầu chỉ dành cho huấn luyện, 4 shard riêng biệt dành cho kiểm định. Kiểm tra chéo bằng tập hợp bảo đảm tính cô lập tuyệt đối:
```python
assert not ({r["page"] for r in train_ok} & {r["page"] for r in dev}), "LEAK: trang xuất hiện ở cả train và dev"
```

#### B. Chuẩn hóa thuật toán tính Set-based F1
Trong phiên bản ban đầu, toàn bộ danh sách mệnh đề được ghép chuỗi lại:
```python
# v1: Nối chuỗi sai lệch
p_clean = " ".join([str(p).strip() for p in preds if str(p).strip()])
r_clean = " ".join([str(p).strip() for p in targets if str(p).strip()])
P, R, F1 = score([p_clean], [r_clean], model_type="roberta-large")
```
Cách tính này biến bài toán đánh giá tập hợp thành bài toán so khớp văn bản dài, khiến BERTScore đạt ~81-82% nhưng không phản ánh việc mô hình có tách đúng ranh giới các mệnh đề hay không.

Trong phiên bản v2, thuật toán được cài đặt chuẩn xác theo Section 3 của bài báo:  
Với tập mệnh đề dự đoán $\hat{P} = \{\hat{p}_1, \dots, \hat{p}_m\}$ và tập tham chiếu $P = \{p_1, \dots, p_n\}$, độ tương đồng $s(\hat{p}, p)$ là BERTScore-F1 giữa hai mệnh đề. Độ chính xác (Precision) và độ phủ (Recall) của tập hợp được tính như sau:

$$\text{Precision} = \frac{1}{|\hat{P}|} \sum_{\hat{p} \in \hat{P}} \max_{p \in P} s(\hat{p}, p)$$

$$\text{Recall} = \frac{1}{|P|} \sum_{p \in P} \max_{\hat{p} \in \hat{P}} s(\hat{p}, p)$$

$$F_1 = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$

Mã nguồn triển khai ma trận ghép cặp trong v2:
```python
def set_f1(F, spans):
    out = []
    for s, n_p, n_r in spans:
        if n_p == 0 or n_r == 0:
            out.append((0.0, 0.0, 0.0))
            continue
        M = F[s:s + n_p * n_r].reshape(n_p, n_r)
        P = M.max(1).mean()
        R = M.max(0).mean()
        f1 = (2 * P * R / (P + R)) if (P + R > 0) else 0.0
        out.append((P, R, f1))
    return np.array(out).mean(0)
```

---