"""Worker độc lập xử lý Bước 2 (Propositionize) trên Corpus mới (9,715 Điều).
Chạy độc lập hoàn toàn, không phụ thuộc gói code lp_prop_pipeline cũ.
Hỗ trợ chạy 2 GPU T4 song song + tự động lưu Checkpoint trước 12 tiếng + Resume.
"""
import argparse, glob, json, os, re, shutil, time, unicodedata
from collections import Counter

DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct-AWQ"
LOGIC_TYPES = {
    "TRỪ_TRƯỜNG_HỢP", "KHÔNG_ÁP_DỤNG", "VỚI_ĐIỀU_KIỆN",
    "NHƯNG_PHẢI", "GIỚI_HẠN", "HIỆU_LỰC", "DẪN_CHIẾU"
}

_TAIL_DUMP_RE = re.compile(
    r"(?:[-_]{4,}\s*\n|"
    r"\bLuật này (?:đã )?được Quốc hội|"
    r"\bBộ luật này (?:đã )?được Quốc hội|"
    r"\bPháp lệnh này (?:đã )?được|"
    r"\bNghị quyết này (?:đã )?được Quốc hội|"
    r"QUỐC\s*HỘI|"
    r"CỘNG\s+HÒA\s+XÃ\s+HỘI\s+CHỦ\s+NGHĨA\s+VIỆT\s+NAM|"
    r"CHỦ\s+TỊCH\s+QUỐC\s+HỘI|"
    r"ỦY\s+BAN\s+THƯỜNG\s+VỤ\s+QUỐC\s+HỘI\s*(?:Số|Pháp lệnh))"
)
_KHOAN_RE = re.compile(r"(?m)^\s*(\d+)\.\s+")
_HEADING_RE = re.compile(r"(?m)^\s*(?:Mục|Chương|Phần|MỤC|CHƯƠNG|PHẦN|Điều|ĐIỀU)\s+[0-9IVXLCDM]+(?:\.|\b)")
_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)
_SENT = re.compile(r"(?<=[.;])\s+")


def norm(s):
    s = unicodedata.normalize("NFC", s or "")
    s = re.sub(
        r"([a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ])(thì\s+)",
        r"\1 \2", s
    )
    s = re.sub(
        r"([a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ])"
        r"([A-ZÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ])",
        r"\1. \2", s
    )
    return s


def clean_article_raw(article):
    article = norm(article)
    m = _TAIL_DUMP_RE.search(article)
    if m and m.start() > 20:
        article = article[:m.start()].strip()
    article = re.sub(
        r"^(Điều\s+\d+\.[^\n]{3,120}?)(?:\s{2,}|\s+(?=(?:Trường hợp|Trong trường hợp|Nếu|Khi|Đối với|Căn cứ|Tổ chức|Cá nhân|Cơ quan|Bộ|Ủy ban|Chính phủ|Người)\b))",
        r"\1\n",
        article.strip()
    )
    lines = article.strip().split("\n")
    first_line_low = lines[0].lower() if lines else ""
    is_amending = any(w in first_line_low for w in ("sửa đổi", "bổ sung", "bãi bỏ"))
    if not is_amending:
        dm = re.search(r"(?:^|\n|[.;])\s*Điều\s+\d+\.", article[15:])
        if dm:
            cut_idx = 15 + dm.start() + (1 if article[15 + dm.start()] in ".;" else 0)
            article = article[:cut_idx].strip()
        ms = list(_KHOAN_RE.finditer(article))
        if len(ms) > 1:
            prev_k = int(ms[0].group(1))
            for m_k in ms[1:]:
                k = int(m_k.group(1))
                if k <= prev_k:
                    article = article[:m_k.start()].strip()
                    break
                prev_k = k
    return article


def split_khoan(article):
    article = clean_article_raw(article)
    lines = article.strip().split("\n")
    if len(lines) > 1 and len(lines[0].split()) <= 25 and not lines[0].strip().endswith((".", ";", ":")):
        if not re.match(r"^\s*\d+\.", lines[0]):
            article = "\n".join(lines[1:]).strip()
    ms = list(_KHOAN_RE.finditer(article))
    if not ms:
        res = {0: article.strip()}
    else:
        res = {}
        preamble = article[:ms[0].start()].strip()
        if preamble:
            res[0] = preamble
        for i, m in enumerate(ms):
            end_pos = ms[i + 1].start() if i + 1 < len(ms) else len(article)
            res[int(m.group(1))] = article[m.end():end_pos].strip()
    for k in list(res.keys()):
        m = _HEADING_RE.search(res[k])
        if m:
            res[k] = res[k][:m.start()].strip()
    return res


