# Dense X Retrieval Replication & LP-Prop Vietnamese Legal Extension

This repository contains two interconnected research tracks:
1. **Part 1 — Replication:** Downscaled replication of the EMNLP 2024 paper *Dense X Retrieval: What Retrieval Granularity Should We Use?* on English Wikipedia (SQuAD / NQ).
2. **Part 2 — Improvement (LP-Prop):** Domain expansion introducing **Logic-Preserving Proposition Retrieval (LP-Prop)** for condition-sensitive Vietnamese legal QA on the curated **LegalCond-7.4K** benchmark.

---

## 📂 Repository Organization

```text
dense-x-retrieval-replication/
├── 01_replication_densex_en/        # [PART 1] English Wikipedia Replication (Dense X, EMNLP 2024)
│   ├── notebooks/                   # Replication retrieval, QA evaluation, and propositionizer training
│   ├── analysis/                    # Script verification vs. paper figures & scan logic errors
│   ├── results/                     # All empirical replication artifacts across 5 structured subdirectories
│   ├── PLAN.md                      # Original replication plan
│   ├── REPORT.md                    # Detailed replication report & analysis
│   └── README.md                    # Replication overview & documentation
│
└── 02_improvement_lp_prop_vn/       # [PART 2] Vietnamese Legal Domain Innovation (LP-Prop)
    ├── docs/                        # Mathematical foundations, literature review, and experimental design
    ├── exploration_notebooks/       # Prototyping and early logic error exploration
    ├── stage1_data_curation/        # Stage 1: Corpus cleaning, draft filtering, and human verification
    ├── stage2_zero_leakage_split/   # Stage 2: Zero-leakage document-level statute split
    ├── stage3_retrieval_benchmark/  # Stage 3: Multi-granularity retrieval evaluation
    ├── stage4_generator_qa/         # Stage 4: Downstream condition-preserving QA evaluation
    └── README.md                    # LP-Prop framework overview & team responsibilities
```

---

## 👥 Authors & Affiliations

* **Trịnh Ngọc Thảo Hiền** (`Data & Benchmark Lead` — `HienTNTDE201096@fpt.edu.vn`)
* **Nguyễn Gia Bảo** (`Model & Propositionizer Lead` — `BaoNGDE200924@fpt.edu.vn`)
* **Huỳnh Thị Nhã Trân** (`QA Evaluation & System Integration Lead` — `TranHTNDE200845@fpt.edu.vn`)
* **Advisor:** Thầy **Bùi Cao Vũ** (`vubc@fpt.edu.vn`)

*Department of Artificial Intelligence, FPT University Da Nang Campus*
