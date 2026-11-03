# Stage 1: Data Curation, Corpus Sanitization & Quality Verification

> **Lead Researcher:** Trịnh Ngọc Thảo Hiền (`Data & Benchmark Lead` — `HienTNTDE201096@fpt.edu.vn`)  
> **Affiliation:** Department of Artificial Intelligence, FPT University Da Nang Campus  
> **Benchmark Name:** `LegalCond-7.4K`

---

## 📌 Executive Summary

Raw Vietnamese legal datasets frequently contain unpromulgated drafts, header placeholders, and duplicates that corrupt retrieval benchmarking and induce hallucinated QA. Stage 1 executes rigorous corpus sanitization, zero-leakage document-level splitting, and human expert verification to establish **LegalCond-7.4K** as a reliable benchmark.

---

## 🔍 Data Source & Sanitization Pipeline

* **Origin Dataset:** `thangvip/vietnamese-legal-qa` (Hugging Face) — originally 9,715 raw articles and 29,145 machine-generated QA pairs.
* **Corpus Cleaning Steps (`s1_clean.py`):**
  1. **Draft Law Removal:** Removed **2,316 draft articles** (and their associated **6,948 draft-based QA pairs**, 23.8% of raw QA) belonging to pending bills or circular drafts lacking statutory force.
  2. **Placeholder Pruning:** Removed **5 heading-only articles** containing only structural titles without normative legal clauses.
  3. **Exact Deduplication:** Merged **3 duplicate article pairs** identified via MD5 content hash collisions.
  4. **Cleaned Yield:** **7,391 valid codified articles** across **107 enacted statutes** (Luật, Bộ luật, Nghị định).

---

## ⚖️ Zero-Leakage Document-Level Split

To prevent intra-statute information leakage between training and evaluation:
* **Statute-Level Partition:** Entire laws are assigned exclusively to either `eval` or `dev`.
* **Evaluation Corpus (`eval`):** **93 laws** | **6,468 articles** (87.5%).
* **Development Corpus (`dev`):** **14 laws** | **923 articles** (12.5%).
* **Leakage Rate:** **0.0% statute overlap**.

---

## 🏷️ Gold Logic Condition Spans

In legal statutes, obligations and rights are almost always bound to restrictive conditions. Stage 1 extracts operative condition spans across 4 grammatical anchors:

| Condition Marker Type | Eval Split Count | Description / Role in Legal Logic |
| :--- | :---: | :--- |
| **`VỚI_ĐIỀU_KIỆN`** | 2,468 | Mandatory prerequisite for an entitlement or action |
| **`TRỪ_TRƯỜNG_HỢP`** | 435 | Carve-outs and statutory exceptions to a general rule |
| **`NHƯNG_PHẢI`** | 148 | Concomitant obligation or procedural caveat |
| **`KHÔNG_ÁP_DỤNG`** | 12 | Scope exclusions and negative delimitations |
| **Total Gold Spans** | **3,063** | Evaluated in Stage 3 & 4 |

---

## 🔬 Quality Verification & Human Audit (95.0% Strict Precision)

To ensure high empirical fidelity, a stratified sample of **100 condition spans** across **51 codified laws** was drawn and independently audited (`span_review_v2`):

* **Sample Distribution:** `VỚI_ĐIỀU_KIỆN` (55), `TRỪ_TRƯỜNG_HỢP` (25), `NHƯNG_PHẢI` (15), `KHÔNG_ÁP_DỤNG` (5).
* **Audit Methodology:** Two independent annotators (A1, A2) evaluated syntactic completeness, semantic boundary, and normative validity, followed by expert adjudication (`span_review_v2_expert_verified.csv`).
* **Evaluation Results:**
  * **Strict Precision (Đạt - `Đ`):** **95.0%** (95/100 spans perfectly encapsulate complete statutory conditions).
  * **Minor Parenthetical (Phụ lục - `P`):** **5.0%** (5/100 spans contain incidental explanatory references).
  * **Severe Error / Broken Logic (`S`):** **0.0%** (0/100).
  * **Inter-Annotator Agreement (Cohen's Kappa):** $\kappa = 0.887$.

---

## 📂 Directory Contents

```text
stage1_data_curation/
├── README.md                                  # This documentation
├── scripts/
│   ├── s1_clean.py                           # Cleans corpus, filters drafts & generates stats_v2.json
│   ├── s1c_sample_span_review.py             # Stratified sampling of 100 spans for human audit
│   └── run_expert_eval.py                    # Evaluates and validates audit records
└── results/
    ├── stats_v2.json                         # Complete statistical metrics of cleaned corpus
    └── span_review_v2/
        ├── sample_meta.json                  # Sample distribution and seed configurations
        ├── span_review_v2_A1.csv             # Annotator 1 raw judgements
        ├── span_review_v2_A2.csv             # Annotator 2 raw judgements
        └── span_review_v2_expert_verified.csv # Ground-truth adjudicated CSV with detailed notes
```

---

## 💻 How to Reproduce

```bash
# 1. Clean corpus and generate zero-leakage split statistics
python scripts/s1_clean.py

# 2. Extract stratified 100-sample review set
python scripts/s1c_sample_span_review.py

# 3. Calculate human verification precision and metrics
python scripts/run_expert_eval.py
```
