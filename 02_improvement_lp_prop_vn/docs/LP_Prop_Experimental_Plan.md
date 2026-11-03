# Kế Hoạch Thực Nghiệm (Experimental Plan) — Đề Xuất LP-Prop

---

## 1. Tiền Đề Nghiên Cứu Từ Bước Replicate (Inception & Empirical Premise)

Ý tưởng cốt lõi của đề xuất **LP-Prop** không phải là giả định lý thuyết đơn thuần, mà bắt nguồn từ phát hiện thực chứng khách quan trong quá trình nhóm thực hiện **Phần 1: Tái hiện Dense X (Downscaled Replication)**:

* **Phát hiện từ Corpus gốc (Wikipedia):**
  Trong quá trình đánh giá mô hình phân tách mệnh đề gốc (Flan-T5 Propositionizer của Chen et al., 2024), thành viên **Trịnh Ngọc Thảo Hiền** đã xây dựng công cụ quét lỗi logic tự động ([`scan_logic_errors.py`](../01_replication_densex_en/analysis/scan_logic_errors.py)) quét qua hàng vạn đoạn văn bản.
* **Bằng chứng thực nghiệm:**
  Kết quả ghi nhận tại [`01_replication_densex_en/results/04_logic_error_analysis/potential_logic_errors.csv`](../01_replication_densex_en/results/04_logic_error_analysis/potential_logic_errors.csv) cho thấy Propositionizer tiêu chuẩn thường xuyên **cắt đứt các mệnh đề điều kiện và ngoại lệ** (`unless`, `provided that`, `except that`, `only if`), biến các quy tắc có điều kiện thành khẳng định vô điều kiện sai sự thật (*Unconditional Fallacy*).
* **Chuyển dịch sang Miền Pháp Luật Việt Nam:**
  Nhận thấy lỗ hổng logic này gây ra hậu quả đặc biệt nghiêm trọng trong ngành Luật (nơi việc bỏ rơi một điều kiện "trừ trường hợp" hay "với điều kiện" sẽ đảo ngược hoàn toàn phán quyết pháp lý), nhóm quyết định mở rộng nghiên cứu sang bài toán cải tiến: **Logic-Preserving Proposition Retrieval (LP-Prop)** và xây dựng bộ benchmark chuẩn hóa trên hệ thống pháp luật Việt Nam (**LegalCond-7.4K**).

---

## 2. Câu Hỏi Nghiên Cứu & Giả Thuyết Khoa Học (Research Questions & Hypotheses)

Kế hoạch thực nghiệm được thiết kế nhằm trả lời 3 câu hỏi nghiên cứu cốt lõi:

* **RQ1 (Retrieval Condition Completeness):** Khi người dùng đặt câu hỏi nhạy cảm với điều kiện, liệu cơ chế liên kết và mở rộng đồ thị ngữ cảnh hai chiều của LP-Prop có giúp truy xuất đầy đủ điều kiện ràng buộc hơn so với Dense X chuẩn và Passage Retrieval hay không?
  * *Giả thuyết H1:* LP-Prop sẽ đạt tỷ lệ bao phủ điều kiện (CCR@B) cao hơn Dense X chuẩn ở cùng một ngân sách từ, đồng thời hạn chế tối đa số lượng quy tắc mồ côi (Orphan Rules).
* **RQ2 (Budget Efficiency & Precision):** Việc mở rộng ngữ cảnh theo đồ thị có làm phình to số lượng từ nạp vào LLM như Passage Retrieval truyền thống không?
  * *Giả thuyết H2:* Nhờ trích xuất ở mức proposition và chỉ kéo kèm đúng nút điều kiện phụ thuộc (1-hop), LP-Prop vẫn giữ được độ tập trung ngữ nghĩa cao hơn hẳn Passage Retrieval trong ngân sách $B \in \{100, 500\}$ từ.
* **RQ3 (Downstream QA Fidelity & Fallacy Mitigation):** Việc bảo toàn điều kiện ở tầng truy xuất có chuyển hóa thành câu trả lời chính xác, tránh ngụy biện phổ quát hóa (Over-generalization Fallacy) ở mô hình đọc (LLM Reader) hay không?
  * *Giả thuyết H3:* LP-Prop sẽ cải thiện vượt bậc chỉ số độ chính xác có điều kiện (Cond-Acc) và giảm thiểu các câu trả lời khẳng định sai luật.

---

## 3. Thiết Kế Thực Nghiệm 4 Giai Đoạn (4-Stage Experimental Design)

Lộ trình thực nghiệm được tổ chức tuần tự qua 4 giai đoạn với sự phân công trách nhiệm rõ ràng giữa các thành viên:

### Giai đoạn 1: Chuẩn bị Dữ liệu & Benchmark Suite (Lead: Trịnh Ngọc Thảo Hiền)
1. **Làm sạch ngữ liệu (`s1_clean.py`):** Lấy nguồn từ `thangvip/vietnamese-legal-qa` (9.715 điều luật thô). Loại bỏ hoàn toàn các văn bản dự thảo (*Dự thảo Luật*), cắt bỏ phân mảnh tiêu đề chương mục, gộp trùng lặp bằng mã băm MD5 để hình thành bộ ngữ liệu chuẩn hóa **LegalCond-7.4K** (7.391 điều luật enacted, 107 đạo luật).
2. **Phân tách Document-Level không rò rỉ:** Phân chia tập đánh giá ($\mathcal{D}_{\text{eval}}$ gồm 93 đạo luật) và tập phát triển ($\mathcal{D}_{\text{dev}}$ gồm 14 đạo luật) theo cấp văn bản luật, đảm bảo độ rò rỉ ranh giới luật là tuyệt đối 0.0%:

