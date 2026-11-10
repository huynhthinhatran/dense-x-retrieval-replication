"""Tier 3 re-scoring from the saved reader and judge outputs (no GPU).

Two checks asked for in the review of the first version:
  * abstain = wrong: answers matched by ABSTAIN_PAT ("không đủ thông tin" ...) are forced to incorrect,
    then Accuracy and Cond-Acc are recomputed (the judge had marked 27.4% of them correct);
  * held-out questions: the judge prompt (v4) was tuned on the first 100 questions, so results are also
    reported on the remaining 1,100.

Usage:
  python tier3_rescore.py --work work_s5 --scripts ../.. --out results [--cond cond_questions_v2_eval_1200.jsonl]
Without --cond, the 100 calibration questions are read from the start of judge_v4.shard0.jsonl
(the calibration run judged them first: 100 questions x 11 systems x 2 calls).
"""
import argparse, collections, glob, json, os, sys

SYSTEMS = ["passage", "std", "lp_noptr", "lp_out", "lp"]


def read_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True, help="folder with reader.shard*.jsonl and judge_v4.shard*.jsonl")
    ap.add_argument("--scripts", default=os.path.join(os.path.dirname(__file__), "..", ".."))
    ap.add_argument("--cond", default=None, help="question file; its first --calib_n questions are the calibration set")
    ap.add_argument("--calib_n", type=int, default=100)
    ap.add_argument("--iters", type=int, default=1000)
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    sys.path.insert(0, os.path.join(a.scripts, "s5_reader_judge", "scripts"))
    sys.path.insert(0, os.path.join(a.scripts, "s6_evaluation", "scripts"))
    import s5_reader_judge as s5
    from s6_evaluate import bootstrap_diff

    answers = {r["key"]: r for p in sorted(glob.glob(os.path.join(a.work, "reader.shard*.jsonl"))) for r in read_jsonl(p)}
    jfiles = sorted(glob.glob(os.path.join(a.work, "judge_v4.shard*.jsonl")))
    judge = [r for p in jfiles for r in read_jsonl(p)]
    if a.cond:
        calib = {q["qid"] for q in read_jsonl(a.cond)[: a.calib_n]}
    else:
        calib, seen = set(), []
        for r in read_jsonl(jfiles[0]):
            if r["qid"] not in calib:
                calib.add(r["qid"])
            if len(calib) == a.calib_n:
                break

    mains, conds = {}, {}
    for r in judge:   # same parsing and precedence as s5_reader_judge.stage_aggregate
        if r["key"].endswith("#c"):
            v, k = s5.parse_cond(r["raw"]), r["key"][:-2]
            if v is not None or k not in conds:
                conds[k] = v
        else:
            v = s5.parse_main(r["raw"])
            if v is not None or r["key"] not in mains:
                mains[r["key"]] = v
    per = collections.defaultdict(dict)
    for k, r in answers.items():
        j = s5.merge_judge(mains.get(k), conds.get(k))
        if j is None:
            continue
        ab = int(bool(s5.ABSTAIN_PAT.search(r["raw"])))
        m = {"acc": j["correct"], "kept": j["condition_kept"], "cacc": int(j["correct"] and j["condition_kept"]),
             "over": j["overgeneralized"], "abst": ab}
        m["acc_f"] = 0 if ab else m["acc"]
        m["cacc_f"] = 0 if ab else m["cacc"]
        per[(r["system"], str(r["budget"]))][r["qid"]] = m

    allq = set(per[("lp", "500")])
    subsets = {"all": allq, "heldout": allq - calib}
    res = {"n_all": len(allq), "n_heldout": len(subsets["heldout"]), "n_calib": len(calib & allq),
           "abstentions": sum(m["abst"] for d in per.values() for m in d.values()),
           "abstentions_judged_correct": sum(m["abst"] and m["acc"] for d in per.values() for m in d.values()),
           "table": {}, "bootstrap": {}, "rank": {}}
    for name, sub in subsets.items():
        for (s, B), d in per.items():
            ks = [q for q in d if q in sub]
            res["table"][f"{name}|{s}|B{B}"] = {c: 100 * sum(d[q][c] for q in ks) / len(ks) for c in
                                                ("acc", "acc_f", "kept", "cacc", "cacc_f", "over", "abst")}
        for c in ("acc", "acc_f", "cacc", "cacc_f"):
            for B in ("100", "500"):
                order = sorted(SYSTEMS, key=lambda s: -res["table"][f"{name}|{s}|B{B}"][c])
                res["rank"][f"{name}|{c}|B{B}"] = order
                L = per[("lp", B)]
                for s in SYSTEMS[:-1]:
                    ks = sorted(q for q in sub if q in L and q in per[(s, B)])
                    d, lo, hi = bootstrap_diff([L[q][c] for q in ks], [per[(s, B)][q][c] for q in ks], a.iters)
                    res["bootstrap"][f"{name}|{c}@B{B}: lp - {s}"] = [100 * d, 100 * lo, 100 * hi, not (lo <= 0 <= hi)]

    os.makedirs(a.out, exist_ok=True)
    json.dump(res, open(os.path.join(a.out, "tier3_rescore.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    out = ["# Tier 3 re-scored", "",
           f"Questions: {res['n_all']} (held-out: {res['n_heldout']}, calibration: {res['n_calib']}). "
           f"Abstentions: {res['abstentions']}, judged correct: {res['abstentions_judged_correct']}.", "",
           "`_f`: abstention forced to incorrect.", ""]
    for name in subsets:
        out += [f"## {name} ({len(subsets[name])} questions, %)", "",
                "| Budget | System | Acc | Acc_f | Kept | Cond-Acc | Cond-Acc_f | Over-gen | Abstain |", "|---|---|---|---|---|---|---|---|---|"]
        keys = [k for k in res["table"] if k.startswith(name + "|")]
        keys.sort(key=lambda k: (k.split("|")[2], (SYSTEMS + ["oracle"]).index(k.split("|")[1])))
        for k in keys:
            r = res["table"][k]; _, s, B = k.split("|")
            out.append(f"| {B} | {s} | {r['acc']:.1f} | {r['acc_f']:.1f} | {r['kept']:.1f} | {r['cacc']:.1f} | {r['cacc_f']:.1f} | {r['over']:.1f} | {r['abst']:.1f} |")
        out += ["", "| Metric | Ranking (best first) |", "|---|---|"]
        out += [f"| {k.split('|', 1)[1]} | {' > '.join(v)} |" for k, v in res["rank"].items() if k.startswith(name + "|")]
        out += ["", "| Comparison | Diff | 95% CI | Sig. |", "|---|---|---|---|"]
        out += [f"| {k.split('|', 1)[1]} | {v[0]:+.1f} | [{v[1]:+.1f}, {v[2]:+.1f}] | {'*' if v[3] else ''} |"
                for k, v in res["bootstrap"].items() if k.startswith(name + "|")]
        out.append("")
    open(os.path.join(a.out, "tier3_rescore.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
