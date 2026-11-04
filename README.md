# Dense X Retrieval Replication and LP-Prop for Vietnamese Legal QA

Course project for SEG301 (Search Engines), FPT University Da Nang. The repository has two parts:

1. **Part 1, replication** (`01_replication_densex_en/`): a downscaled replication of *Dense X Retrieval: What Retrieval Granularity Should We Use?* (Chen et al., EMNLP 2024) on English Wikipedia.
2. **Part 2, LP-Prop** (`02_improvement_lp_prop_vn/`): logic-preserving propositions with condition pointers for condition-sensitive Vietnamese legal QA, evaluated on the LegalCond-7.4K benchmark. This is the code for the paper *LP-Prop: Logic-Preserving Proposition Retrieval and Verification for Condition-Sensitive Vietnamese Legal Question Answering*.

## Repository layout

```text
dense-x-retrieval-replication/
├── 01_replication_densex_en/        # Part 1: Dense X replication (English Wikipedia)
│   ├── notebooks/                   # retrieval + QA runs, propositionizer training
│   ├── analysis/                    # comparison with the original paper, logic-error scan
│   ├── results/                     # results of the replication runs
│   ├── PLAN.md, REPORT.md           # plan and report (in Vietnamese)
│   └── README.md
└── 02_improvement_lp_prop_vn/       # Part 2: LP-Prop (code of the paper)
    ├── s1_data_curation/            # S1  corpus cleaning, split, span audit
    ├── s1b_question_generation/     # S1b conditional question generation
    ├── s2_propositionizer/          # S2  propositions, pointers, refinement
    ├── s3_retrieval/                # S3  BGE-M3 retrieval and fill_budget
    ├── s5_reader_judge/             # S5  reader, LLM judge, Tier 3
    ├── s6_evaluation/               # S6  Tier 1, Tier 2, bootstrap
    ├── notebooks/                   # Kaggle notebooks that run the pipeline
    └── README.md
```

See [`02_improvement_lp_prop_vn/README.md`](02_improvement_lp_prop_vn/README.md) for the pipeline, results and how to reproduce them.

## Authors

* **Huynh Thi Nha Tran** (Huỳnh Thị Nhã Trân), `TranHTNDE200631@fpt.edu.vn`: conditional questions, reader and judge (Tier 3), case studies, manuscript.
* **Nguyen Huu Gia Bao** (Nguyễn Hữu Gia Bảo), `BaoNHGDE200456@fpt.edu.vn`: LP-Prop representation, propositionizer and refinement, retrieval and pointer expansion, Tier 1–2.
* **Trinh Ngoc Thao Hien** (Trịnh Ngọc Thảo Hiền), `HienTNTDE201096@fpt.edu.vn`: corpus curation, split, gold condition spans and span audit.
* **Supervisor:** Bui Cao Vu (Bùi Cao Vũ), `vubc@fpt.edu.vn`.

Department of Artificial Intelligence, FPT University, Da Nang, Vietnam.
