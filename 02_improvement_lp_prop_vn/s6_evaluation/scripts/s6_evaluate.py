"""
s6_evaluate.py — Chấm Tầng 1 + Tầng 2 + Paired Bootstrap cho LP-Prop,
đọc lại ranks_*.jsonl / contexts_*.jsonl đã có từ s3 (KHÔNG encode lại).

Khác với phần s6 trong run_s3_s6.py:
  1. Luôn dùng ĐÚNG bộ 1.200 câu cond (cond_questions_eval_1200.jsonl của work_clean),
     không phụ thuộc thứ tự --inputs.
  2. Chấm "dedup-aware": các Điều có nội dung giống hệt nhau (133 nhóm) được coi là
     cùng một đáp án (Recall/MRR/CCR). Vẫn báo kèm Recall@5 strict (theo aid) để đối chiếu.
  3. Câu generic: bỏ câu thuộc Điều chỉ có tiêu đề (body < 5 từ) hoặc Điều không có
     passage nào, để so sánh công bằng giữa các mức hạt (áp dụng cho MỌI hệ).

Chạy trên Kaggle (add 3 dataset D1, S2, S3 làm input):
  python s6_evaluate.py --root /kaggle/input --out /kaggle/working/results
"""
import argparse, glob, hashlib, json, os, random, re, unicodedata
from collections import Counter, defaultdict

STRONG = {"TRỪ_TRƯỜNG_HỢP", "KHÔNG_ÁP_DỤNG", "VỚI_ĐIỀU_KIỆN", "NHƯNG_PHẢI", "GIỚI_HẠN"}
STOP = set("của và các là được có cho theo với trong này đó những một người phải thì".split())
ORDER = ["passage", "std_raw", "std", "lp_noptr", "lp_out", "lp_raw", "lp_edge_only", "lp"]
TIER1_SYS = ["std_raw", "std", "lp_raw", "lp_edge_only", "lp"]
BASES = ["passage", "std", "lp_noptr", "lp_out", "lp_raw", "lp_edge_only"]


# ---------------- tiện ích ----------------
def norm(s):
    return unicodedata.normalize("NFC", s or "")

def toks(s):
    return [w for w in re.findall(r"\w+", norm(s).lower()) if w not in STOP]

def coverage(span, texts):
    st = toks(span)
    if not st:
        return 0.0
    bag = set(w for t in texts for w in toks(t))
    return sum(1 for w in st if w in bag) / len(st)