# =====================================================================
# Prompts cho LP-Prop va Standard Dense X
# =====================================================================
EX1 = """Điều 12. Thời hạn nộp hồ sơ
1. Người đề nghị cấp giấy phép phải nộp hồ sơ trong thời hạn 30 ngày kể từ ngày phát sinh nghĩa vụ, trừ trường hợp quy định tại khoản 2 Điều này.
2. Trường hợp người đề nghị là doanh nghiệp nhỏ và vừa thì thời hạn nộp hồ sơ là 45 ngày, nhưng phải thông báo trước cho cơ quan quản lý."""

EX2 = """Điều 25. Miễn tiền sử dụng nước sạch
1. Hộ gia đình thuộc diện hộ nghèo được miễn tiền sử dụng nước sạch nếu lượng nước sử dụng không quá 4 mét khối mỗi tháng.
2. Quy định tại khoản 1 Điều này không áp dụng đối với hộ gia đình sử dụng nước sạch cho mục đích kinh doanh."""

EX1_PROPS = [
    "Người đề nghị cấp giấy phép phải nộp hồ sơ trong thời hạn 30 ngày kể từ ngày phát sinh nghĩa vụ.",
    "Người đề nghị cấp giấy phép là doanh nghiệp nhỏ và vừa có thời hạn nộp hồ sơ là 45 ngày.",
    "Doanh nghiệp nhỏ và vừa áp dụng thời hạn nộp hồ sơ 45 ngày phải thông báo trước cho cơ quan quản lý.",
]
EX2_PROPS = [
    "Hộ gia đình thuộc diện hộ nghèo được miễn tiền sử dụng nước sạch.",
    "Hộ nghèo chỉ được miễn tiền sử dụng nước sạch khi lượng nước sử dụng không quá 4 mét khối mỗi tháng.",
    "Việc miễn tiền sử dụng nước sạch cho hộ nghèo không áp dụng đối với hộ gia đình sử dụng nước sạch cho mục đích kinh doanh.",
]

EX1_LP = {
    "propositions": [
        {"pid": "p1", "text": EX1_PROPS[0], "role": "RULE", "khoan": 1},
        {"pid": "p2", "text": EX1_PROPS[1], "role": "MODIFIER", "khoan": 2},
        {"pid": "p3", "text": EX1_PROPS[2], "role": "MODIFIER", "khoan": 2},
    ],
    "edges": [
        {"head": "p1", "tail": "p2", "type": "TRỪ_TRƯỜNG_HỢP", "cue": "trừ trường hợp quy định tại khoản 2 Điều này"},
        {"head": "p2", "tail": "p3", "type": "NHƯNG_PHẢI", "cue": "nhưng phải"},
    ],
}
EX2_LP = {
    "propositions": [
        {"pid": "p1", "text": EX2_PROPS[0], "role": "RULE", "khoan": 1},
        {"pid": "p2", "text": EX2_PROPS[1], "role": "MODIFIER", "khoan": 1},
        {"pid": "p3", "text": EX2_PROPS[2], "role": "MODIFIER", "khoan": 2},
    ],
    "edges": [
        {"head": "p1", "tail": "p2", "type": "VỚI_ĐIỀU_KIỆN", "cue": "nếu"},
        {"head": "p1", "tail": "p3", "type": "KHÔNG_ÁP_DỤNG", "cue": "không áp dụng đối với"},
    ],
}

LP_SYSTEM = """Bạn là chuyên gia kỹ thuật lập pháp Việt Nam. Nhiệm vụ: phân rã một Điều luật thành các mệnh đề (proposition) và các con trỏ điều kiện giữa chúng. Chỉ trả về JSON hợp lệ, không giải thích.

Quy tắc:
1. Mỗi mệnh đề diễn đạt đúng MỘT ý pháp lý và đọc độc lập vẫn hiểu: thay "Điều này", "khoản 1", "người nói trên" bằng nội dung cụ thể.
2. Giữ nguyên chữ của văn bản ở mức tối đa. Không thêm "luôn", "mọi", "trong mọi trường hợp". Không bỏ hoặc đổi con số, thời hạn, chủ thể.
3. role: RULE = nguyên tắc chính; MODIFIER = điều kiện, ngoại lệ, giới hạn, nghĩa vụ kèm theo; FACT = định nghĩa hoặc thông tin khác.
4. Mỗi khi văn bản có quan hệ "A trừ/nếu/nhưng phải/không áp dụng... B", tạo cạnh head = mệnh đề A, tail = mệnh đề B, type là MỘT trong:
   TRỪ_TRƯỜNG_HỢP, KHÔNG_ÁP_DỤNG, VỚI_ĐIỀU_KIỆN, NHƯNG_PHẢI, GIỚI_HẠN, HIỆU_LỰC, DẪN_CHIẾU.
   cue = cụm từ gốc gây ra quan hệ (chép nguyên văn).
5. Nếu ngoại lệ nằm ở khoản khác, vẫn nối cạnh tới mệnh đề của khoản đó.

Schema:
{"propositions":[{"pid":"p1","text":"...","role":"RULE|MODIFIER|FACT","khoan":1}],
 "edges":[{"head":"p1","tail":"p2","type":"...","cue":"..."}]}"""

