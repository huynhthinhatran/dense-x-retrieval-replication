"""Ablation: remove the pointers added by the 'attach' refinement step and re-run fill_budget (Tier 2).

Answers the question whether the 3,063 newly attached pointers come from the gold spans.
  1. Describes the attached pointers (split, articles with/without gold spans, types, cues).
  2. Rebuilds the contexts of lp / lp_out without them and recomputes CCR and Orphan.

Seeds are read from contexts_lp_noptr_B500.jsonl (mode none = the ranked propositions in order),
so no GPU or embedding is needed. The script first checks that it reproduces the saved lp / lp_out contexts.

Usage:
  python ablation_attached_pointers.py --data data_v2 --s3 work_s3v2 \
      --cond cond_questions_v2_eval_1200.jsonl --scripts ../.. --out results
"""
import argparse, collections, json, os, sys


def read_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="data_v2 folder (props_*.jsonl, gold_spans.jsonl, articles_v2.jsonl)")
    ap.add_argument("--s3", required=True, help="S3 output folder (contexts_*_B*.jsonl)")
    ap.add_argument("--cond", required=True, help="1,200 conditional questions (jsonl with qid, aid, head, condition)")
    ap.add_argument("--scripts", default=os.path.join(os.path.dirname(__file__), "..", ".."),
                    help="folder that contains s3_retrieval/ and s6_evaluation/")
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    sys.path.insert(0, os.path.join(a.scripts, "s3_retrieval", "scripts"))
    sys.path.insert(0, os.path.join(a.scripts, "s6_evaluation", "scripts"))
    from s3_retrieve_v2 import build_pointers, fill_budget
    from s6_evaluate import ccr_item, bootstrap_diff

    split = {r["aid"]: r.get("split") for r in read_jsonl(os.path.join(a.data, "articles_v2.jsonl"))}
    gold_aids = {g["aid"] for g in read_jsonl(os.path.join(a.data, "gold_spans.jsonl"))}
    raw = {r["aid"]: r for r in read_jsonl(os.path.join(a.data, "props_lp_raw.jsonl"))}
    lp = read_jsonl(os.path.join(a.data, "props_lp.jsonl"))

    # attached = pointers of the final graph whose (head, tail) pair is not in the raw graph in either direction
    no_att, attached = [], []
    for r in lp:
        pairs = {(p["head"], p["tail"]) for p in raw[r["aid"]]["pointers"]}
        pairs |= {(t, h) for h, t in pairs}
        keep = [p for p in r["pointers"] if (p["head"], p["tail"]) in pairs]
        attached += [(r["aid"], p) for p in r["pointers"] if (p["head"], p["tail"]) not in pairs]
        no_att.append(dict(r, pointers=keep))
    desc = {
        "n_attached": len(attached),
        "by_split": dict(collections.Counter(split.get(x) for x, _ in attached)),
        "in_articles_with_gold_span": sum(x in gold_aids for x, _ in attached),
        "in_articles_without_gold_span": sum(x not in gold_aids for x, _ in attached),
        "types": dict(collections.Counter(p["type"] for _, p in attached).most_common()),
        "empty_cue": sum(p["cue"] == "" for _, p in attached),
        "top_cues": dict(collections.Counter(p["cue"] for _, p in attached if p["cue"]).most_common(8)),
    }

    cond = {q["qid"]: q for q in read_jsonl(a.cond)}
    seeds = {r["qid"]: [u["uid"] for u in r["units"]] for r in read_jsonl(os.path.join(a.s3, "contexts_lp_noptr_B500.jsonl"))}
    qids = sorted(q for q in seeds if q in cond)
    full, na = build_pointers(lp), build_pointers(no_att)

    repro = {}
    for name, mode in [("lp", "both"), ("lp_out", "out")]:
        for B in (100, 500):
            saved = {r["qid"]: [u["uid"] for u in r["units"]] for r in read_jsonl(os.path.join(a.s3, f"contexts_{name}_B{B}.jsonl"))}
            repro[f"{name}_B{B}"] = sum(saved[q] == [u["uid"] for u in fill_budget(seeds[q], full[0], B, full[1], full[2], mode)] for q in qids)

    systems = [("lp_noptr", full, "none"), ("lp_out", full, "out"), ("lp", full, "both"),
               ("lp_out_noattach", na, "out"), ("lp_noattach", na, "both")]
    items, table = {}, {}
    for name, pb, mode in systems:
        for B in (100, 500):
            it = {q: ccr_item(cond[q], fill_budget(seeds[q], pb[0], B, pb[1], pb[2], mode), {}, 0.6) for q in qids}
            items[(name, B)] = it
            table[f"{name}|B{B}"] = {m: 100 * sum(x[m] for x in it.values()) / len(it) for m in ("ccr", "orphan")}
    boot = {}
    for B in (100, 500):
        for x, y in [("lp", "lp_noattach"), ("lp_out", "lp_out_noattach"), ("lp_noattach", "lp_noptr"), ("lp", "lp_noptr")]:
            for m in ("ccr", "orphan"):
                d, lo, hi = bootstrap_diff([items[(x, B)][q][m] for q in qids], [items[(y, B)][q][m] for q in qids])
                boot[f"{m}@B{B}: {x} - {y}"] = [100 * d, 100 * lo, 100 * hi]

    os.makedirs(a.out, exist_ok=True)
    res = {"n_questions": len(qids), "attached_pointers": desc, "reproduced_contexts": repro, "table": table, "bootstrap": boot}
    json.dump(res, open(os.path.join(a.out, "ablation_attached_pointers.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    L = ["# Ablation: removing the attached pointers", "",
         f"Questions: {len(qids)}. Reproduced saved contexts: " + ", ".join(f"{k} {v}/{len(qids)}" for k, v in repro.items()), "",
         "## Attached pointers", "", "```", json.dumps(desc, ensure_ascii=False, indent=1), "```", "",
         "## CCR / Orphan (%)", "", "| System | CCR@B100 | Orphan@B100 | CCR@B500 | Orphan@B500 |", "|---|---|---|---|---|"]
    for name, _, _ in systems:
        r1, r5 = table[f"{name}|B100"], table[f"{name}|B500"]
        L.append(f"| {name} | {r1['ccr']:.1f} | {r1['orphan']:.1f} | {r5['ccr']:.1f} | {r5['orphan']:.1f} |")
    L += ["", "## Paired bootstrap (1,000 resamples, points, 95% CI)", "", "| Comparison | Diff | CI |", "|---|---|---|"]
    L += [f"| {k} | {v[0]:+.2f} | [{v[1]:+.2f}, {v[2]:+.2f}] |" for k, v in boot.items()]
    open(os.path.join(a.out, "ablation_attached_pointers.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
