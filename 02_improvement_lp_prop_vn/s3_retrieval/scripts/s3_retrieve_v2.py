"""
s3_retrieve_v2.py — LP-Prop v2: truy xuất BGE-M3 cho 8 hệ, DÙNG LẠI embedding cũ của s3.

- Đơn vị (passage / proposition) của corpus v2 là tập con của corpus cũ -> lấy vector từ
  emb_<set>_bge-m3.npy cũ theo emb_map.json (do s1_clean tạo). Chỉ embed: passage mới + câu hỏi.
- Nếu không tìm thấy file cũ hoặc số dòng không khớp, tự embed lại toàn bộ tập đó (chậm hơn, vẫn đúng).
- Logic fill_budget / ranked_aids / con trỏ giống hệt run_s3_s6.py cũ.

Ra (trong --out): ranks_<hệ>.jsonl (top-20 Điều cho mọi câu hỏi eval), contexts_<hệ>_B<budget>.jsonl (câu cond), s3_meta.json

Dùng:
  python s3_retrieve_v2.py --data /kaggle/working/data_v2 --cond <file 1200 câu> --old_emb_root /kaggle/input --out /kaggle/working/work_s3v2
"""
import argparse, glob, json, os, time
from collections import OrderedDict, defaultdict
import numpy as np

SYSTEMS = {"passage": ("passage", "none"), "std": ("std", "none"), "lp_noptr": ("lp", "none"),
           "lp_out": ("lp", "out"), "lp": ("lp", "both"), "std_raw": ("std_raw", "none"),
           "lp_raw": ("lp_raw", "both"), "lp_edge_only": ("lp_edge_only", "both")}
ORDER = ["passage", "std_raw", "std", "lp_noptr", "lp_out", "lp_raw", "lp_edge_only", "lp"]
UNIT_SETS = ["passage", "std", "lp", "std_raw", "lp_raw", "lp_edge_only"]


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

def build_pointers(records):
    props, condition_ids, rule_of = OrderedDict(), defaultdict(list), defaultdict(list)
    for r in records:
        for p in r["props"]:
            props[p["uid"]] = p
        for e in r.get("pointers", []):
            if e["tail"] not in condition_ids[e["head"]]:
                condition_ids[e["head"]].append(e["tail"])
            if e["head"] not in rule_of[e["tail"]]:
                rule_of[e["tail"]].append(e["head"])
    return props, dict(condition_ids), dict(rule_of)

def fill_budget(ranked_uids, units, B, condition_ids=None, rule_of=None, mode="none"):
    condition_ids, rule_of = condition_ids or {}, rule_of or {}
    ctx, seen, used = [], set(), 0
    for uid in ranked_uids:
        if used >= B:
            break
        group = [uid]
        if mode in ("out", "both"):
            group = group + condition_ids.get(uid, [])
        if mode == "both":
            group = rule_of.get(uid, []) + group
        for q in group:
            if q in seen or used >= B or q not in units:
                continue
            w = units[q]["text"].split()[: B - used]
            ctx.append({"uid": q, "aid": units[q]["aid"], "text": " ".join(w)})
            seen.add(q); used += len(w)
    return ctx

def ranked_aids(ranked_uids, units):
    seen, out = set(), []
    for u in ranked_uids:
        a = units[u]["aid"]
        if a not in seen:
            seen.add(a); out.append(a)
    return out


class Encoder:
    def __init__(self, name, mock=False, dim=1024):
        self.mock, self.dim = mock, dim
        if mock:
            return
        import torch
        from sentence_transformers import SentenceTransformer
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[encoder] {name} trên {dev}", flush=True)
        self.m = SentenceTransformer(name, device=dev); self.m.max_seq_length = 512
        if dev == "cuda":
            self.m.half()

    def encode(self, texts, batch=128):
        if not texts:
            return np.zeros((0, self.dim), dtype="float32")
        if self.mock:
            rs = [np.random.default_rng(abs(hash(t)) % (2 ** 32)).standard_normal(self.dim) for t in texts]
            X = np.asarray(rs, dtype="float32"); return X / np.linalg.norm(X, axis=1, keepdims=True)
        return self.m.encode(texts, batch_size=batch, normalize_embeddings=True, show_progress_bar=True,
                             convert_to_numpy=True).astype("float32")


