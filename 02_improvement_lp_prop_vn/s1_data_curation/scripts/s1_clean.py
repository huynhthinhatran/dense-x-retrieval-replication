"""
s1_clean.py — LP-Prop v2: làm sạch corpus từ dữ liệu đã có (D1 + S2/work_clean). Chỉ dùng CPU.

Việc làm:
  1. Bỏ Điều chỉ có tiêu đề (mục lục bị cào nhầm, body < 5 từ sau khi bỏ dòng CHƯƠNG/MỤC/số trang).
  2. Bỏ toàn bộ văn bản dự thảo (doc_name bắt đầu bằng "Dự thảo").
  3. Gộp Điều trùng nội dung: giữ aid nhỏ nhất trong mỗi nhóm.
  4. Passage: giữ passage cũ của các Điều còn lại; tạo passage cho các Điều bị sót
     (bug split_khoan cắt rỗng Điều một đoạn / Điều kết thúc bằng dòng CHƯƠNG ...).
  5. Lọc gold_spans, qa_generic, props_* (s2) theo Điều còn lại. KHÔNG chạy lại LLM của s2:
     proposition được tách riêng cho từng Điều nên Điều giữ lại có nội dung y hệt.
  6. Ghi emb_map.json: với mỗi tập đơn vị (passage, std, lp, ...) — vị trí của từng đơn vị mới trong
     file embedding cũ của s3 (emb_<set>_bge-m3.npy), -1 nếu là đơn vị mới -> s3_v2 không phải embed lại.

Dùng:
  python s1_clean.py --input_root /kaggle/input --out /kaggle/working/data_v2
"""
import argparse, glob, hashlib, importlib.util, json, os, re
from collections import Counter, OrderedDict, defaultdict

PROP_SETS = ["std", "lp", "std_raw", "lp_raw", "lp_edge_only"]
HEAD_LINE = re.compile(r"^\s*(CHƯƠNG|Chương|MỤC|Mục|PHẦN|Phần)\s+[IVXLCDM\d]+", re.U)
PAGE_NUM = re.compile(r"\.{0,3}\s*\d{1,3}\s*$")


