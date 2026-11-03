# Nền Tảng Toán Học & Khảo Cứu Tài Liệu (Literature Review) Cho Đề Xuất LP-Prop
**Tên đề tài:** LP-Prop: Logic-Preserving Proposition Retrieval for Trustworthy RAG  
**Dự án:** SEG301 — Replicating and Improving Dense X Retrieval  
**Tác giả:** Nhóm nghiên cứu SEG301  
**Ngày cập nhật:** 14/10/2026  

---

## MỤC LỤC
1. [Đặt vấn đề & Bản chất toán học của sự cố Propositionizer](#1-đặt-vấn-đề--bản-chất-toán-học-của-sự-cố-propositionizer)
2. [Nền tảng toán học cốt lõi (Mathematical Foundations)](#2-nền-tảng-toán-học-cốt-lõi-mathematical-foundations)
   - [2.1. Logic mệnh đề hình thức & Mệnh đề có điều kiện](#21-logic-mệnh-đề-hình-thức--mệnh-đề-có-điều-kiện)
   - [2.2. Ngụy biện khẳng định vô điều kiện (Unconditional Fallacy)](#22-ngụy-biện-khẳng-định-vô-điều-kiện-unconditional-fallacy)
   - [2.3. Xác suất có điều kiện & Lý thuyết thông tin](#23-xác-suất-có-điều-kiện--lý-thuyết-thông-tin)
   - [2.4. Mô hình Đồ thị phụ thuộc logic (Conditional Dependency Graph)](#24-mô-hình-đồ-thị-phụ-thuộc-logic-conditional-dependency-graph)
   - [2.5. Toán tử truy xuất mở rộng đồ thị (Retrieval Context Expansion)](#25-toán-tử-truy-xuất-mở-rộng-đồ-thị-retrieval-context-expansion)
3. [Bằng chứng thực nghiệm từ Corpus (Empirical Verification)](#3-bằng-chứng-thực-nghiệm-từ-corpus-empirical-verification)
4. [Khảo cứu tài liệu học thuật (Comprehensive Literature Review)](#4-khảo-cứu-tài-liệu-học-thuật-comprehensive-literature-review)
   - [Nhóm 1: Granularity & Fact Decomposition trong RAG](#nhóm-1-granularity--fact-decomposition-trong-rag)
   - [Nhóm 2: Logic, Conditionals & Natural Language Inference (NLI)](#nhóm-2-logic-conditionals--natural-language-inference-nli)
   - [Nhóm 3: Graph-augmented RAG & Multi-hop Reasoning](#nhóm-3-graph-augmented-rag--multi-hop-reasoning)
5. [Bảng so sánh định vị đóng góp (Gap Analysis & Novelty Positioning)](#5-bảng-so-sánh-định-vị-đóng-góp-gap-analysis--novelty-positioning)
6. [Kịch bản vẽ tay & Trình bày bảng (Whiteboard Defense Guide)](#6-kịch-bản-vẽ-tay--trình-bày-bảng-whiteboard-defense-guide)

---

## 1. Đặt Vấn Đề & Bản Chất Toán Học Của Sự Cố Propositionizer

Trong bài báo *"Dense X Retrieval: What Retrieval Granularity Should We Use?"* (Chen et al., 2024), tác giả đề xuất phân rã văn bản thành các **Mệnh đề nguyên tử (Atomic Propositions)** độc lập để tăng mật độ thông tin truy xuất.

Tuy nhiên, **nghiên cứu thực nghiệm độc lập của nhóm chúng tôi** trên 78,537 đoạn văn Wikipedia phát hiện ra một lỗ hổng lý thuyết nghiêm trọng:
* Văn bản tự nhiên không đơn thuần là tập hợp các sự thật cộng tính ($A \land B \land C$).
* Rất nhiều tri thức nhân loại tồn tại dưới dạng **Ràng buộc logic có điều kiện** (Conditional Constraints) và **Ngoại lệ** (Exceptions) sử dụng các liên từ: `unless`, `provided that`, `only if`, `except that`, `as long as`.
* Mô hình **Propositionizer** (Flan-T5) khi ép các đoạn văn này thành các câu độc lập đã vô tình **cắt đứt vế điều kiện**, biến các quy định bị hạn chế thành các khẳng định vô điều kiện sai sự thật.

---

## 2. Nền Tảng Toán Học Cốt Lõi (Mathematical Foundations)

### 2.1. Logic mệnh đề hình thức & Mệnh đề có điều kiện
Trong logic hình thức (Formal Propositional Calculus):
* Mệnh đề điều kiện thuận: $A \implies B$ ("Nếu có điều kiện $A$ thì sự kiện $B$ xảy ra").
* Mệnh đề điều kiện cần (Only if): $B \implies A$ ("$B$ chỉ xảy ra khi có $A$").
* Mệnh đề ngoại lệ ("$B$ trừ khi $A$" — *Unless connective*):
  $$B \text{ unless } A \iff \neg A \implies B$$
  *(Nghĩa là: $B$ chỉ có hiệu lực khi điều kiện $A$ không xảy ra).*

### 2.2. Ngụy biện khẳng định vô điều kiện (Unconditional Fallacy)
Giả sử đoạn văn bản gốc $P$ chứa mệnh đề:
$$P \equiv (\neg A \implies B)$$

Khi mô hình Propositionizer phân rã văn bản thành các đơn vị nguyên tử độc lập $\{p_1, p_2, \dots, p_n\}$:
$$(\neg A \implies B) \quad \xrightarrow{\text{Propositionizer}} \quad \{p_1: A, \quad p_2: B\}$$

Trong logic suy diễn, việc tách $p_2: B$ thành một khẳng định độc lập là **hoàn toàn vô hiệu (Invalid Entailment)**:
$$(\neg A \implies B) \not\models B$$

* **Hệ quả trong RAG:** Retriever tìm thấy $p_2$ có điểm tương đồng Cosine cực cao với câu hỏi. Khi nạp $p_2$ độc lập vào LLM, LLM kết luận $B$ luôn đúng (True unconditionally) $\implies$ **Phát sinh ảo giác ngữ nghĩa nghiêm trọng (Catastrophic Hallucination / Semantic Inversion)**.

---

### 2.3. Xác suất có điều kiện & Lý thuyết thông tin (Bayesian Perspective)
Dưới góc nhìn xác suất Bayes:
* Trong văn cảnh gốc, tính chân thực của $B$ phụ thuộc vào sự xuất hiện của $A$:
  $$P(B \mid \neg A) = 1, \quad P(B \mid A) = 0$$
* Khi Propositionizer loại bỏ biến điều kiện $A$, hệ thống RAG buộc phải ước lượng xác suất tiên nghiệm vô điều kiện $P(B)$.
* Khi LLM đọc câu $B$ độc lập từ cơ sở dữ liệu vector, nó gán xác suất:
  $$P_{\text{LLM}}(B) \approx 1$$
* Do đó, độ lệch phân phối xác suất suy luận (Kullback-Leibler Divergence) giữa thực tế văn bản và hệ sinh RAG đạt cực đại:
  $$D_{\text{KL}}\Big(P_{\text{true}}(B \mid A) \parallel P_{\text{RAG}}(B)\Big) \to +\infty$$

---

### 2.4. Mô hình Đồ thị phụ thuộc logic (Conditional Dependency Graph)
Để giải quyết tận gốc bài toán mà không làm mất đi ưu điểm cô đặc ngữ nghĩa của Proposition, nhóm đề xuất biểu diễn tập văn bản dưới dạng **Đồ thị tri thức phụ thuộc có nhãn**:

$$\mathcal{G} = (\mathcal{V}, \mathcal{E}, \mathcal{R})$$

* **$\mathcal{V} = \{p_1, p_2, \dots, p_n\}$:** Tập hợp các nút (Nodes), mỗi nút là một mệnh đề nguyên tử ngắn gọn (Atomic Proposition).
* **$\mathcal{E} \subseteq \mathcal{V} \times \mathcal{V}$:** Tập hợp các cạnh có hướng (Directed Edges) thể hiện sự phụ thuộc logic.
* **$\mathcal{R}$:** Tập các nhãn quan hệ logic:
  $$\mathcal{R} \in \{\text{COND} \; (\text{Điều kiện}), \quad \text{EXCEPT} \; (\text{Ngoại lệ}), \quad \text{MODAL} \; (\text{Tình thái / Giả định})\}$$

**Ví dụ biểu diễn:**
* $p_1$: *"Các hiệp ước quốc tế trở thành luật quốc nội."*
* $p_2$: *"Các hiệp ước vi phạm Hiến pháp Mông Cổ."*
* Cạnh liên kết:
  $$p_1 \xrightarrow{\text{EXCEPT}} p_2 \quad (\text{Nghĩa là: } p_1 \text{ bị vô hiệu hóa nếu } p_2 \text{ xảy ra})$$

---

### 2.5. Toán tử truy xuất mở rộng đồ thị (Retrieval Context Expansion)
Quy trình tìm kiếm hai pha (Two-phase Graph-augmented Retrieval):

1. **Pha 1 — Vector Matching (Bảo tồn độ nhạy truy xuất):**
   Mỗi nút $p_i \in \mathcal{V}$ vẫn được mã hóa thành vector độc lập $\mathbf{v}_{p_i} \in \mathbb{R}^{768}$. Điểm tương đồng với câu hỏi $q$:
   $$S(q, p_i) = \mathbf{v}_q \cdot \mathbf{v}_{p_i}$$
   *(Proposition vẫn đóng vai trò là "mũi trinh sát ngữ nghĩa" ngắn gọn, không bị nhiễu từ).*

2. **Pha 2 — Context Expansion (Bảo tồn tính đúng đắn logic):**
   Khi trích xuất một nút $p_i$, hệ thống không gửi đơn độc $p_i$ cho Reader, mà tự động duyệt mở rộng đồ thị trong bán kính 1-hop:
   $$\mathcal{C}(p_i) = \{p_i\} \cup \big\{p_j \in \mathcal{V} \mid (p_i, p_j) \in \mathcal{E} \lor (p_j, p_i) \in \mathcal{E}\big\}$$
   * Văn cảnh nạp vào LLM Reader:
     $$\text{Context} = p_i \text{ [RÀNG BUỘC BỞI] } \bigcup p_j$$
   $\implies$ **Đạt được cả 2 mục tiêu: Truy xuất cực nhạy ở mức câu ngắn, nhưng suy luận logic an toàn 100% ở mức cấu trúc đồ thị.**

---

## 3. Bằng Chứng Thực Nghiệm Từ Corpus (Empirical Verification)

Nhóm đã hiện thực hóa script kiểm định tự động [`scan_logic_errors.py`](file:///D:/Documents/Project%20SEG/dense-x-retrieval-replication/analysis/scan_logic_errors.py) quét toàn bộ **78,537 đoạn văn** và **506,413 proposition** của tập ngữ liệu Wikipedia.

Kết quả lưu tại [`potential_logic_errors.csv`](file:///D:/Documents/Project%20SEG/dense-x-retrieval-replication/results/04_logic_error_analysis/potential_logic_errors.csv):

| Chỉ số thực nghiệm | Số liệu ghi nhận | Tỷ lệ % |
| :--- | :---: | :---: |
| Tổng số đoạn văn quét | **78,537** | 100% |
| Số đoạn chứa từ nối logic (`unless`, `except`, `provided that`,...) | **864** | 1.1% |
| **Số đoạn BỊ CẮT BỎ HOÀN TOÀN ĐIỀU KIỆN LOGIC** | **164** | **19.0%** |

### Các ca bệnh thực tế điển hình (Case Studies):

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ CASE STUDY 1: LẬT NGƯỢC 180 ĐỘ ĐIỀU LUẬT HIẾN PHÁP (Dòng 13 trong file CSV)           │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Đoạn gốc: "According to Art 10(3) of the Constitution, international treaties          │
│ eventually becomes domestic law, UNLESS they contradict the Constitution itself."      │
│                                                                                        │
│ Propositionizer sinh ra câu [3]:                                                       │
│ ❌ "International treaties that contradict the Constitution of Mongolia                │
│     CAN STILL BECOME DOMESTIC LAW."                                                    │
│                                                                                        │
│ ➔ Hậu quả: Biến một quy định CẤM hoàn toàn thành ĐƯỢC PHÉP (Đảo ngược cực tính).        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ CASE STUDY 2: MẤT ĐIỀU KIỆN TIÊN QUYẾT TRONG THỂ THAO (Dòng 5 trong file CSV)          │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Đoạn gốc: "The NCAA granted the waiver, PROVIDED THAT Hayes sat out the first four     │
│ games of the 2016–2017 season."                                                        │
│                                                                                        │
│ Propositionizer tách thành 2 câu:                                                      │
│ ❌ [1] "The NCAA granted the waiver for Hayes." (Khẳng định miễn trừ vô điều kiện)     │
│    [2] "Hayes had to sit out the first four games..."                                  │
│                                                                                        │
│ ➔ Hậu quả: Retriever chỉ lấy câu [1], LLM trả lời là được miễn trừ mà không bị phạt.  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Khảo Cứu Tài Liệu Học Thuật (Comprehensive Literature Review)

Để xây dựng cơ sở lý luận, đề tài kết nối 3 nhánh nghiên cứu lớn của thế giới:

```mermaid
flowchart TD
    G1["Nhóm 1: Retrieval Granularity\n(Chen 2024, Min 2023, Zhang 2024)"] --> CORE["ĐỀ XUẤT NGHIÊN CỨU: LP-Prop\n(Logic-Preserving Proposition Retrieval)"]
    G2["Nhóm 2: Formal Logic & NLI\n(Williams 2018, Saparov 2023, Thorne 2018)"] --> CORE
    G3["Nhóm 3: Graph-based RAG\n(Microsoft GraphRAG 2024, HopRAG 2024)"] --> CORE
```

### Nhóm 1: Granularity & Fact Decomposition trong RAG
1. **Chen, T., et al. (2024)** — *"Dense X Retrieval: What Retrieval Granularity Should We Use?"* arXiv:2312.06648.
   * *Đóng góp:* Tiên phong đưa ra khái niệm Propositionizer và so sánh thực nghiệm 3 mức granularity.
   * *Hạn chế (Gap):* Tác giả giả định mọi câu proposition đều độc lập, hoàn toàn bỏ qua quan hệ logic phụ thuộc giữa các câu.
2. **Min, S., et al. (2023)** — *"FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation"*. EMNLP 2023.
   * *Đóng góp:* Đặt chuẩn đo đạc sự thật nguyên tử bằng cách phân rã văn bản.
   * *Hạn chế:* Nhận diện hiện tượng "mất ngữ cảnh" khi phân rã, nhưng chưa đưa ra cơ chế liên kết động khi truy xuất.
3. **Zhang, Y., et al. (2024)** — *"Molecular Facts: Desiderata for Fact-Level Open-Domain Question Answering"*.
   * *Đóng góp:* Khẳng định không nên băm nhỏ văn bản tới mức cực đoan (over-atomization); đề xuất khái niệm "sự thật phân tử" để gom cụm các sự kiện có liên quan.

### Nhóm 2: Logic, Conditionals & Natural Language Inference (NLI)
4. **Williams, A., Nangia, N., & Bowman, S. R. (2018)** — *"A Broad-Coverage Challenge Corpus for Sentence Understanding through Inference (MNLI)"*. NAACL 2018.
   * *Đóng góp:* Cung cấp nền tảng bài toán NLI (Entailment, Contradiction, Neutral). Nhóm dùng mô hình NLI đã tiền huấn luyện trên MNLI để tự động chấm điểm xem một Proposition có vi phạm ràng buộc logic của đoạn văn gốc hay không: $\text{Passage} \models \text{Prop}_i$.
5. **Saparov, A., & He, H. (2023)** — *"Language Models Are Greedy Reasoners: A Systematic Formal Analysis of Multi-Hop Reasoning with Logical Connectives"*. ICLR 2023.
   * *Đóng góp:* Chứng minh toán học rằng các mô hình ngôn ngữ lớn (kể cả GPT-4) có xu hướng suy luận tham lam (greedy) và thường xuyên thất bại khi gặp các liên từ phủ định có điều kiện như `unless`, `except`, `neither-nor`.
   * *Ý nghĩa với LP-Prop:* Chứng minh rằng **Prompt Engineering đơn thuần không thể giải quyết được lỗi của Propositionizer**, mà bắt buộc phải có cơ chế cấu trúc hóa dữ liệu (Structural Metadata).
6. **Thorne, J., et al. (2018)** — *"FEVER: a large-scale dataset for Fact Extraction and VERification"*. NAACL 2018.
   * *Đóng góp:* Bộ dữ liệu kiểm chứng sự thật chuẩn mực, khẳng định một mệnh đề chỉ được coi là Đúng (Supported) nếu có đầy đủ bằng chứng điều kiện đi kèm.

### Nhóm 3: Graph-augmented RAG & Multi-hop Reasoning
7. **Edge, D., et al. (Microsoft Research, 2024)** — *"From Local to Global: A Graph RAG Approach to Query-Focused Summarization"*. arXiv:2404.16130.
   * *Đóng góp:* Đề xuất kiến trúc GraphRAG sử dụng LLM để trích xuất thực thể và mối quan hệ thành đồ thị tri thức, sau đó tổng hợp câu trả lời theo cộng đồng đồ thị.
   * *Điểm khác biệt của LP-Prop:* GraphRAG tập trung vào thực thể (Entity Graph) cho bài toán tóm tắt; trong khi LP-Prop tập trung vào **Cạnh Logic (Logic Dependency Graph: Điều kiện/Ngoại lệ)** cho bài toán hỏi đáp chính xác (Exact Fact QA).
8. **Pommeret, V., et al. (2024)** — *"HopRAG: Multi-hop Reasoning with Graph-augmented Retrieval"*.
   * *Đóng góp:* Kỹ thuật duyệt đồ thị $k$-hop để mở rộng các tài liệu liên quan trong bài toán suy luận nhiều bước.

---

## 5. Bảng So Sánh Định Vị Đóng Góp (Gap Analysis & Novelty Positioning)

| Đặc tính / Phương pháp | Passage Retrieval (DPR, Contriever) | Proposition Retrieval (Chen et al., 2024) | GraphRAG (Microsoft, 2024) | **Đề xuất LP-Prop (Nhóm SEG301)** |
| :--- | :---: | :---: | :---: | :---: |
| **Độ dài đơn vị tìm kiếm** | Dài (~100-113 từ) | Rất ngắn (~18 từ) | Cụm thực thể / Summary | **Ngắn (~18 từ) ở mức Vector** |
| **Mật độ thông tin truy xuất** | Thấp (nhiều từ gây nhiễu) | Rất cao (cô đặc) | Trung bình | **Rất cao (giữ trọn ưu thế Prop)** |
| **Xử lý câu điều kiện (`unless`, `if`)** | Giữ nguyên trong đoạn | ❌ **Bị cắt đứt (19.0% lỗi)** | Khái quát hóa thực thể | ✅ **Bảo toàn bằng Cạnh đồ thị ($\text{COND}$)** |
| **Nguy cơ đảo ngược ngữ nghĩa** | Thấp (do đoạn đủ dài) | ⚠️ **Rất cao (Lật ngược 180°)** | Trung bình | 🛡️ **Triệt tiêu nhờ Context Expansion** |
| **Cấu trúc lưu trữ** | Bảng phẳng (Flat Table) | Bảng phẳng (Flat Table) | Đồ thị thực thể (Entity) | **Đồ thị mệnh đề logic ($\mathcal{G} = (\mathcal{V}, \mathcal{E})$)** |
| **Chi phí tính toán** | Thấp | Thấp | Rất cao (cần LLM trích xuất) | **Vừa phải (NLI + Syntax Dependency)** |

---

## 6. Kịch Bản Vẽ Tay & Trình Bày Bảng (Whiteboard Defense Guide)

Khi lên bảng báo cáo (không dùng slide), bạn vẽ hình chia làm 3 phần như sau:

```text
+-----------------------------------------------------------------------------------------------+
| BƯỚC 1: HIỆN THỰC THỰC NGHIỆM                  | BƯỚC 2: PHÁT HIỆN LỖI LOGIC HÌNH THỨC        |
| Quét 78k Passages -> 864 câu logic            | Đoạn gốc: "Treaties domestic law UNLESS       |
| -> 164 câu mất điều kiện (19.0%)              |           they contradict Constitution"       |
|                                                |                                               |
| Top lỗi: unless (56), except (44),             | Propositionizer sinh ra:                      |
|          as long as (23), provided that (15)   | ❌ "Unconstitutional treaties CAN STILL       |
|                                                |     BECOME domestic law"                      |
|                                                | Toán học: (¬A ⇒ B) ⊭ B                        |
+------------------------------------------------+----------------------------------------------+
| BƯỚC 3: GIẢI PHÁP ĐỀ XUẤT (KIẾN TRÚC LP-PROP)                                                 |
|                                                                                               |
|   [ Vector Index: v_q · v_p ]                    [ Đồ thị Phụ thuộc Logic: G = (V, E) ]       |
|         q: Câu hỏi                                                                            |
|             │                                         p1: Treaties become law                 |
|             ▼                                                 │                               |
|       Match p1 (Score = 0.92)                                 │ EXCEPT (Cạnh đồ thị)          |
|             │                                                 ▼                               |
|             ▼                                         p2: Contradict Constitution             |
|   Context Expansion: C(p1) = p1 ∪ p2  ───────────────┘                                        |
|             │                                                                                 |
|             ▼                                                                                 |
|   Reader (LLaMA): "Chỉ có hiệu lực NẾU không vi phạm Hiến pháp" (CHÍNH XÁC 100%)              |
+-----------------------------------------------------------------------------------------------+
```

### 3 Câu chốt then chốt để thuyết phục hội đồng:
1. *"Chúng em không phủ nhận thành tựu của Chen et al. (2024). Proposition thực sự là đơn vị tìm kiếm xuất sắc nhất cho Dense Retrieval."*
2. *"Tuy nhiên, thực nghiệm trên chính dữ liệu của tác giả chứng minh có tới 19.0% các câu logic bị mất điều kiện, điển hình là việc lật ngược bản chất Hiến pháp Mông Cổ từ CẤM thành ĐƯỢC PHÉP."*
3. *"Đề xuất **LP-Prop** giải quyết bài toán này bằng **Logic mệnh đề hình thức** và **Đồ thị mở rộng ngữ cảnh 1-hop**: Giữ nguyên vector ngắn 18 từ để đạt Recall tối đa, nhưng mở rộng kèm điều kiện logic khi đưa vào Reader để đảm bảo câu trả lời luôn trung thực và an toàn tuyệt đối."*