STD_SYSTEM = """Hãy phân rã đoạn văn bản thành các mệnh đề rõ ràng, đơn giản, đọc độc lập vẫn hiểu được.
1. Tách câu ghép thành các câu đơn. Giữ nguyên cách diễn đạt của văn bản gốc khi có thể.
2. Với mỗi thực thể có kèm thông tin mô tả, tách thông tin mô tả đó thành một mệnh đề riêng.
3. Làm cho mệnh đề độc lập với ngữ cảnh: thay đại từ và cụm chỉ định ("nó", "người này", "Điều này") bằng tên đầy đủ của thực thể.
4. Trả về danh sách mệnh đề dưới dạng mảng JSON các chuỗi, không giải thích."""


def build_messages(article, mode):
    w = article.split()
    if len(w) > 2000:
        article = " ".join(w[:2000])
    if mode == "lp":
        return [
            {"role": "system", "content": LP_SYSTEM},
            {"role": "user", "content": EX1},
            {"role": "assistant", "content": json.dumps(EX1_LP, ensure_ascii=False)},
            {"role": "user", "content": EX2},
            {"role": "assistant", "content": json.dumps(EX2_LP, ensure_ascii=False)},
            {"role": "user", "content": article},
        ]
    return [
        {"role": "system", "content": STD_SYSTEM},
        {"role": "user", "content": EX1},
        {"role": "assistant", "content": json.dumps(EX1_PROPS, ensure_ascii=False)},
        {"role": "user", "content": EX2},
        {"role": "assistant", "content": json.dumps(EX2_PROPS, ensure_ascii=False)},
        {"role": "user", "content": article},
    ]


