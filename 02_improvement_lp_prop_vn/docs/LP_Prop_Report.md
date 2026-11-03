# Báo Cáo Thực Nghiệm (Experimental Report) — Giai Đoạn 1: Data Curation & Benchmark LegalCond-7.4K

---

## 1. Tổng Quan Phần Việc (Stage 1 Scope & Ownership)

Báo cáo này tổng kết toàn bộ kết quả thực nghiệm của **Giai đoạn 1 (Stage 1: Data Curation, Corpus Sanitization & Quality Verification)** trong dự án LP-Prop, do thành viên **Trịnh Ngọc Thảo Hiền** (`Data & Benchmark Lead` — `HienTNTDE201096@fpt.edu.vn`) trực tiếp phụ trách và hiện thực hóa.

Mục tiêu cốt lõi của Giai đoạn 1 là loại bỏ triệt để các nguồn dữ liệu rác, văn bản dự thảo chưa ban hành và các phân mảnh tiêu đề từ bộ dữ liệu gốc, xây dựng nên bộ benchmark chuẩn hóa **LegalCond-7.4K** có độ tin cậy pháp lý cao và tỷ lệ rò rỉ thông tin tuyệt đối bằng 0.

---

## 2. Kết Quả Làm Sạch Ngữ Liệu Pháp Luật (Corpus Sanitization)

### 2.1. Thống kê Quy trình Lọc (`s1_clean.py` $\to$ `stats_v2.json`)
Bộ dữ liệu thô ban đầu được trích xuất từ tập `thangvip/vietnamese-legal-qa` trên Hugging Face. Toàn bộ quy trình xử lý và làm sạch cho kết quả như sau:

| Tiêu chí xử lý | Số lượng ghi nhận | Ý nghĩa & Tác động kỹ thuật |
| :--- | :---: | :--- |
| **Tổng số điều ban đầu** | **9.715 điều** | Toàn bộ corpus thô chứa 29.145 cặp câu hỏi-đáp tự động. |
| **Lọc bỏ văn bản dự thảo** | **-2.316 điều** | Loại bỏ triệt để các văn bản mang tiền tố *"Dự thảo Luật"*, *"Dự thảo Nghị định"*. |
| **Lọc bỏ QA ảo sinh trên dự thảo** | **-6.948 cặp QA** | Xóa bỏ **23.8%** tổng tập QA gốc để ngăn ngừa ảo giác pháp lý từ các quy định chưa được Quốc hội thông qua. |
| **Lọc bỏ phân mảnh tiêu đề** | **-5 điều** | Cắt bỏ các dòng rỗng chỉ chứa tên chương/mục (`a3382`, `a3746`, `a4087`, `a4340`, `a6242`). |
| **Gộp điều luật trùng nội dung** | **-3 điều** | Dùng hàm băm MD5 trên văn bản chuẩn hóa để gộp 3 cặp trùng: `a3701`$\to$`a2365`, `a3703`$\to$`a2366`, `a8494`$\to$`a4033`. |
| **Corpus chính thức (LegalCond-7.4K)** | **7.391 điều** | Tập dữ liệu sạch, có hiệu lực pháp lý cao nhất, thuộc **107 đạo luật** enacted. |
| **Tổng số Passages sinh ra** | **12.425 đoạn** | Đoạn văn bản chuẩn (100–190 từ) làm đơn vị đối đầu trong retrieval. |

---

## 3. Phân Tách Tập Document-Level Không Rò Rỉ (Zero-Leakage Split)

Để đảm bảo không xảy ra hiện tượng rò rỉ thuật ngữ, định nghĩa chung (thường nằm ở Điều 2 hoặc Điều 3 của luật) hoặc cấu trúc ngữ pháp giữa tập phát triển và tập đánh giá, dữ liệu được chia tách nghiêm ngặt theo **cấp văn bản luật (Statute-level)**:

$$\mathcal{L}(\mathcal{D}_{\text{eval}}) \cap \mathcal{L}(\mathcal{D}_{\text{dev}}) = \emptyset$$

* **Tập Đánh giá ($\mathcal{D}_{\text{eval}}$):** Gồm **93 đạo luật** với **6.468 điều** (chiếm 87.5% tổng corpus). Toàn bộ 1.200 câu hỏi đánh giá truy xuất và QA được thực hiện độc quyền trên tập này.
* **Tập Phát triển ($\mathcal{D}_{\text{dev}}$):** Gồm **14 đạo luật** với **923 điều** (chiếm 12.5% tổng corpus), dành riêng cho việc cân chỉnh prompt và phát triển quy tắc đồ thị.
* **Tỷ lệ rò rỉ ranh giới luật:** **Đúng 0.0%**.

