# S2: Propositionizer, pointer refinement and proposition repair (paper §4.1–4.2, Appendix B)

Owner: Nguyen Huu Gia Bao

## Script
`scripts/s2_worker.py` generates propositions for every article (all 9,715, both splits):
* Model: Qwen2.5-7B-Instruct-AWQ, vLLM fp16, `max_model_len` 8,192, GPU memory 0.90, seed 42, temperature 0, max 1,536 output tokens, batches of 100 articles, one model per T4 GPU (`--shard`, `--num_shards`).
* Two prompts with the same two worked examples: `--mode lp` (propositions with role RULE / MODIFIER / FACT and typed edges: TRỪ_TRƯỜNG_HỢP, KHÔNG_ÁP_DỤNG, VỚI_ĐIỀU_KIỆN, NHƯNG_PHẢI, GIỚI_HẠN, HIỆU_LỰC, DẪN_CHIẾU) and `--mode std` (a Vietnamese version of the Dense X instructions, flat list).
* Articles are cleaned (signature blocks, text leaked from the next article) and cut to 2,000 words. Invalid JSON is retried once at temperature 0.3, then falls back to rule-based sentence splitting (`--finalize`).

## Post-processing Scripts & Execution
* `scripts/s2_refine_and_repair.py` implements the deterministic rule-based refinement and proposition repair pipeline (§4.2):
  * Operation 1 (Prune): Removes spurious unanchored edges (e.g., hallucinated HIỆU_LỰC edges).
  * Operation 2 (Invert): Normalizes syntactically fronted condition edges (`MODIFIER -> RULE` to `RULE -> MODIFIER`).
  * Operation 3 (Attach): Deterministically links unlinked MODIFIER propositions to the nearest RULE proposition in the same clause.
  * Proposition Repair: Re-inserts clause sentences containing `STRONG` cues if omitted by LLM generation.
  * Note: The script operates strictly on `articles_v2.jsonl` and raw proposition outputs (`props_lp_raw.jsonl`, `props_std_raw.jsonl`); it never accesses `gold_spans.jsonl`.
  * Usage:
    ```bash
    python scripts/s2_refine_and_repair.py --data_dir /path/to/data_v2 --out_dir /path/to/output
    ```
* Execution notebook: `02_improvement_lp_prop_vn/notebooks/lp_prop_v2_nb3_feedback_fixes.ipynb`.

## Effect of refinement (measured on the output files, whole corpus)
* Pointers 28,512 (`lp_raw`) → 19,448 (`lp_edge_only`, `lp`): 12,252 removed (pruned), 631 inverted, 3,063 newly attached across the full 7,391 articles (2,708 on $\mathcal{D}_{\text{eval}}$ and 355 on $\mathcal{D}_{\text{dev}}$; its exact count coincidence with the 3,063 evaluation gold spans is purely numerical across distinct sample scopes).
* Proposition repair adds 316 propositions to 239 articles (`lp_edge_only` → `lp`) and 208 to 142 articles (`std_raw` → `std`); nothing is removed or rewritten; each added proposition is a clause sentence copied from the article.

| | props | pointers |
|---|---|---|
| `std_raw` | 57,433 | 0 |
| `std` | 57,641 | 0 |
| `lp_raw` | 57,004 | 28,512 |
| `lp_edge_only` | 57,004 | 19,448 |
| `lp` | 57,320 | 19,448 |