def search(X, Q, k):
    """Top-k inner product. Dùng faiss nếu có, không thì torch/numpy theo lô."""
    k = min(k, len(X))
    try:
        import faiss
        ix = faiss.IndexFlatIP(X.shape[1]); ix.add(X)
        return ix.search(Q, k)[1]
    except ImportError:
        pass
    try:
        import torch
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        Xt = torch.from_numpy(X).to(dev, dtype=torch.float16 if dev == "cuda" else torch.float32)
        out = []
        for i in range(0, len(Q), 2048):
            q = torch.from_numpy(Q[i:i + 2048]).to(dev, dtype=Xt.dtype)
            out.append(torch.topk(q @ Xt.T, k, dim=1).indices.cpu().numpy())
        return np.vstack(out)
    except ImportError:
        out = []
        for i in range(0, len(Q), 1024):
            s = Q[i:i + 1024] @ X.T
            idx = np.argpartition(-s, k - 1, axis=1)[:, :k]
            out.append(np.take_along_axis(idx, np.argsort(-np.take_along_axis(s, idx, 1), 1), 1))
        return np.vstack(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="/kaggle/working/data_v2")
    ap.add_argument("--cond", required=True, help="file câu hỏi cond (1.200 câu)")
    ap.add_argument("--old_emb_root", default="/kaggle/input")
    ap.add_argument("--out", default="/kaggle/working/work_s3v2")
    ap.add_argument("--encoder", default="BAAI/bge-m3")
    ap.add_argument("--budgets", type=int, nargs="+", default=[100, 500])
    ap.add_argument("--topk", type=int, default=100)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--mock_dim", type=int, default=64)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()
    tag = a.encoder.split("/")[-1]
    emb_map = json.load(open(os.path.join(a.data, "emb_map.json")))

    unit_sets = {"passage": (OrderedDict((u["uid"], u) for u in read_jsonl(os.path.join(a.data, "passages.jsonl"))), {}, {})}
    for m in UNIT_SETS[1:]:
        unit_sets[m] = build_pointers(read_jsonl(os.path.join(a.data, f"props_{m}.jsonl")))

    arts = {x["aid"]: x for x in read_jsonl(os.path.join(a.data, "articles_v2.jsonl"))}
    cond = [dict(q, kind="cond") for q in read_jsonl(a.cond) if q["aid"] in arts]
    gen = [dict(q, kind="generic") for q in read_jsonl(os.path.join(a.data, "qa_generic.jsonl"))
           if arts.get(q["aid"], {}).get("split") == "eval"]
    qs = cond + gen
    assert len({q["qid"] for q in qs}) == len(qs), "qid trùng giữa câu cond và generic"
    cond_ids = {q["qid"] for q in cond}
    print(f"[data] {len(cond)} câu cond + {len(gen)} câu generic eval", flush=True)

    enc = Encoder(a.encoder, mock=a.mock, dim=a.mock_dim)
    qc = os.path.join(a.out, f"emb_queries_{tag}.npy")
    if os.path.exists(qc) and len(np.load(qc)) == len(qs):
        Q = np.load(qc)
    else:
        Q = enc.encode([q["question"] for q in qs]); np.save(qc, Q)

    meta = {"n_cond": len(cond), "n_generic": len(gen), "units": {}, "emb": {}}
    for name in UNIT_SETS:
        units, c_ids, r_of = unit_sets[name]
        uids = list(units)
        rows = emb_map[name]["rows"]
        assert len(rows) == len(uids), f"emb_map lệch với {name}"
        hits = sorted(glob.glob(os.path.join(a.old_emb_root, "**", f"emb_{name}_{tag}.npy"), recursive=True))
        X = None
        if hits:
            old = np.load(hits[0], mmap_mode="r")
            if len(old) == emb_map[name]["n_old"]:
                X = np.zeros((len(uids), old.shape[1]), dtype="float32")
                keep = [i for i, r in enumerate(rows) if r >= 0]
                X[keep] = old[[rows[i] for i in keep]]
                # kiểm tra an toàn: embed lại 32 đơn vị ngẫu nhiên, phải gần trùng vector cũ
                probe = np.random.default_rng(0).choice(keep, size=min(32, len(keep)), replace=False) if keep else []
                cos = float(np.mean(np.sum(enc.encode([units[uids[i]]["text"] for i in probe]) * X[probe], axis=1))) if len(probe) and not a.mock else 1.0
                if cos < 0.97:
                    meta["emb"][name] = f"vector cũ không khớp văn bản (cos={cos:.3f}) -> embed lại toàn bộ"
                    X = None
                else:
                    new = [i for i, r in enumerate(rows) if r < 0]
                    if new:
                        X[new] = enc.encode([units[uids[i]]["text"] for i in new])
                    meta["emb"][name] = f"dùng lại {len(keep)} vector cũ (kiểm tra cos={cos:.3f}), embed mới {len(new)}"
            else:
                meta["emb"][name] = f"file cũ có {len(old)} dòng != {emb_map[name]['n_old']} -> embed lại toàn bộ"
        else:
            meta["emb"][name] = "không thấy file cũ -> embed lại toàn bộ"
        if X is None:
            X = enc.encode([units[u]["text"] for u in uids])
        print(f"[emb] {name}: {meta['emb'][name]}", flush=True)
        meta["units"][name] = len(uids)

        I = search(np.ascontiguousarray(X, dtype="float32"), np.ascontiguousarray(Q, dtype="float32"), a.topk)
        ranked = [[uids[j] for j in row if j >= 0] for row in I]
        for s in ORDER:
            src, mode = SYSTEMS[s]
            if src != name:
                continue
            write_jsonl(os.path.join(a.out, f"ranks_{s}.jsonl"),
                        [{"qid": q["qid"], "aids": ranked_aids(r, units)[:20]} for q, r in zip(qs, ranked)])
            for B in a.budgets:
                write_jsonl(os.path.join(a.out, f"contexts_{s}_B{B}.jsonl"),
                            [{"qid": q["qid"], "kind": "cond", "units": fill_budget(r, units, B, c_ids, r_of, mode)}
                             for q, r in zip(qs, ranked) if q["qid"] in cond_ids])
            print(f"[OK] {s}", flush=True)
    meta["minutes"] = round((time.time() - t0) / 60, 1)
    json.dump(meta, open(os.path.join(a.out, "s3_meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(meta, ensure_ascii=False, indent=1)); print("[done]")


if __name__ == "__main__":
    main()
