"""Rút 100 gold span từ tập eval để thẩm định chất lượng (paper §3.2).

- Chỉ lấy span thuộc split eval và Điều còn trong articles_v2.jsonl.
- Phân tầng theo loại điều kiện (oversample loại hiếm để đủ mẫu phân tích lỗi: 55/25/15/5).
- Mỗi Điều tối đa 1 span, mỗi văn bản luật tối đa 4 span -> tránh thiên lệch.
- Loại span trùng nguyên văn (head+condition) để không lặp câu mẫu.
- Đính kèm nguyên văn khoản chứa span để người chấm đối chiếu.
"""
import argparse, csv, json, os, random, re
from collections import Counter, defaultdict

QUOTA = {"VỚI_ĐIỀU_KIỆN": 55, "TRỪ_TRƯỜNG_HỢP": 25, "NHƯNG_PHẢI": 15, "KHÔNG_ÁP_DỤNG": 5}
MAX_PER_DOC = 4
SEED = 2026

KHOAN_RE = re.compile(r"(?m)^\s*(\d+)\.\s+")
def khoan_text(article, k, limit=1200):
    ms = list(KHOAN_RE.finditer(article))
    txt = article
    for i, m in enumerate(ms):
        if int(m.group(1)) == k:
            end = ms[i + 1].start() if i + 1 < len(ms) else len(article)
            txt = article[m.start():end]
            break
    txt = txt.strip()
    return txt if len(txt) <= limit else txt[:limit] + " …"


def read_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    parser = argparse.ArgumentParser(description="Draw 100-span audit sample from eval split.")
    parser.add_argument("--data", default="data_v2", help="Directory containing articles_v2.jsonl and gold_spans.jsonl")
    parser.add_argument("--out", default="results/span_review_v2", help="Output directory for sample and metadata")
    parser.add_argument("--seed", type=int, default=SEED, help="Random seed (default: 2026)")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    arts = {a["aid"]: a for a in read_jsonl(os.path.join(args.data, "articles_v2.jsonl"))}
    spans = [s for s in read_jsonl(os.path.join(args.data, "gold_spans.jsonl"))
             if s.get("split") == "eval" and s["aid"] in arts and arts[s["aid"]]["split"] == "eval"]

    rng = random.Random(args.seed)
    by_type = defaultdict(list)
    for s in spans:
        by_type[s["type"]].append(s)

    picked, used_aid, doc_cnt, seen_txt = [], set(), Counter(), set()
    for t, q in QUOTA.items():
        pool = by_type[t][:]
        rng.shuffle(pool)
        n = 0
        for s in pool:
            if n >= q:
                break
            doc = arts[s["aid"]]["doc_name"]
            key = (s["head"].strip().lower(), s["condition"].strip().lower())
            if s["aid"] in used_aid or doc_cnt[doc] >= MAX_PER_DOC or key in seen_txt:
                continue
            used_aid.add(s["aid"]); doc_cnt[doc] += 1; seen_txt.add(key)
            picked.append(s); n += 1
        if n < q:
            print(f"[warn] {t}: chỉ lấy được {n}/{q}")

    rng.shuffle(picked)  # trộn ngẫu nhiên

    cols = ["stt", "sid", "loai", "cue", "van_ban", "head", "condition", "nguyen_van_khoan",
            "nhan(D/P/S)", "ma_loi", "ghi_chu"]

    out_csv = os.path.join(args.out, "span_review_v2_sample.csv")
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for i, s in enumerate(picked, 1):
            a = arts[s["aid"]]
            w.writerow([i, s["sid"], s["type"], s["cue"], a["doc_name"], s["head"], s["condition"],
                        khoan_text(a["article_content"], s.get("khoan", 0)), "", "", ""])

    meta = {"seed": args.seed, "quota": QUOTA, "max_per_doc": MAX_PER_DOC, "n": len(picked),
            "pool_eval_spans": len(spans),
            "picked_by_type": dict(Counter(s["type"] for s in picked)),
            "n_docs": len(doc_cnt), "n_articles": len(used_aid)}
    json.dump(meta, open(os.path.join(args.out, "sample_meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(meta, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
