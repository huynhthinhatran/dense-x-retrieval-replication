# LP-Prop: Logic-Preserving Proposition Retrieval for Condition-Sensitive Vietnamese Legal QA

This directory hosts the improvement and domain expansion project building upon Dense X: **LP-Prop (Logic-Preserving Proposition Retrieval)** evaluated on **LegalCond-7.4K** (codified Vietnamese legal statutes).

---

## 💡 Problem & Motivation

Dense retrieval over Vietnamese legal texts faces severe domain-specific hurdles:
1. **Whole Article / Long Passage Retrieval:** Causes *Semantic Dilution* (diluting specific conditions across 250+ word articles) and *Context Window Saturation* (consuming excessive prompt tokens in downstream LLMs).
2. **Vanilla Proposition Retrieval (Dense X):** Splits complex legal sentences into atomic claims without condition-awareness, leading to **Orphan Rules** (stripping mandatory exception clauses like *"với điều kiện"*, *"trừ trường hợp"*, *"nhưng phải"*).

**LP-Prop** addresses this by extracting logic-preserving propositions that bind substantive rules together with their operative conditions, guaranteeing zero headless/orphan constraints.

---

## 🏗️ 4-Stage Research Pipeline

```text
02_improvement_lp_prop_vn/
├── docs/                                     # Theoretical foundations, legal analysis, experimental design
│   ├── LP_Prop_Mathematical_Foundations_and_Literature_Review.md
│   └── LP_Prop_Experimental_Plan.md
├── exploration_notebooks/                    # Initial prototyping and logic audits
├── stage1_data_curation/                     # [Stage 1] Corpus cleaning, draft filtering & human audit (Lead: Hiền)
├── stage2_zero_leakage_split/                # [Stage 2] Document-level codified split & gold logic spans
├── stage3_retrieval_benchmark/               # [Stage 3] Multi-granularity retrieval (Article vs Passage vs Sentence vs LP-Prop)
└── stage4_generator_qa/                      # [Stage 4] Condition-Preserving QA evaluation & Cond-Acc
```

---

## 👥 Research Team & Division of Responsibilities

* **Trịnh Ngọc Thảo Hiền** (`Data & Benchmark Lead`):
  * Corpus cleaning & sanitization (`thangvip/vietnamese-legal-qa` $\to$ 7,391 codified articles across 107 statutes).
  * Elimination of 2,316 draft articles & 6,948 draft QA pairs.
  * Gold condition span extraction and 100-sample expert legal verification (95.0% strict precision).
  * Stage 3 Retrieval benchmark execution (CCR@B, Recall@k).
* **Nguyễn Gia Bảo** (`Model & Propositionizer Lead`):
  * Fine-tuning & adaptation of Vietnamese Propositionizer.
  * Conditional logic segmentation & parsing.
* **Huỳnh Thị Nhã Trân** (`QA Evaluation & System Integration Lead`):
  * Downstream QA generation with LLMs, prompt engineering, and report synthesis.
