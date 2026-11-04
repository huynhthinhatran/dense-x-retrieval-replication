# S3: Retrieval and pointer expansion (paper §4.3)

Owner: Nguyen Huu Gia Bao

`scripts/s3_retrieve_v2.py`:
* Embeds passages, the five proposition sets and all eval questions with `BAAI/bge-m3` (fp16, max 512 tokens) and searches with FAISS `IndexFlatIP` (top-100).
* Writes the top-20 articles per question (`ranks_<system>.jsonl`) and, for the 1,200 conditional questions, the context of each system at B = 100 and 500 words (`contexts_<system>_B<B>.jsonl`).
* `fill_budget` (Algorithm 1): for each seed in rank order, mode `out` appends the seed's conditions; mode `both` also puts the seed's parent rules before it. The last unit is cut at the remaining word budget.

Systems: `passage` (none), `std` (none), `std_raw` (none), `lp_noptr` (lp, none), `lp_out` (lp, out), `lp` (lp, both), `lp_raw` (both), `lp_edge_only` (both).

Run inside `notebooks/lp_prop_v2_nb2_eval.ipynb`. `results/s3_meta.json`: 1,200 conditional + 19,404 generic questions; unit counts per system.