# =====================================================================
# JSON Parsing & I/O
# =====================================================================
def read_jsonl(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for l in f:
            l = l.strip()
            if not l:
                continue
            try:
                out.append(json.loads(l))
            except json.JSONDecodeError:
                continue
    return out


def write_jsonl(path, rows, mode="w"):
    with open(path, mode, encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        f.flush()


def parse_llm_json(raw):
    raw = norm(raw).strip()
    cands = [m.group(1) for m in _FENCE.finditer(raw)] + [raw]
    dec = json.JSONDecoder()
    for c in cands:
        for i, ch in enumerate(c):
            if ch in "{[":
                try:
                    return dec.raw_decode(c[i:])[0]
                except json.JSONDecodeError:
                    continue
    return None


def fallback_props(article):
    return [s.strip() for t in split_khoan(article).values() for s in _SENT.split(t) if len(s.split()) >= 3]


def normalize_output(aid, js, mode):
    props, ptrs, bad = [], [], 0
    if isinstance(js, dict):
        plist = js.get("propositions", [])
    elif isinstance(js, list):
        plist = js
    else:
        plist = []
    pid2uid = {}
    for i, p in enumerate(plist):
        if isinstance(p, str):
            p = {"pid": f"p{i + 1}", "text": p}
        if not isinstance(p, dict) or not str(p.get("text", "")).strip():
            continue
        pid = str(p.get("pid", f"p{i + 1}"))
        uid = f"{aid}:{pid}"
        pid2uid[pid] = uid
        props.append({"uid": uid, "aid": aid, "text": norm(str(p["text"])).strip(), "role": p.get("role", "FACT")})
    if mode == "lp" and isinstance(js, dict):
        for e in js.get("edges", []) or []:
            if not isinstance(e, dict):
                bad += 1
                continue
            h, t = pid2uid.get(str(e.get("head"))), pid2uid.get(str(e.get("tail")))
            ty = e.get("type")
            if h and t and h != t and ty in LOGIC_TYPES:
                ptrs.append({"head": h, "tail": t, "type": ty, "cue": e.get("cue", "")})
            else:
                bad += 1
    return {"aid": aid, "props": props, "pointers": ptrs, "bad_edges": bad}


def is_valid_json(js, mode):
    if mode == "lp":
        return isinstance(js, dict) and isinstance(js.get("propositions"), list) and len(js["propositions"]) > 0
    return (isinstance(js, list) and len(js) > 0) or (isinstance(js, dict) and bool(js.get("propositions")))


# =====================================================================
# vLLM Generator & Checkpointed Batch Runner
# =====================================================================
class VLLMGenerator:
    def __init__(self, model=DEFAULT_MODEL, max_model_len=8192, gpu_util=0.90):
        from vllm import LLM
        self.llm = LLM(
            model, dtype="half", max_model_len=max_model_len,
            gpu_memory_utilization=gpu_util, enforce_eager=False, seed=42
        )

    def generate(self, batch_messages, max_tokens=1536, temperature=0.0):
        from vllm import SamplingParams
        sp = SamplingParams(temperature=temperature, max_tokens=max_tokens, seed=42)
        outs = self.llm.chat(batch_messages, sp, use_tqdm=True)
        return [o.outputs[0].text for o in outs]


def run_batched(gen_factory, items, mode, out_path, batch=100, preload_paths=None, deadline=None, temperature=0.0):
    preloaded = {}
    for p in (preload_paths or []):
        if os.path.exists(p) and os.path.abspath(p) != os.path.abspath(out_path):
            for r in read_jsonl(p):
                if "aid" in r and "raw" in r:
                    preloaded[r["aid"]] = r["raw"]
    local_done = set()
    if os.path.exists(out_path):
        for r in read_jsonl(out_path):
            if "aid" in r and "raw" in r:
                local_done.add(r["aid"])
                preloaded[r["aid"]] = r["raw"]

    carry = [{"aid": it["aid"], "raw": preloaded[it["aid"]]}
             for it in items if it["aid"] in preloaded and it["aid"] not in local_done]
    if carry:
        write_jsonl(out_path, carry, mode="a")
        print(f"[resume] Đã kế thừa {len(carry)} Điều từ phiên trước vào {out_path}", flush=True)

    done = set(preloaded.keys())
    todo = [it for it in items if it["aid"] not in done]
    print(f"[run] {len(items) - len(todo)}/{len(items)} đã xong, còn {len(todo)} -> {out_path}", flush=True)
    if not todo:
        return True

    gen = gen_factory()
    t0 = time.time()
    n_done = 0
    completed_all = True
    for i in range(0, len(todo), batch):
        if deadline and time.time() >= deadline:
            print(f"[checkpoint] Chạm mốc thời gian an toàn ({n_done}/{len(todo)}). Dừng sớm để lưu dữ liệu!", flush=True)
            completed_all = False
            break
        chunk = todo[i:i + batch]
        msgs = [build_messages(it["article_content"], mode) for it in chunk]
        raws = gen.generate(msgs, max_tokens=1536, temperature=temperature)
        write_jsonl(out_path, [{"aid": it["aid"], "raw": r} for it, r in zip(chunk, raws)], mode="a")
        n_done += len(chunk)
        print(f"[run] {n_done}/{len(todo)} — {(time.time() - t0) / n_done:.2f} s/item", flush=True)

    if n_done > 0:
        json.dump(
            {"items": n_done, "seconds": round(time.time() - t0, 1), "sec_per_item": round((time.time() - t0) / n_done, 3)},
            open(out_path + ".timing.json", "w", encoding="utf-8"), indent=1
        )
    return completed_all


def find_files(pattern, search_dirs):
    out = []
    for d in search_dirs:
        out += sorted(glob.glob(os.path.join(d, pattern)))
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["lp", "std"], required=True)
    p.add_argument("--shard", type=int, default=0)
    p.add_argument("--num_shards", type=int, default=1)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--batch", type=int, default=100)
    p.add_argument("--deadline_epoch", type=float, default=0.0)
    p.add_argument("--finalize", action="store_true")
    p.add_argument("--work", default="/kaggle/working/work")
    p.add_argument("--inputs", nargs="*", default=[])
    a = p.parse_args()

    os.makedirs(a.work, exist_ok=True)
    search_dirs = [a.work] + list(a.inputs)
    deadline = a.deadline_epoch if a.deadline_epoch > 0 else None

    arts_files = find_files("articles_all.jsonl", search_dirs) or find_files("articles_1000.jsonl", search_dirs)
    if not arts_files:
        raise FileNotFoundError(f"Không tìm thấy articles_all.jsonl hoặc articles_1000.jsonl trong {search_dirs}")
    arts = read_jsonl(arts_files[0])
    for x in arts:
        x["article_content"] = clean_article_raw(x["article_content"])
    by_aid = {x["aid"]: x for x in arts}

    if not a.finalize:
        mine = arts[a.shard::a.num_shards]
        preload = [f for f in find_files(f"raw_{a.mode}_*.jsonl", search_dirs) if not f.endswith("_retry.jsonl")]
        out_path = os.path.join(a.work, f"raw_{a.mode}_{a.shard}.jsonl")
        run_batched(
            lambda: VLLMGenerator(a.model), mine, a.mode, out_path,
            batch=a.batch, preload_paths=preload, deadline=deadline, temperature=0.0
        )
        return

    # Finalize: gộp các shard, retry JSON hỏng ở T=0.3 và xuất props_{mode}.jsonl
    raws = {}
    for f in find_files(f"raw_{a.mode}_*.jsonl", search_dirs):
        if f.endswith("_retry.jsonl"):
            continue
        for r in read_jsonl(f):
            if "aid" in r and "raw" in r:
                raws[r["aid"]] = r["raw"]

    missing = [x for x in arts if x["aid"] not in raws]
    if missing:
        print(f"[checkpoint] Còn {len(missing)}/{len(arts)} Điều ({a.mode}) chưa chạy xong. "
              f"Đã lưu an toàn các file raw_{a.mode}_*.jsonl để chạy tiếp ở phiên sau!", flush=True)
        return

    target_props = os.path.join(a.work, f"props_{a.mode}.jsonl")
    target_stats = os.path.join(a.work, f"stats_props_{a.mode}.json")
    for pf in find_files(f"props_{a.mode}.jsonl", search_dirs):
        if os.path.abspath(pf) != os.path.abspath(target_props):
            prev_recs = read_jsonl(pf)
            if len(prev_recs) == len(arts):
                shutil.copyfile(pf, target_props)
                sf = os.path.join(os.path.dirname(pf), f"stats_props_{a.mode}.json")
                if os.path.exists(sf):
                    shutil.copyfile(sf, target_stats)
                print(f"[resume] Đã kế thừa {len(prev_recs)} Điều hoàn chỉnh từ {pf}", flush=True)
                return

    bad = [by_aid[k] for k, v in raws.items() if k in by_aid and not is_valid_json(parse_llm_json(v), a.mode)]
    retry = {}
    if bad:
        print(f"[retry] {len(bad)} Điều JSON hỏng, thử lại với T=0.3", flush=True)
        retry_out = os.path.join(a.work, f"raw_{a.mode}_retry.jsonl")
        retry_preload = find_files(f"raw_{a.mode}_retry.jsonl", search_dirs)
        ok_retry = run_batched(
            lambda: VLLMGenerator(a.model), bad, a.mode, retry_out,
            batch=a.batch, preload_paths=retry_preload, deadline=deadline, temperature=0.3
        )
        for f in find_files(f"raw_{a.mode}_retry.jsonl", search_dirs):
            for r in read_jsonl(f):
                if "aid" in r and "raw" in r:
                    retry[r["aid"]] = r["raw"]
        if not ok_retry:
            print(f"[checkpoint] Tạm dừng trong lúc retry ({len(retry)}/{len(bad)}). Chạy tiếp ở phiên sau!", flush=True)
            return

    recs, status = [], Counter()
    for x in arts:
        raw = retry.get(x["aid"], raws[x["aid"]])
        js = parse_llm_json(raw)
        if is_valid_json(js, a.mode):
            status["retry_ok" if x["aid"] in retry else "ok"] += 1
        else:
            js = fallback_props(x["article_content"])
            status["fallback"] += 1
        rec = normalize_output(x["aid"], js, a.mode)
        rec["raw"] = raw
        recs.append(rec)

    write_jsonl(target_props, recs)
    st = {
        "mode": a.mode, "articles": len(recs), **status,
        "bad_edges": sum(r["bad_edges"] for r in recs),
        "pointers": sum(len(r["pointers"]) for r in recs),
        "props": sum(len(r["props"]) for r in recs),
    }
    json.dump(st, open(target_stats, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("✅ Hoàn tất finalize:", st, flush=True)


if __name__ == "__main__":
    main()