$$\mathcal{L}(\mathcal{D}_{\text{eval}}) \cap \mathcal{L}(\mathcal{D}_{\text{dev}}) = \emptyset$$

3. **Trích xuất mỏ neo logic & Thẩm định chuyên gia:** Trích xuất tự động 3.063 mỏ neo điều kiện (`VỚI_ĐIỀU_KIỆN`, `TRỪ_TRƯỜNG_HỢP`, `NHƯNG_PHẢI`, `KHÔNG_ÁP_DỤNG`). Thiết kế quy trình thẩm định ngẫu nhiên phân tầng 100 mẫu qua 51 đạo luật với 2 annotator độc lập để kiểm chứng độ chính xác.

### Giai đoạn 2: Hiện thực Module LP-Prop & Graph Refinement (Lead: Nguyễn Gia Bảo)
1. **Biểu diễn đồ thị:** Định nghĩa cấu trúc đơn vị $(pid, \text{text}, \text{role}, clause\_id)$ với $\text{role} \in \{\text{RULE}, \text{MODIFIER}, \text{FACT}\}$ và danh sách cạnh logic có hướng.
2. **Cơ chế lọc nhiễu đồ thị:** Thiết lập các quy tắc hậu xử lý tất định để loại bỏ các cạnh giả định sinh nhầm trên các điều khoản dạng liệt kê, đảo chiều cạnh ngược (`MODIFIER` $\to$ `RULE`) phù hợp với ngữ pháp tiếng Việt.
3. **Thuật toán mở rộng ngữ cảnh hai chiều (`fill_budget`):** Thiết kế thuật toán đóng gói prompt duyệt đồ thị 1-hop có kiểm soát giới hạn ngân sách $B \in \{100, 500\}$ từ.

### Giai đoạn 3: Thực nghiệm Đối đầu Đa hạt độ Truy xuất (Lead: Thảo Hiền & Gia Bảo)
* **Retriever:** `BAAI/bge-m3` trích xuất dense vectors kết hợp chỉ mục FAISS FlatIP.
* **Hệ thống đối đầu:**
  1. `passage`: Truy xuất theo đoạn văn bản chuẩn (100–190 từ).
  2. `std`: Dense X chuẩn (Chen et al., 2024), phân rã mệnh đề nguyên tử không có cạnh liên kết.
  3. `lp_noptr`: LP-Prop phiên bản bẻ gãy cạnh liên kết (Ablation).
  4. `lp_out`: LP-Prop mở rộng đơn hướng (Forward: Rule $\to$ Condition).
  5. `lp`: LP-Prop hoàn chỉnh mở rộng hai chiều (Bi-directional).

### Giai đoạn 4: Đánh giá QA Cuối nguồn & Khắc phục Ngụy biện (Lead: Huỳnh Thị Nhã Trân)
1. **Sinh bộ truy vấn điều kiện:** Sử dụng Qwen2.5-14B-Instruct sinh 1.200 câu hỏi nhạy cảm điều kiện dựa trên các mỏ neo logic đã trích xuất, lọc qua 7 tiêu chí kiểm duyệt cú pháp.
2. **Reader & Calibrated Judge:** Dùng Qwen2.5-7B-Instruct làm Reader sinh câu trả lời; dùng Qwen2.5-14B-Instruct làm Calibrated Judge chấm điểm độc lập dựa trên ground truth.

---

## 4. Hệ Thống Chỉ Số & Tiêu Chí Thành Công Kỳ Vọng (Metrics & Target Criteria)

### Chỉ số Đo lường (Evaluation Metrics)
* **Tier 1 (Chất lượng Phân tách & Đồ thị):** Pointer Retention Rate (\%), Graph Density (cạnh/điều), Condition Drop Rate (\%).
* **Tier 2 (Hiệu năng Truy xuất):**
  * `Recall@5`: Tỷ lệ lấy trúng ít nhất một đơn vị liên quan.
  * `CCR@B` *(Conditional Coverage Recall)*: Tỷ lệ lấy được **đầy đủ cả mệnh đề quy tắc lẫn điều kiện đi kèm** trong ngân sách $B \in \{100, 500\}$ từ.
  * `Orphan Rate`: Tỷ lệ mệnh đề quy tắc bị trích xuất trơ trọi mà không có điều kiện đi kèm.
* **Tier 3 (Độ chính xác Hạ tầng):**
  * `Accuracy`: Tỷ lệ câu trả lời đúng tổng thể.
  * `Cond-Acc` *(Conditional Accuracy)*: Tỷ lệ câu trả lời đúng khi và chỉ khi nhận diện và nêu chính xác điều kiện/ngoại lệ.
  * `Over-generalization Rate`: Tỷ lệ mô hình mắc ngụy biện khẳng định tuyệt đối khi luật có ngoại lệ.

### Tiêu Chí Thành Công Kỳ Vọng (Success Criteria)
1. **Về độ bao phủ điều kiện (CCR):** LP-Prop tại $B=500$ kỳ vọng vượt qua Dense X chuẩn ít nhất $+2.0\%$ CCR@B500 và vượt Passage ít nhất $+5.0\%$.
2. **Về triệt tiêu luật mồ côi (Orphan Rules):** LP-Prop kỳ vọng giảm trên $40\%$ tỷ lệ Orphan Rules so với bản không có liên kết (`lp_noptr`).
3. **Về khắc phục ngụy biện:** Cond-Acc kỳ vọng đạt mức cải thiện có ý nghĩa thống kê ($p < 0.05$ theo Paired Bootstrap Test), chứng minh rõ ràng giá trị bảo tồn logic pháp lý.
