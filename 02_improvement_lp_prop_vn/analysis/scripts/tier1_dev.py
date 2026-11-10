"""Tier 1 on the held-out development split, and sensitivity to the coverage threshold tau.

tau = 0.6, the refinement rules and the prompts were fixed without a separate tuning split. Applying them
unchanged to D_dev (14 statutes not used anywhere else) checks that they do not only fit D_eval.

Usage:
  python tier1_dev.py --data data_v2 --scripts ../.. --out results
"""
import argparse, collections, json, os, sys

SYSTEMS = ["std_raw", "std", "lp_raw", "lp_edge_only", "lp"]


def read_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--scripts", default=os.path.join(os.path.dirname(__file__), "..", ".."))
    ap.add_argument("--taus", type=float, nargs="+", default=[0.5, 0.6, 0.7])
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    sys.path.insert(0, os.path.join(a.scripts, "s6_evaluation", "scripts"))
    from s6_evaluate import tier1, STRONG

    split = {r["aid"]: r.get("split") for r in read_jsonl(os.path.join(a.data, "articles_v2.jsonl"))}
    gold = read_jsonl(os.path.join(a.data, "gold_spans.jsonl"))
    props = {m: read_jsonl(os.path.join(a.data, f"props_{m}.jsonl")) for m in SYSTEMS}
    res = {}
    for sp in ("eval", "dev"):
        spans = collections.defaultdict(list)
        for g in gold:
            if split.get(g["aid"]) == sp and g["type"] in STRONG:
                spans[g["aid"]].append(g)
        for m in SYSTEMS:
            recs = [r for r in props[m] if split.get(r["aid"]) == sp]
            for t in a.taus:
                x = tier1(recs, spans, t)
                res[f"{sp}|{m}|{t}"] = {"n_spans": x["n_spans"], "drop": 100 * x["ConditionDropRate"],
                                        "uncond": 100 * x["UnconditionalRuleRate"], "ptr_ret": 100 * x["PointerRetention"],
                                        "ptr_per_article": x["pointers_per_article"]}
    os.makedirs(a.out, exist_ok=True)
    json.dump(res, open(os.path.join(a.out, "tier1_dev.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    out = ["# Tier 1 on D_eval and D_dev, tau sensitivity (%)", "",
           "| Split | System | tau | Spans | Drop | Uncond. | PtrRet | Ptr/Art |", "|---|---|---|---|---|---|---|---|"]
    for k, r in res.items():
        sp, m, t = k.split("|")
        out.append(f"| {sp} | {m} | {t} | {r['n_spans']} | {r['drop']:.1f} | {r['uncond']:.1f} | {r['ptr_ret']:.1f} | {r['ptr_per_article']:.2f} |")
    open(os.path.join(a.out, "tier1_dev.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
