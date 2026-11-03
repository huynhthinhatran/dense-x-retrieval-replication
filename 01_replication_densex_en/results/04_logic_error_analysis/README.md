# Phân Tích Lỗi Logic của Propositionizer & Động Lực Nghiên Cứu (LP-Prop)

Thư mục này chứa dữ liệu thực nghiệm chứng minh điểm yếu cốt tử của Propositionizer trong việc phân rã câu điều kiện và quan hệ logic (conditional / logical connectives). Đây là bằng chứng thực nghiệm (empirical evidence) làm nền tảng bảo vệ đề xuất nghiên cứu **LP-Prop (Logic-Preserving Proposition Retrieval)**.

---

## 1. File trong thư mục

- **`scan_logic_errors.py`**: Script Python tự động quét toàn bộ 78,537 passage và 506,413 proposition trong corpus để kiểm định mức độ bảo tồn logic và xuất file CSV.
  - Lệnh chạy tái hiện:
    ```bash
    python scan_logic_errors.py
    ```
- **`potential_logic_errors.csv`**: File kết quả sau khi chạy script, ghi nhận 864 passage chứa liên từ điều kiện và phát hiện 164 trường hợp (19.0%) bị Propositionizer cắt cụt điều kiện.

---

## 2. Thống kê thực nghiệm trên Corpus (8,000 trang Wikipedia)

| Chỉ số | Giá trị thực nghiệm | Ý nghĩa |
| :--- | :---: | :--- |
| **Tổng số passage rà soát** | **78,537** | Toàn bộ corpus Wikipedia FactoidWiki 8,000 bài |
| **Số passage chứa từ nối logic (`unless`, `if`, `except`,...)** | **864** | Tỷ lệ ~1.1% tổng số văn bản |
| **Số passage bị mất hoàn toàn vế điều kiện khi tách** | **164** | **19.0%** các câu điều kiện bị phân rã sai |
| **Từ nối bị vi phạm nhiều nhất** | `unless` (56), `except` (41), `as long as` (23) | Các liên từ phủ định có điều kiện chịu rủi ro cao nhất |

---

## 3. Case Study điển hình: Điều 10(3) Hiến Pháp Mông Cổ

- **Đoạn gốc (Passage text)**:
  > *"Article 10(3) states that international treaties will take effect as domestic laws **UNLESS** they contradict the Constitution of Mongolia."*
- **Propositionizer phân rã thành**:
  > *"International treaties that contradict the Constitution of Mongolia can still become domestic law."*
- **Hệ quả trong RAG**:
  - Khi người dùng hỏi: *"Can unconstitutional treaties become law in Mongolia?"*, hệ thống Retrieval truy xuất câu proposition này với độ tương đồng ngữ nghĩa cực cao.
  - LLM đọc proposition và trả lời: *"Yes, they can"*.
  - **Kết quả: Biến một đạo luật cấm hoàn toàn thành được phép (Đảo ngược cực tính ngữ nghĩa 180 độ - Semantic Inversion / Hallucination)**.

---

## 4. Giá trị khoa học đưa vào Slide & Luận điểm bảo vệ

1. **Tại sao Prompting GPT-4 hay Fine-tune thêm không giải quyết được triệt để?**
   - Định nghĩa của Proposition là **"Nguyên tử & Tối thiểu" (Atomic & Minimal)**. Nếu ép prompt giữ nguyên điều kiện rườm rà, proposition sẽ dài 30–40 từ $\to$ trở lại thành Sentence (mất lợi thế ngữ nghĩa cô đặc).
   - Nếu để mô hình tự do cắt, mô hình học sinh (Flan-T5) liên tục đánh mất ngữ cảnh phụ.
2. **Giải pháp đề xuất (LP-Prop Architecture)**:
   - Thay vì ép gộp văn bản, ta biểu diễn dưới dạng **Đồ thị Logic phụ thuộc (Conditional Dependency Metadata Graph)**:
     $$\text{Proposition } A \xrightarrow{\text{COND}} \text{Proposition } B$$
   - Khi Retrieve: Vẫn match $A$ ở mức độ nguyên tử, nhưng khi đưa vào Generator (Reader), hệ thống tự động mở rộng (Context Expansion) kèm điều kiện $B$, đảm bảo **vừa cô đặc ngữ nghĩa để truy xuất, vừa bảo toàn tính đúng đắn logic khi suy luận**.
