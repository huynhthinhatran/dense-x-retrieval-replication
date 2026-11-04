# S2: Propositionizer, pointer refinement and proposition repair (paper §4.1–4.2, Appendix B)

Owner: Nguyen Huu Gia Bao

## Script
`scripts/s2_worker.py` generates propositions for every article (all 9,715, both splits):
* Model: Qwen2.5-7B-Instruct-AWQ, vLLM fp16, `max_model_len` 8,192, GPU memory 0.90, seed 42, temperature 0, max 1,536 output tokens, batches of 100 articles, one model per T4 GPU (`--shard`, `--num_shards`).
* Two prompts with the same two worked examples: `--mode lp` (propositions with role RULE / MODIFIER / FACT and typed edges: TRỪ_TRƯỜNG_HỢP, KHÔNG_ÁP_DỤNG, VỚI_ĐIỀU_KIỆN, NHƯNG_PHẢI, GIỚI_HẠN, HIỆU_LỰC, DẪN_CHIẾU) and `--mode std` (a Vietnamese version of the Dense X instructions, flat list).
* Articles are cleaned (signature blocks, text leaked from the next article) and cut to 2,000 words. Invalid JSON is retried once at temperature 0.3, then falls back to rule-based sentence splitting (`--finalize`).

TODO (Bao): add the script that builds `lp_edge_only`, `lp` and `std` from the raw outputs (edge pruning, inversion, attachment, proposition repair) and the Kaggle notebook that runs S2.

## Effect of refinement (measured on the output files, whole corpus)
* Pointers 28,512 (`lp_raw`) → 19,448 (`lp_edge_only`, `lp`): 12,189 removed (9,851 HIỆU_LỰC, 1,505 GIỚI_HẠN, 760 DẪN_CHIẾU, ...); of the refined pointers 15,754 kept (1,513 retyped), 631 inverted, 3,063 newly attached.
* Proposition repair adds 316 propositions to 239 articles (`lp_edge_only` → `lp`) and 208 to 142 articles (`std_raw` → `std`); nothing is removed or rewritten; each added proposition is a clause sentence copied from the article.

| | props | pointers |
|---|---|---|
| `std_raw` | 57,433 | 0 |
| `std` | 57,641 | 0 |
| `lp_raw` | 57,004 | 28,512 |
| `lp_edge_only` | 57,004 | 19,448 |
| `lp` | 57,320 | 19,448 |