---

## 4. Trích Xuất Mỏ Neo Logic (Gold Logic Spans)

Trên tập đánh giá $\mathcal{D}_{\text{eval}}$ (6.468 điều), hệ thống regex pháp lý đã trích xuất được **3.063 mỏ neo điều kiện** làm căn cứ đánh giá khả năng bao phủ điều kiện (CCR):

| Nhóm mỏ neo logic | Mẫu cú pháp đại diện | Số lượng trên `eval` | Tỷ lệ (%) | Vai trò trong quy phạm pháp luật |
| :--- | :--- | :---: | :---: | :--- |
| **`VỚI_ĐIỀU_KIỆN`** | *với điều kiện, khi đáp ứng...* | 2.468 | 80.57% | Điều kiện tiên quyết để được hưởng quyền hoặc cấp phép. |
| **`TRỪ_TRƯỜNG_HỢP`** | *trừ trường hợp, ngoại trừ...* | 435 | 14.20% | Ngoại lệ luật định phủ quyết hoặc hạn chế quy tắc chung. |
| **`NHƯNG_PHẢI`** | *nhưng phải bảo đảm, nhưng phải...* | 148 | 4.83% | Nghĩa vụ bắt buộc đi kèm khi thực thi quyền. |
| **`KHÔNG_ÁP_DỤNG`** | *không áp dụng đối với...* | 12 | 0.39% | Quy định loại trừ phạm vi áp dụng của điều luật. |
| **Tổng cộng** | --- | **3.063** | **100.00%** | **Căn cứ ground-truth cho toàn bộ benchmark.** |

---

## 5. Thẩm Định Chất Lượng Chuyên Gia (Human Quality Verification)

Nhóm đã thực hiện quy trình thẩm định người thật độc lập hai vòng trên mẫu phân tầng ngẫu nhiên **100 spans** qua **51 đạo luật khác nhau** (`results/span_review_v2/span_review_v2_expert_verified.csv`):

* **Phân bố mẫu:** `VỚI_ĐIỀU_KIỆN` (55), `TRỪ_TRƯỜNG_HỢP` (25), `NHƯNG_PHẢI` (15), `KHÔNG_ÁP_DỤNG` (5).
* **Kết quả thẩm định trên tập sạch LegalCond-7.4K:**
  * **Độ chính xác nghiêm ngặt (Strict Precision — `Đ`):** **95.0%** (95/100 spans gói trọn vẹn điều kiện pháp lý, không bị cắt cụt ngữ nghĩa).
  * **Phụ lục tham chiếu (Minor Parenthetical — `P`):** **5.0%** (5/100 spans chứa trích dẫn phụ lục đi kèm nhưng vẫn đúng quy định).
  * **Lỗi nặng / Đứt gãy logic (`S`):** **0.0%** (0/100 spans bị mất điều kiện hay lỗi cú pháp).
  * **Hệ số đồng thuận (Cohen's Kappa):** $\kappa = 0.887$ (Mức độ đồng thuận gần như tuyệt đối giữa 2 kiểm định viên).

### 🔍 So Sánh Đối Chứng với Tập Raw Chưa Làm Sạch (Ablation Analysis)
Để khẳng định tính sống còn của công đoạn làm sạch dữ liệu Stage 1:
* Khi kiểm định trên 100 mẫu của tập thô ban đầu (`span_review_v1`), có tới **37 mẫu rơi vào các điều luật dự thảo** chưa được thông qua (trong đó có 16 mẫu từ riêng dự thảo `a8020`).
* Độ chính xác pháp lý thực tế trên tập thô bị kéo tụt xuống chỉ còn **61.0%**.
* $\implies$ Điều này chứng minh rằng nếu không qua bước lọc dự thảo và làm sạch nghiêm ngặt của Hiền, mọi kết quả benchmark truy xuất và QA sau đó đều bị sai lệch nghiêm trọng.

---

## 6. Phân Tích Hình Thái Độ Dài Điều Luật

Thống kê độ dài từ ngữ trên 7.391 điều luật của LegalCond-7.4K:
* **Độ dài trung bình:** **253.6 từ/điều** (bác bỏ nhận định sai lầm cho rằng điều luật Việt Nam ngắn dưới 100 từ).
* **77.3%** số điều luật có độ dài $> 100$ từ.
* **45.0%** số điều luật có độ dài $> 200$ từ.
* $\implies$ Căn cứ thực chứng khẳng định: Truy xuất toàn bộ điều luật (Whole Article) chắc chắn gây tràn ngữ cảnh và loãng vector, chứng minh việc chia nhỏ thành Proposition có liên kết điều kiện của LP-Prop là hoàn toàn đúng đắn.