def read_jsonl(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for l in f:
            l = l.strip()
            if l:
                try:
                    out.append(json.loads(l))
                except json.JSONDecodeError:
                    pass
    return out


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def find(root, name, prefer=None):
    hits = sorted(glob.glob(os.path.join(root, "**", name), recursive=True))
    if prefer:
        hits = [h for h in hits if prefer in h] or hits
    if not hits:
        raise FileNotFoundError(f"không thấy {name} dưới {root}")
    return hits[0]


def real_body(article):
    """Phần thân Điều sau khi bỏ dòng tiêu đề Điều, dòng CHƯƠNG/MỤC và số trang mục lục."""
    lines = article.split("\n")[1:]
    keep = []
    for l in lines:
        s = l.strip()
        if not s or HEAD_LINE.match(s):
            continue
        if s.isupper() and len(s.split()) <= 20:      # dòng tên chương viết hoa
            continue
        keep.append(s)
    body = " ".join(keep)
    return PAGE_NUM.sub("", body).strip() if len(body.split()) < 30 else body


def make_passages(aid, article, split_khoan, target=(120, 190)):
    """Tạo passage cho Điều bị sót. Ưu tiên split_khoan của s2; nếu nó cắt rỗng thì dùng real_body."""
    pieces = [t.strip() for t in split_khoan(article).values() if t and t.strip()]
    if not pieces or sum(len(p.split()) for p in pieces) < 0.5 * len(real_body(article).split()):
        pieces = [p for p in re.split(r"\n\s*\n|\n", "\n".join(article.split("\n")[1:])) if p.strip()]
        pieces = [re.sub(r"^\s*\d+\.\s*", "", p).strip() for p in pieces
                  if not HEAD_LINE.match(p.strip()) and not (p.strip().isupper() and len(p.split()) <= 20)]
    # tách đoạn quá dài theo câu
    sents = []
    for p in pieces:
        if len(p.split()) <= target[1]:
            sents.append(p)
        else:
            sents += [s for s in re.split(r"(?<=[.;:])\s+", p) if s.strip()]
    out, cur = [], []
    for s in sents:
        if cur and len(" ".join(cur).split()) + len(s.split()) > target[1] and len(" ".join(cur).split()) >= target[0] // 2:
            out.append(" ".join(cur)); cur = []
        cur.append(s)
    if cur:
        out.append(" ".join(cur))
    return [{"uid": f"{aid}:c{i}", "aid": aid, "text": t} for i, t in enumerate(out) if t.split()]


def ordered_units(records):
    """Thứ tự đơn vị giống build_pointers() của s3 cũ: vị trí = lần xuất hiện đầu, nội dung = lần cuối."""
    units = OrderedDict()
    for r in records:
        for p in r["props"]:
            units[p["uid"]] = p
    return units


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input_root", default="/kaggle/input")
    ap.add_argument("--out", default="/kaggle/working/data_v2")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    p_articles = find(a.input_root, "articles_all.jsonl")
    p_gold = find(a.input_root, "gold_spans.jsonl", prefer="work-d1")
    p_pas = find(a.input_root, "passages.jsonl", prefer="work-d1")
    p_gen = find(a.input_root, "qa_generic.jsonl", prefer="work-d1")
    p_s2w = find(a.input_root, "s2_worker.py")
    p_props = {m: find(a.input_root, f"props_{m}.jsonl", prefer="work_clean") for m in PROP_SETS}
    print("[input]", json.dumps({"articles": p_articles, "gold": p_gold, "passages": p_pas, "generic": p_gen,
                                 "s2_worker": p_s2w, **{f"props_{k}": v for k, v in p_props.items()}}, ensure_ascii=False, indent=1))

    spec = importlib.util.spec_from_file_location("s2w", p_s2w); s2w = importlib.util.module_from_spec(spec); spec.loader.exec_module(s2w)

    arts = read_jsonl(p_articles)
    reason = {}
    for x in arts:
        if x["doc_name"].strip().startswith("Dự thảo"):
            reason[x["aid"]] = "draft"
        elif len(real_body(x["article_content"]).split()) < 5:
            reason[x["aid"]] = "heading_only"
    groups = defaultdict(list)
    for x in arts:
        if x["aid"] not in reason:
            groups[hashlib.md5(x["article_content"].strip().encode("utf-8")).hexdigest()].append(x["aid"])
    dup_of = {}
    for v in groups.values():
        if len(v) > 1:
            keep = min(v, key=lambda s: (len(s), s))
            for aid in v:
                if aid != keep:
                    reason[aid] = "duplicate"; dup_of[aid] = keep
    kept = [x for x in arts if x["aid"] not in reason]
    K = {x["aid"] for x in kept}
    write_jsonl(os.path.join(a.out, "articles_v2.jsonl"), kept)

    # passages
    old_pas = read_jsonl(p_pas)
    old_pas_row = {p["uid"]: i for i, p in enumerate(old_pas)}
    pas = [p for p in old_pas if p["aid"] in K]
    have = {p["aid"] for p in pas}
    new_pas = []
    for x in kept:
        if x["aid"] not in have:
            new_pas += make_passages(x["aid"], x["article_content"], s2w.split_khoan)
    rows = [old_pas_row[p["uid"]] for p in pas] + [-1] * len(new_pas)
    pas += new_pas
    write_jsonl(os.path.join(a.out, "passages.jsonl"), pas)
    emb_map = {"passage": {"n_old": len(old_pas), "rows": rows}}

    # gold spans, generic QA
    gold = [g for g in read_jsonl(p_gold) if g["aid"] in K]
    write_jsonl(os.path.join(a.out, "gold_spans.jsonl"), gold)
    gen = [q for q in read_jsonl(p_gen) if q["aid"] in K]
    write_jsonl(os.path.join(a.out, "qa_generic.jsonl"), gen)

    # props của s2 + bản đồ embedding cũ
    prop_stats = {}
    for m, path in p_props.items():
        old = read_jsonl(path)
        old_units = ordered_units(old)
        old_row = {u: i for i, u in enumerate(old_units)}
        new = []
        for r in old:
            if r["aid"] not in K:
                continue
            seen = OrderedDict()
            for p in r["props"]:
                seen[p["uid"]] = old_units[p["uid"]]          # nội dung = lần xuất hiện cuối (giống s3 cũ)
            valid = set(seen)
            ptrs = [e for e in r.get("pointers", []) if e["head"] in valid and e["tail"] in valid]
            new.append(dict(r, props=list(seen.values()), pointers=ptrs))
        write_jsonl(os.path.join(a.out, f"props_{m}.jsonl"), new)
        units = ordered_units(new)
        emb_map[m] = {"n_old": len(old_units), "rows": [old_row[u] for u in units]}
        prop_stats[m] = {"articles": len(new), "props": sum(len(r["props"]) for r in new),
                         "pointers": sum(len(r.get("pointers", [])) for r in new)}
    json.dump(emb_map, open(os.path.join(a.out, "emb_map.json"), "w"))

    ev = [x for x in kept if x.get("split") == "eval"]
    stats = {
        "articles_in": len(arts), "articles_kept": len(kept), "articles_eval": len(ev),
        "docs_kept": len({x["doc_name"] for x in kept}),
        "removed": dict(Counter(reason.values())), "duplicate_of": dup_of,
        "passages": len(pas), "passages_new": len(new_pas), "articles_with_new_passages": len({p["aid"] for p in new_pas}),
        "gold_spans": len(gold), "gold_spans_eval": sum(g["aid"] in {x["aid"] for x in ev} for g in gold),
        "qa_generic": len(gen), "props": prop_stats,
    }
    json.dump(stats, open(os.path.join(a.out, "stats_v2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(reason, open(os.path.join(a.out, "removed_aids.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(json.dumps({k: v for k, v in stats.items() if k != "duplicate_of"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
