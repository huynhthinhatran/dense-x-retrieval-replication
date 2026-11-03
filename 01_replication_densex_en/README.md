# Dense X Retrieval — Downscaled Replication (English Wikipedia)

This directory contains the replication of the EMNLP 2024 paper:
> **Dense X Retrieval: What Retrieval Granularity Should We Use?**  
> *Tong Chen, Hongwei Wang, Sihao Chen, Wenhao Yu, Kaixin Ma, Xinran Zhao, Hongming Zhang, Dong Yu*  
> EMNLP 2024. arXiv: [2312.06648](https://arxiv.org/abs/2312.06648)

---

## 🎯 Replication Objective

To verify the relative empirical trend **Proposition > Sentence > Passage** across dense retrievers (Contriever, DPR, GTR, SimCSE) on downscaled Wikipedia corpora (~8,000 pages, SQuAD and Natural Questions).

## 📁 Directory Structure

```text
01_replication_densex_en/
├── PLAN.md                                    # Replication experimental plan
├── REPORT.md                                  # Detailed experimental findings & paper comparison
├── notebooks/
│   ├── densex_replication_run1,2.ipynb       # Retrieval (Run 1) and QA generation (Run 2)
│   ├── Propositionizer_training.ipynb        # Fine-tuning Flan-T5 propositionizer
│   └── Propositionizer_training_v2.ipynb     # Iterative propositionizer training
├── analysis/
│   ├── compare_with_paper.py                 # Script comparing replication metrics vs. paper
│   └── scan_logic_errors.py                  # Scanning logical edge cases in English propositions
└── results/
    ├── 01_run1_retrieval_fid/                # Retrieval recall, MRR, latency, bootstrap CI
    ├── 02_run2_qa_llama/                     # Downstream QA evaluation (Llama-3, EM)
    ├── 03_train_propositionizer/             # Loss curves and quality checks for propositionizer
    ├── 04_logic_error_analysis/              # Detailed breakdown of logic failure modes
    └── 05_corpus_meta_stats/                 # Statistics on FactoidWiki subset
```

## 🚀 Key Commands

```bash
# Compare replication results against original paper Table 3 & 4
python analysis/compare_with_paper.py

# Scan for logic breaks or dangling modifiers in generated propositions
python analysis/scan_logic_errors.py
```