def read_jsonl(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for l in f:
            l = l.strip()
            if l:
                try:
                    out.append(json.loads(l))
                except json.JSONDecodeError:
                    continue
    return out

def find(root, name, prefer=None):
    """Tìm file theo tên dưới root; nếu nhiều bản, ưu tiên đường dẫn chứa `prefer`."""
    hits = sorted(glob.glob(os.path.join(root, "**", name), recursive=True))
    if not hits:
        return None
    if prefer:
        pref = [h for h in hits if prefer in h]
        if pref:
            return pref[0]
    return hits[0]

mean = lambda xs: sum(xs) / len(xs) if xs else float("nan")
pct = lambda x: "–" if x != x else f"{100 * x:.1f}"


# ---------------- Tầng 1 (giữ nguyên công thức gốc) ----------------
def tier1(records, spans_by_aid, tau=0.6):
    by_aid = {r["aid"]: r for r in records}
    n = drop = uncond = keep_ptr = 0
    for aid, spans in spans_by_aid.items():
        r = by_aid.get(aid)
        if r is None:
            continue
        texts = {p["uid"]: p["text"] for p in r["props"]}
        for sp in spans:
            n += 1
            cond_any = any(coverage(sp["condition"], [t]) >= tau for t in texts.values())
            head_any = any(coverage(sp["head"], [t]) >= tau for t in texts.values())
            drop += not cond_any
            uncond += head_any and not cond_any
            self_c = any(coverage(sp["head"], [t]) >= tau and coverage(sp["condition"], [t]) >= tau
                         for t in texts.values())
            pair = any(coverage(sp["head"], [texts[e["head"]]]) >= tau and coverage(sp["condition"], [texts[e["tail"]]]) >= tau
                       for e in r.get("pointers", []) if e["head"] in texts and e["tail"] in texts)
            keep_ptr += self_c or pair
    n_props = sum(len(r["props"]) for r in records)
    words = [len(p["text"].split()) for r in records for p in r["props"]]
    return {
        "n_spans": n,
        "ConditionDropRate": drop / max(n, 1),
        "UnconditionalRuleRate": uncond / max(n, 1),
        "PointerRetention": keep_ptr / max(n, 1),
        "props_per_article": n_props / max(len(records), 1),
        "words_per_prop": sum(words) / max(len(words), 1),
        "pointers_per_article": sum(len(r.get("pointers", [])) for r in records) / max(len(records), 1),
    }


# ---------------- Tầng 2 (dedup-aware) ----------------
def recall_mrr(aids, gold_aid, grp, k=5):
    """grp: aid -> id nhóm nội dung. Hit nếu Điều trong top-k cùng nhóm với gold."""
    g = grp.get(gold_aid, gold_aid)
    for i, a in enumerate(aids[:k]):
        if grp.get(a, a) == g:
            return 1.0, 1.0 / (i + 1)
    return 0.0, 0.0

def recall_strict(aids, gold_aid, k=5):
    return float(gold_aid in aids[:k])

def ccr_item(q, ctx, grp, tau=0.6):
    g = grp.get(q["aid"], q["aid"])
    texts = [u["text"] for u in ctx if grp.get(u["aid"], u["aid"]) == g]
    h = coverage(q["head"], texts) >= tau
    c = coverage(q["condition"], texts) >= tau
    return {"head": float(h), "ccr": float(h and c), "orphan": float(h and not c)}

def bootstrap_diff(a, b, iters=1000, seed=0):
    rng = random.Random(seed); n = len(a)
    if n == 0:
        return 0.0, 0.0, 0.0
    ds = []
    for _ in range(iters):
        idx = [rng.randrange(n) for _ in range(n)]
        ds.append(sum(a[i] - b[i] for i in idx) / n)
    ds.sort()
    return sum(x - y for x, y in zip(a, b)) / n, ds[int(.025 * iters)], ds[int(.975 * iters) - 1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/kaggle/input", help="thư mục chứa 3 dataset D1, S2, S3")
    ap.add_argument("--out", default="/kaggle/working/results")
    ap.add_argument("--data", default=None, help="v2: thư mục data_v2 (articles_v2, passages, gold_spans, qa_generic, props_*)")
    ap.add_argument("--runs", default=None, help="v2: thư mục ranks_*/contexts_* của s3_v2")
    ap.add_argument("--cond", default=None, help="v2: file câu hỏi cond")
    ap.add_argument("--budgets", type=int, nargs="+", default=[100, 500])
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--iters", type=int, default=1000)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    # ---- nạp dữ liệu ----
    D = a.data or a.root          # v2: --data trỏ thẳng tới data_v2 (không tìm lẫn sang dataset cũ)
    R = a.runs or a.root          # v2: --runs trỏ tới thư mục ranks/contexts của s3_v2
    arts_path = (find(D, "articles_v2.jsonl") or find(D, "articles_all.jsonl") or find(D, "articles_1000.jsonl"))
    cond_path = a.cond or find(a.root, "cond_questions_eval_1200.jsonl")
    assert cond_path, "Không thấy file câu hỏi cond (--cond)"
    paths = {
        "articles": arts_path,
        "cond": cond_path,
        "generic": find(D, "qa_generic.jsonl"),
        "gold": find(D, "gold_spans.jsonl"),
        "passages": find(D, "passages.jsonl"),
    }
    print("Đường dẫn dùng:", json.dumps(paths, ensure_ascii=False, indent=1))

    arts = {x["aid"]: x for x in read_jsonl(paths["articles"])}
    eval_aids = {k for k, v in arts.items() if v.get("split") == "eval"}

    # nhóm nội dung trùng
    h2a = defaultdict(list)
    for aid, x in arts.items():
        h2a[hashlib.md5(x["article_content"].strip().encode("utf-8")).hexdigest()].append(aid)
    grp = {aid: min(v) for v in h2a.values() for aid in v}
    n_dup_groups = sum(1 for v in h2a.values() if len(v) > 1)

    # Điều không dùng cho generic
    pas_aids = {p["aid"] for p in read_jsonl(paths["passages"])}
    heading_only = {k for k, v in arts.items() if len(v["article_content"].partition("\n")[2].split()) < 5}
    excl_generic = heading_only | (set(arts) - pas_aids)

    cond_list = [q for q in read_jsonl(paths["cond"]) if q["aid"] in eval_aids]
    gen_all = [q for q in read_jsonl(paths["generic"]) if q["aid"] in eval_aids]
    gen_list = [q for q in gen_all if q["aid"] not in excl_generic]
    cond_map = {q["qid"]: q for q in cond_list}
    gen_map = {q["qid"]: q for q in gen_list}
    n_cond_dup = sum(1 for q in cond_list if len(h2a[hashlib.md5(arts[q["aid"]]["article_content"].strip().encode("utf-8")).hexdigest()]) > 1)
    print(f"cond = {len(cond_list)} (trong đó {n_cond_dup} câu thuộc Điều có bản trùng) | "
          f"generic = {len(gen_list)} (đã bỏ {len(gen_all) - len(gen_list)} câu thuộc Điều rỗng/không passage)")

    spans = defaultdict(list)
    for s in read_jsonl(paths["gold"]):
        if s["aid"] in eval_aids and s["type"] in STRONG:
            spans[s["aid"]].append(s)

    res = {"split": "eval",
           "setup": {"n_cond": len(cond_list), "n_cond_on_dup_articles": n_cond_dup,
                     "n_generic": len(gen_list), "n_generic_dropped": len(gen_all) - len(gen_list),
                     "dup_groups": n_dup_groups, "k": a.k, "paths": paths},
           "tier1": {}, "tier2": {}, "significance": {}}

    # ---- Tầng 1 ----
    for m in TIER1_SYS:
        f = find(D, f"props_{m}.jsonl", prefer=None if a.data else "work_clean")
        if f:
            recs = [r for r in read_jsonl(f) if r["aid"] in eval_aids]
            res["tier1"][m] = tier1(recs, spans, 0.6)
            print(f"[Tier1] {m}: {res['tier1'][m]['ConditionDropRate']:.4f} drop")

    # ---- Tầng 2 ----
    vec = defaultdict(dict)
    for s in ORDER:
        rf = find(R, f"ranks_{s}.jsonl")
        if not rf:
            print(f"[!] thiếu ranks_{s}.jsonl — bỏ qua"); continue
        r_c, r_cs, r_g, r_gs, m_g = {}, [], [], [], []
        for r in read_jsonl(rf):
            q = cond_map.get(r["qid"]) or gen_map.get(r["qid"])
            if not q:
                continue
            rec, mrr = recall_mrr(r["aids"], q["aid"], grp, a.k)
            strict = recall_strict(r["aids"], q["aid"], a.k)
            if r["qid"] in cond_map:
                r_c[r["qid"]] = rec; r_cs.append(strict)
            else:
                r_g.append(rec); r_gs.append(strict); m_g.append(mrr)
        d = res["tier2"].setdefault(s, {})
        d.update({f"Recall@{a.k}_cond": mean(list(r_c.values())), f"Recall@{a.k}_cond_strict": mean(r_cs),
                  f"Recall@{a.k}_generic": mean(r_g), f"Recall@{a.k}_generic_strict": mean(r_gs),
                  f"MRR@{a.k}_generic": mean(m_g), "n_cond_ranked": len(r_c), "n_generic_ranked": len(r_g)})
        vec[f"Recall@{a.k}_cond"][s] = r_c

        for B in a.budgets:
            cf = find(R, f"contexts_{s}_B{B}.jsonl")
            if not cf:
                continue
            items = {r["qid"]: ccr_item(cond_map[r["qid"]], r["units"], grp, 0.6)
                     for r in read_jsonl(cf) if r["qid"] in cond_map}
            d[f"CCR@B{B}"] = mean([x["ccr"] for x in items.values()])
            d[f"Orphan@B{B}"] = mean([x["orphan"] for x in items.values()])
            d[f"HeadRecall@B{B}"] = mean([x["head"] for x in items.values()])
            d[f"n_ctx@B{B}"] = len(items)
            vec[f"CCR@B{B}"][s] = {k: x["ccr"] for k, x in items.items()}
            vec[f"Orphan@B{B}"][s] = {k: x["orphan"] for k, x in items.items()}
        print(f"[Tier2] {s}: n_cond={len(r_c)} R@{a.k}_cond={pct(d[f'Recall@{a.k}_cond'])}")

    # ---- Paired bootstrap: lp vs các hệ khác ----
    for metric, by_sys in vec.items():
        for base in BASES:
            if "lp" in by_sys and base in by_sys:
                A, Bv = by_sys["lp"], by_sys[base]
                ks = sorted(set(A) & set(Bv))
                if ks:
                    dlt, lo, hi = bootstrap_diff([A[k] for k in ks], [Bv[k] for k in ks], a.iters)
                    res["significance"][f"{metric}: lp - {base}"] = {
                        "diff": dlt, "ci95": [lo, hi], "n": len(ks), "significant": not (lo <= 0 <= hi)}

    json.dump(res, open(os.path.join(a.out, "results.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # ---- bảng markdown ----
    k = a.k
    L = [f"# Kết quả LP-Prop — BGE-M3 (split = eval)", "",
         f"- Câu có điều kiện: **{len(cond_list)}** ({n_cond_dup} câu thuộc Điều có bản trùng nội dung; chấm dedup-aware)",
         f"- Câu generic: **{len(gen_list)}** (đã bỏ {len(gen_all) - len(gen_list)} câu thuộc Điều chỉ có tiêu đề / không có passage)",
         f"- Nhóm Điều trùng nội dung trong corpus: {n_dup_groups}", ""]
    if res["tier1"]:
        L += ["## Tầng 1 — Propositionizer", "",
              "| Hệ | Spans | Condition Drop (%) | Unconditional Rule (%) | Pointer Retention (%) | Props/Điều | Từ/prop | Pointers/Điều |",
              "|---|---|---|---|---|---|---|---|"]
        for m, d in res["tier1"].items():
            L.append(f"| {m} | {d['n_spans']} | {pct(d['ConditionDropRate'])} | {pct(d['UnconditionalRuleRate'])} | "
                     f"{pct(d['PointerRetention'])} | {d['props_per_article']:.2f} | {d['words_per_prop']:.2f} | {d['pointers_per_article']:.2f} |")
        L.append("")
    if res["tier2"]:
        cols = [f"Recall@{k}_cond", f"Recall@{k}_cond_strict", f"Recall@{k}_generic", f"MRR@{k}_generic"]
        for B in a.budgets:
            cols += [f"HeadRecall@B{B}", f"CCR@B{B}", f"Orphan@B{B}"]
        L += ["## Tầng 2 — Truy xuất BGE-M3 (%)", "", "| Hệ | " + " | ".join(cols) + " |", "|---" * (len(cols) + 1) + "|"]
        for s in [x for x in ORDER if x in res["tier2"]]:
            L.append(f"| {s} | " + " | ".join(pct(res["tier2"][s].get(c, float("nan"))) for c in cols) + " |")
        L.append("")
    if res["significance"]:
        L += [f"## Paired Bootstrap ({a.iters} lần)", "", "| So sánh | Chênh lệch (điểm %) | CI 95% | n | Có ý nghĩa |", "|---|---|---|---|---|"]
        for name, d in res["significance"].items():
            L.append(f"| {name} | {100 * d['diff']:+.2f} | [{100 * d['ci95'][0]:+.2f}, {100 * d['ci95'][1]:+.2f}] | {d['n']} | {'✓' if d['significant'] else ''} |")
    md = "\n".join(L) + "\n"
    open(os.path.join(a.out, "tables.md"), "w", encoding="utf-8").write(md)
    print("\n" + md)


if __name__ == "__main__":
    main()
