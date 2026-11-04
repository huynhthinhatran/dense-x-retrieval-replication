"""
s5_reader_judge.py — Tầng 3: Reader + LLM-judge cho LP-Prop (bộ 1.200 câu cond, split=eval).

Đầu vào (đọc từ --root, thường là /kaggle/input):
  - cond_questions_eval_1200.jsonl      (S2 / work_clean)
  - contexts_{system}_B{budget}.jsonl   (S3 / work_s3)
  - articles_all.jsonl                  (D1, chỉ dùng cho hệ "oracle")

3 giai đoạn (--stage):
  reader    : sinh câu trả lời từ ngữ cảnh của từng hệ × budget
  judge     : chấm từng câu trả lời so với đáp án chuẩn (JSON: correct / condition_kept / overgeneralized)
  aggregate : gộp các shard, tính chỉ số + paired bootstrap -> results/s5_results.json, s5_tables.md

Có checkpoint: chạy lại lệnh cũ sẽ tự bỏ qua mục đã xong. Chia 2 GPU bằng --shard 0/1 --num_shards 2.

Ví dụ trên Kaggle (2×T4):
  CUDA_VISIBLE_DEVICES=0 python s5_reader_judge.py --stage reader --shard 0 --num_shards 2 &
  CUDA_VISIBLE_DEVICES=1 python s5_reader_judge.py --stage reader --shard 1 --num_shards 2 &
  wait
  (tương tự cho --stage judge), rồi: python s5_reader_judge.py --stage aggregate
"""
import argparse, glob, json, os, random, re, time, unicodedata, zlib
from collections import defaultdict

DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct-AWQ"   # cùng model với s2
DEFAULT_SYSTEMS = ["passage", "std", "lp_noptr", "lp_out", "lp"]
ABLATION_SYSTEMS = ["std_raw", "lp_raw", "lp_edge_only"]
ORDER = ["oracle", "passage", "std_raw", "std", "lp_noptr", "lp_out", "lp_raw", "lp_edge_only", "lp"]
STOP = set("của và các là được có cho theo với trong này đó những một người phải thì".split())
ABSTAIN_PAT = re.compile(r"không đủ thông tin|không có thông tin|ngữ cảnh không (đề cập|cung cấp)", re.I)


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

def phrase_hit(span, text, n=4, frac=0.5):
    """Điều kiện xuất hiện theo CỤM từ liền nhau (n-gram) trong câu trả lời -> chặt hơn so khớp túi từ."""
    c, a = toks(span), toks(text)
    if len(c) < n:
        return coverage(span, [text]) >= 0.9 and " ".join(c) in " ".join(a)
    ag = {tuple(a[i:i + n]) for i in range(len(a) - n + 1)}
    cg = [tuple(c[i:i + n]) for i in range(len(c) - n + 1)]
    return sum(g in ag for g in cg) / len(cg) >= frac

def read_jsonl(path):
    out = []
    if not path or not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for l in f:
            l = l.strip()
            if l:
                try:
                    out.append(json.loads(l))
                except json.JSONDecodeError:
                    continue
    return out

def append_jsonl(path, rows):
    with open(path, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def find(root, name, prefer=None):
    hits = sorted(glob.glob(os.path.join(root, "**", name), recursive=True))
    if not hits:
        return None
    if prefer:
        pref = [h for h in hits if prefer in h]
        if pref:
            return pref[0]
    return hits[0]

def shard_of(key, n):
    return zlib.crc32(key.encode("utf-8")) % n

mean = lambda xs: sum(xs) / len(xs) if xs else float("nan")
pct = lambda x: "–" if x != x else f"{100 * x:.1f}"


# ---------------- prompt ----------------
READER_SYS = (
    "Bạn là trợ lý pháp lý tiếng Việt. Chỉ dựa vào các đoạn NGỮ CẢNH được cung cấp để trả lời, "
    "không dùng kiến thức bên ngoài. Trả lời ngắn gọn, tối đa khoảng 150 từ. "
    "Nếu quy định có điều kiện, ngoại lệ, giới hạn hoặc trường hợp không áp dụng thì phải nêu rõ. "
    "Nếu ngữ cảnh không đủ để trả lời, hãy nói: \"Không đủ thông tin trong ngữ cảnh.\""
)

def reader_messages(question, units):
    if units:
        ctx = "\n".join(f"[{i + 1}] {u['text']}" for i, u in enumerate(units))
    else:
        ctx = "(trống)"
    user = f"NGỮ CẢNH:\n{ctx}\n\nCÂU HỎI: {question}\n\nTRẢ LỜI:"
    return [{"role": "system", "content": READER_SYS}, {"role": "user", "content": user}]

JUDGE_SYS = (
    "You are a strict but fair grader for Vietnamese legal question answering. "
    "Read carefully, reason briefly, then output a JSON object on the last line."
)

def judge_messages(q, answer):
    """Lượt 1 (main): chỉ chấm correct + rule_stated."""
    user = (
        f"QUESTION (Vietnamese):\n{q['question']}\n\n"
        f"REFERENCE ANSWER:\n{q['answer']}\n\n"
        f"CANDIDATE ANSWER:\n{answer}\n\n"
        f"LEGAL RULE: {q['head']}\n\n"
        "Answer two yes/no checks about the CANDIDATE ANSWER:\n"
        "1. correct: Does it give the same core answer to the QUESTION as the REFERENCE ANSWER, without contradicting it? "
        "Missing minor details is fine. Saying there is not enough information = 0.\n"
        "2. rule_stated: Does it state or apply the LEGAL RULE above (paraphrase is fine)?\n\n"
        "Write at most 2 short lines of reasoning, then on the LAST line output only:\n"
        '{"correct": <0 or 1>, "rule_stated": <0 or 1>}'
    )
    return [{"role": "system", "content": JUDGE_SYS}, {"role": "user", "content": user}]

COND_SYS = (
    "Bạn là người kiểm tra văn bản pháp luật tiếng Việt, làm việc cẩn thận và khách quan. "
    "Nhiệm vụ: xác định CÂU TRẢ LỜI có nêu ĐIỀU KIỆN/NGOẠI LỆ đã cho hay không."
)

COND_FEWSHOT = """Quy tắc chấm:
- Chấm 1 nếu câu trả lời nêu điều kiện/ngoại lệ đó, nguyên văn HOẶC diễn đạt lại cùng ý (đổi từ, đổi thứ tự, rút gọn hợp lý đều được).
- Chấm 0 nếu câu trả lời không nhắc tới điều kiện đó, chỉ nêu quy tắc chung, nêu một điều kiện KHÁC, hoặc nói không đủ thông tin.
Cách làm: trước hết chép lại ĐÚNG đoạn trong câu trả lời thể hiện điều kiện (hoặc ghi KHÔNG CÓ), rồi kết luận.

Ví dụ 1
QUY TẮC: Người lao động được nghỉ hằng năm 12 ngày làm việc
ĐIỀU KIỆN: nếu làm việc đủ 12 tháng cho một người sử dụng lao động
CÂU TRẢ LỜI: Người lao động làm việc đủ 12 tháng cho một người sử dụng lao động thì được nghỉ 12 ngày phép năm.
TRÍCH: "làm việc đủ 12 tháng cho một người sử dụng lao động thì được nghỉ"
KẾT LUẬN: 1

Ví dụ 2
QUY TẮC: Tổ chức tín dụng phải niêm yết công khai lãi suất
ĐIỀU KIỆN: trừ trường hợp quy định tại khoản 3 Điều này
CÂU TRẢ LỜI: Tổ chức tín dụng phải công khai lãi suất, ngoại trừ các trường hợp nêu tại khoản 3.
TRÍCH: "ngoại trừ các trường hợp nêu tại khoản 3"
KẾT LUẬN: 1

Ví dụ 3
QUY TẮC: Người nộp thuế được gia hạn nộp thuế
ĐIỀU KIỆN: trong trường hợp bị thiệt hại vật chất do thiên tai, hỏa hoạn
CÂU TRẢ LỜI: Người nộp thuế được gia hạn nộp thuế theo quy định của Luật Quản lý thuế, thời gian gia hạn tối đa 2 năm.
TRÍCH: KHÔNG CÓ
KẾT LUẬN: 0

Ví dụ 4
QUY TẮC: Doanh nghiệp phải thông báo cho cơ quan đăng ký kinh doanh
ĐIỀU KIỆN: nếu thay đổi người đại diện theo pháp luật
CÂU TRẢ LỜI: Không đủ thông tin trong ngữ cảnh.
TRÍCH: KHÔNG CÓ
KẾT LUẬN: 0
"""

def cond_messages(q, answer):
    """Lượt 2 (cond) v4: few-shot, bắt trích dẫn trước rồi mới kết luận."""
    user = (
        COND_FEWSHOT +
        "\nBây giờ chấm trường hợp sau. Trả lời đúng 2 dòng TRÍCH và KẾT LUẬN như ví dụ.\n"
        f"QUY TẮC: {q['head']}\n"
        f"ĐIỀU KIỆN: {q['condition']}\n"
        f"CÂU TRẢ LỜI: {answer}\n"
    )
    return [{"role": "system", "content": COND_SYS}, {"role": "user", "content": user}]

def parse_main(raw):
    for m in reversed(list(re.finditer(r"\{[^{}]*\}", raw or ""))):
        d = {k: re.search(rf'"?{k}"?\s*:\s*"?([01])', m.group(0)) for k in ("correct", "rule_stated")}
        if all(d.values()):
            return {k: int(v.group(1)) for k, v in d.items()}
    return None

def parse_cond(raw):
    t = (raw or "").strip()
    m = list(re.finditer(r"KẾT?\s*LUẬN\s*[:：]\s*\**\s*([01])", t, flags=re.I))
    if m:
        return int(m[-1].group(1))
    if t[:1] in ("0", "1") and (len(t) == 1 or not t[1].isdigit()):
        return int(t[0])
    m = re.findall(r"(?m)^\s*([01])\s*$", t)
    return int(m[-1]) if m else None

def merge_judge(main, cond):
    if main is None or cond is None:
        return None
    return {"correct": main["correct"], "rule_stated": main["rule_stated"], "condition_kept": cond,
            "overgeneralized": int(main["rule_stated"] and not cond)}


# ---------------- generator ----------------
def hf_login():
    """Model gated trên Hugging Face: lấy token từ biến môi trường HF_TOKEN hoặc Kaggle Secrets (tên HF_TOKEN)."""
    tok = os.environ.get("HF_TOKEN")
    if not tok:
        try:
            from kaggle_secrets import UserSecretsClient
            tok = UserSecretsClient().get_secret("HF_TOKEN")
        except Exception:
            tok = None
    if tok:
        os.environ["HF_TOKEN"] = tok
        os.environ["HUGGING_FACE_HUB_TOKEN"] = tok
        print("[hf] đã nạp HF_TOKEN")
    else:
        print("[hf] không có HF_TOKEN — chỉ tải được model công khai")

class VLLMGenerator:
    def __init__(self, model, max_model_len=6144, gpu_util=0.90, tp=1):
        hf_login()
        from vllm import LLM
        print(f"[vllm] nạp {model} (tensor_parallel={tp})")
        self.llm = LLM(model, dtype="half", max_model_len=max_model_len, tensor_parallel_size=tp,
                       gpu_memory_utilization=gpu_util, enforce_eager=False, seed=42)

    def generate(self, batch_messages, max_tokens, temperature=0.0):
        from vllm import SamplingParams
        sp = SamplingParams(temperature=temperature, max_tokens=max_tokens, seed=42)
        outs = self.llm.chat(batch_messages, sp, use_tqdm=True)
        return [o.outputs[0].text for o in outs]

class MockGenerator:
    """--mock: chạy thử pipeline không cần GPU."""
    def generate(self, batch_messages, max_tokens, temperature=0.0):
        rng = random.Random(len(batch_messages))
        outs = []
        for m in batch_messages:
            if m[0]["content"].startswith("Bạn là người kiểm tra"):
                outs.append(f'TRÍCH: KHÔNG CÓ\nKẾT LUẬN: {rng.randint(0, 1)}')
            elif m[0]["content"].startswith("You are a strict"):
                outs.append("lý do...\n" + json.dumps({k: rng.randint(0, 1) for k in ("correct", "rule_stated")}))
            else:
                ctx = m[1]["content"].split("CÂU HỎI:")[0]
                outs.append(ctx[-300:])
        return outs


def run_batched(gen_factory, todo, build, max_tokens, out_path, key_fields, batch, deadline):
    if not todo:
        print(f"[run] không còn mục nào -> {out_path}"); return True
    gen = gen_factory()
    t0, n = time.time(), 0
    for i in range(0, len(todo), batch):
        if deadline and time.time() >= deadline:
            print(f"[checkpoint] chạm deadline sau {n}/{len(todo)} mục, dừng để lưu."); return False
        chunk = todo[i:i + batch]
        raws = gen.generate([build(it) for it in chunk], max_tokens=max_tokens)
        append_jsonl(out_path, [dict({k: it[k] for k in key_fields}, raw=r) for it, r in zip(chunk, raws)])
        n += len(chunk)
        print(f"[run] {n}/{len(todo)} — {(time.time() - t0) / n:.2f} s/mục", flush=True)
    return True


# ---------------- nạp dữ liệu ----------------
def load(a):
    cond_path = a.cond_file or find(a.root, "cond_questions_eval_1200.jsonl")
    assert cond_path and os.path.exists(cond_path), "Không thấy file câu hỏi cond (--cond_file)"
    qs = [q for q in read_jsonl(cond_path) if q.get("split", "eval") == "eval"]
    if a.limit:
        qs = qs[:a.limit]
    qmap = {q["qid"]: q for q in qs}
    print(f"[data] {len(qs)} câu cond từ {cond_path}")

    systems = list(a.systems) + (ABLATION_SYSTEMS if a.ablation else [])
    items = []
    seen = set()
    for s in systems:
        for B in a.budgets:
            cf = find(a.contexts_dir or a.root, f"contexts_{s}_B{B}.jsonl")
            if not cf:
                print(f"[!] thiếu contexts_{s}_B{B}.jsonl — bỏ qua"); continue
            got = 0
            for r in read_jsonl(cf):
                # contexts của s3 có thể chứa cùng qid 2 lần (bản cond + bản generic, nội dung như nhau) -> lấy 1
                if r["qid"] in qmap and f"{s}|B{B}|{r['qid']}" not in seen:
                    seen.add(f"{s}|B{B}|{r['qid']}")
                    items.append({"key": f"{s}|B{B}|{r['qid']}", "system": s, "budget": B,
                                  "qid": r["qid"], "units": r["units"]})
                    got += 1
            print(f"[data] {s} B{B}: {got} câu")
    if a.oracle:
        arts = {x["aid"]: x for x in read_jsonl(a.articles_file or find(a.root, "articles_all.jsonl") or find(a.root, "articles_1000.jsonl"))}
        for q in qs:
            txt = " ".join(arts[q["aid"]]["article_content"].split()[:a.oracle_words])
            items.append({"key": f"oracle|full|{q['qid']}", "system": "oracle", "budget": "full",
                          "qid": q["qid"], "units": [{"aid": q["aid"], "text": txt}]})
        print(f"[data] oracle (Điều gốc, ≤{a.oracle_words} từ): {len(qs)} câu")
    return qmap, items


# ---------------- các giai đoạn ----------------
def stage_reader(a, qmap, items, gen_factory, deadline):
    out = os.path.join(a.work, f"reader.shard{a.shard}.jsonl")
    done = {r["key"] for p in glob.glob(os.path.join(a.work, "reader.shard*.jsonl")) for r in read_jsonl(p)}
    todo = [it for it in items if shard_of(it["key"], a.num_shards) == a.shard and it["key"] not in done]
    print(f"[reader] shard {a.shard}/{a.num_shards}: còn {len(todo)} mục")
    return run_batched(gen_factory, todo, lambda it: reader_messages(qmap[it["qid"]]["question"], it["units"]),
                       a.reader_max_tokens, out, ["key", "system", "budget", "qid"], a.batch, deadline)

def judge_files(a):
    return sorted(glob.glob(os.path.join(a.work, f"judge_{a.judge_tag}.shard*.jsonl")))

def stage_judge(a, qmap, gen_factory, deadline):
    answers = {r["key"]: r for p in glob.glob(os.path.join(a.work, "reader.shard*.jsonl")) for r in read_jsonl(p)}
    out = os.path.join(a.work, f"judge_{a.judge_tag}.shard{a.shard}.jsonl")
    done = set()
    for p in judge_files(a):
        for r in read_jsonl(p):
            ok = parse_cond(r["raw"]) is not None if r["key"].endswith("#c") else parse_main(r["raw"]) is not None
            if ok:
                done.add(r["key"])
    todo = []
    for k, r in answers.items():
        if r["qid"] not in qmap or shard_of(k, a.num_shards) != a.shard:
            continue
        if k not in done:
            todo.append(dict(r, task="main"))
        if a.cond_source == "judge" and k + "#c" not in done:
            todo.append(dict(r, key=k + "#c", task="cond"))
    print(f"[judge] shard {a.shard}/{a.num_shards}: còn {len(todo)} lượt chấm (trên {len(answers)} câu trả lời)")
    build = lambda it: (judge_messages if it["task"] == "main" else cond_messages)(qmap[it["qid"]], it["raw"])
    return run_batched(gen_factory, todo, build, 256, out, ["key", "system", "budget", "qid"], a.batch, deadline)

def bootstrap_diff(x, y, iters=1000, seed=0):
    rng = random.Random(seed); n = len(x)
    if n == 0:
        return 0.0, 0.0, 0.0
    ds = []
    for _ in range(iters):
        idx = [rng.randrange(n) for _ in range(n)]
        ds.append(sum(x[i] - y[i] for i in idx) / n)
    ds.sort()
    return sum(p - q for p, q in zip(x, y)) / n, ds[int(.025 * iters)], ds[int(.975 * iters) - 1]

def stage_aggregate(a, qmap):
    answers = {r["key"]: r for p in glob.glob(os.path.join(a.work, "reader.shard*.jsonl")) for r in read_jsonl(p)}
    mains, conds = {}, {}
    for p in judge_files(a):
        for r in read_jsonl(p):
            if r["key"].endswith("#c"):
                v = parse_cond(r["raw"])
                if v is not None or r["key"][:-2] not in conds:
                    conds[r["key"][:-2]] = v
            else:
                v = parse_main(r["raw"])
                if v is not None or r["key"] not in mains:
                    mains[r["key"]] = v
    if a.cond_source == "phrase":   # mặc định: 'giữ điều kiện' đo bằng so khớp cụm từ (không dùng LLM)
        conds = {k: int(phrase_hit(qmap[r["qid"]]["condition"], r["raw"]) and not ABSTAIN_PAT.search(r["raw"]))
                 for k, r in answers.items() if r["qid"] in qmap}
    judged = {k: merge_judge(mains.get(k), conds.get(k)) for k in answers}

    per = defaultdict(dict)   # (system, budget) -> qid -> metrics
    n_fail = defaultdict(int)
    for k, r in answers.items():
        q = qmap.get(r["qid"])
        if q is None:
            continue
        ans = r["raw"]
        m = {"abstain": float(bool(ABSTAIN_PAT.search(ans))),
             "cond_cov_lex": float(coverage(q["condition"], [ans]) >= 0.6),
             "cond_phrase": float(phrase_hit(q["condition"], ans) and not ABSTAIN_PAT.search(ans))}
        j = judged.get(k)
        if j is None:
            n_fail[(r["system"], str(r["budget"]))] += 1
        else:
            m.update({"correct": float(j["correct"]), "condition_kept": float(j["condition_kept"]),
                      "cond_acc": float(j["correct"] and j["condition_kept"]),
                      "overgeneralized": float(j["overgeneralized"])})
        per[(r["system"], str(r["budget"]))][r["qid"]] = m

    cols = ["correct", "condition_kept", "cond_acc", "overgeneralized", "abstain", "cond_cov_lex", "cond_phrase"]
    # câu "cần điều kiện": điều kiện thật sự xuất hiện trong đáp án chuẩn (874/1200 ở bộ hiện tại)
    relevant = {k for k, q in qmap.items() if coverage(q["condition"], [q["answer"]]) >= 0.6}
    # kiểm tra độ tin cậy của judge: câu trả lời chứa gần nguyên văn điều kiện -> judge phải chấm kept=1
    # Kiểm tra độ tin cậy của judge (chỉ có ý nghĩa khi --cond_source judge)
    jud = [(k, r) for k, r in answers.items() if r["qid"] in qmap and judged.get(k) and not ABSTAIN_PAT.search(r["raw"])]
    pos = [k for k, r in jud if phrase_hit(qmap[r["qid"]]["condition"], r["raw"], frac=0.8)]      # điều kiện gần nguyên văn
    neg = [k for k, r in jud if coverage(qmap[r["qid"]]["condition"], [r["raw"]]) < 0.2]          # gần như không có điều kiện
    abst = [k for k, r in answers.items() if r["qid"] in qmap and judged.get(k) and ABSTAIN_PAT.search(r["raw"])]
    pos_rate = mean([float(judged[k]["condition_kept"]) for k in pos])
    neg_rate = mean([float(judged[k]["condition_kept"]) for k in neg])
    abst_correct = mean([float(judged[k]["correct"]) for k in abst])
    sanity_pass = (pos_rate == pos_rate and pos_rate >= 0.85) and (neg_rate == neg_rate and neg_rate <= 0.15)
    verb, sanity = pos, pos_rate
    res = {"reader_model": a.model, "judge_model": a.judge_model, "judge_tag": a.judge_tag,
           "n_questions": len(qmap), "n_condition_relevant": len(relevant),
           "judge_sanity": {"cond_source": a.cond_source,
                            "pos_n": len(pos), "pos_kept_rate": pos_rate,
                            "neg_n": len(neg), "neg_kept_rate": neg_rate,
                            "abstain_n": len(abst), "abstain_judged_correct": abst_correct,
                            "pass": bool(sanity_pass)},
           "table": {}, "table_relevant": {}, "significance": {}}
    for (s, B), d in per.items():
        row = {c: mean([m[c] for m in d.values() if c in m]) for c in cols}
        row.update({"n": len(d), "n_judge_fail": n_fail[(s, B)]})
        res["table"][f"{s}|B{B}"] = row
        dr = {k: m for k, m in d.items() if k in relevant}
        rr = {c: mean([m[c] for m in dr.values() if c in m]) for c in cols}
        rr.update({"n": len(dr), "n_judge_fail": 0})
        res["table_relevant"][f"{s}|B{B}"] = rr

    for metric in ["cond_acc", "correct", "overgeneralized", "cond_cov_lex", "cond_phrase"]:
        for (s, B), d in per.items():
            if s == "lp" or s == "oracle" or ("lp", B) not in per:
                continue
            L = per[("lp", B)]
            ks = sorted(k for k in set(L) & set(d) if metric in L[k] and metric in d[k])
            if ks:
                dlt, lo, hi = bootstrap_diff([L[k][metric] for k in ks], [d[k][metric] for k in ks], a.iters)
                res["significance"][f"{metric}@B{B}: lp - {s}"] = {"diff": dlt, "ci95": [lo, hi], "n": len(ks),
                                                                   "significant": not (lo <= 0 <= hi)}

    out_dir = os.path.join(a.work, a.results_dir); os.makedirs(out_dir, exist_ok=True)
    json.dump(res, open(os.path.join(out_dir, "s5_results.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    names = {"correct": "Accuracy", "condition_kept": "Cond. kept", "cond_acc": "Cond-Acc",
             "overgeneralized": "Over-general", "abstain": "Abstain", "cond_cov_lex": "CondCov (từ)", "cond_phrase": "CondCov (cụm)"}
    def render(tbl, title):
        out = [title, "", "| Hệ | Budget | " + " | ".join(names[c] for c in cols) + " | n | judge lỗi |", "|---" * (len(cols) + 4) + "|"]
        ks = sorted(tbl, key=lambda k: (str(k.split("|")[1]), ORDER.index(k.split("|")[0]) if k.split("|")[0] in ORDER else 99))
        for k in ks:
            s_, B_ = k.split("|"); r = tbl[k]
            out.append(f"| {s_} | {B_} | " + " | ".join(pct(r[c]) for c in cols) + f" | {r['n']} | {r['n_judge_fail']} |")
        return out + [""]
    if a.cond_source == "phrase":
        note = ("- 'Giữ điều kiện' (và Cond-Acc, Over-general) đo bằng so khớp cụm từ liền nhau giữa điều kiện và câu trả lời, "
                "không dùng LLM. Judge chỉ chấm 'Accuracy' (đúng/sai) và 'có nêu quy tắc'.")
    else:
        note = (f"- Kiểm tra judge ({'ĐẠT' if sanity_pass else 'CHƯA ĐẠT'}): "
                f"ca dương — {len(pos)} câu trả lời chứa ≥80% cụm từ của điều kiện, judge chấm 'có' = **{pct(pos_rate)}%** (cần ≥ 85%); "
                f"ca âm — {len(neg)} câu trả lời gần như không có điều kiện, judge chấm 'có' = **{pct(neg_rate)}%** (cần ≤ 15%); "
                f"câu trả lời 'không đủ thông tin' bị chấm đúng = {pct(abst_correct)}% (nên ≈ 0%).")
    L = [f"# Tầng 3 — Reader: {a.model} | Judge: {a.judge_model} ({a.judge_tag})", "", note, ""]
    L += render(res["table"], f"## Toàn bộ {len(qmap)} câu cond (%)")
    L += render(res["table_relevant"], f"## {len(relevant)} câu mà điều kiện xuất hiện trong đáp án chuẩn (%)")
    if res["significance"]:
        L += ["", f"## Paired Bootstrap ({a.iters} lần)", "", "| So sánh | Chênh lệch (điểm %) | CI 95% | n | Có ý nghĩa |", "|---|---|---|---|---|"]
        for name, d in res["significance"].items():
            L.append(f"| {name} | {100 * d['diff']:+.2f} | [{100 * d['ci95'][0]:+.2f}, {100 * d['ci95'][1]:+.2f}] | {d['n']} | {'✓' if d['significant'] else ''} |")
    md = "\n".join(L) + "\n"
    open(os.path.join(out_dir, "s5_tables.md"), "w", encoding="utf-8").write(md)
    print(md)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["reader", "judge", "aggregate"], required=True)
    ap.add_argument("--root", default="/kaggle/input")
    ap.add_argument("--work", default="/kaggle/working/work_s5")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="model reader")
    ap.add_argument("--judge_model", default=None, help="model judge (mặc định = --model)")
    ap.add_argument("--cond_source", choices=["phrase", "judge"], default="phrase",
                    help="phrase: đo 'giữ điều kiện' bằng so khớp cụm từ (mặc định); judge: dùng LLM")
    ap.add_argument("--cond_file", default=None, help="v2: đường dẫn file câu hỏi cond")
    ap.add_argument("--contexts_dir", default=None, help="v2: thư mục contexts_* của s3_v2")
    ap.add_argument("--articles_file", default=None, help="v2: articles_v2.jsonl (cho hệ oracle)")
    ap.add_argument("--results_dir", default="results", help="thư mục con trong --work để ghi bảng kết quả")
    ap.add_argument("--judge_tag", default="v4", help="tên phiên bản judge (file judge_<tag>.shard*.jsonl)")
    ap.add_argument("--tp", type=int, default=1, help="tensor parallel; =2 nếu model không vừa 1 T4 (khi đó dùng --num_shards 1)")
    ap.add_argument("--max_model_len", type=int, default=6144)
    ap.add_argument("--systems", nargs="+", default=DEFAULT_SYSTEMS)
    ap.add_argument("--ablation", action="store_true", help="chạy thêm std_raw, lp_raw, lp_edge_only")
    ap.add_argument("--budgets", type=int, nargs="+", default=[100, 500])
    ap.add_argument("--oracle", action="store_true", default=True)
    ap.add_argument("--no_oracle", dest="oracle", action="store_false")
    ap.add_argument("--oracle_words", type=int, default=1500)
    ap.add_argument("--reader_max_tokens", type=int, default=384)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--num_shards", type=int, default=1)
    ap.add_argument("--deadline_min", type=float, default=0, help="dừng an toàn sau N phút (0 = không giới hạn)")
    ap.add_argument("--limit", type=int, default=0, help="chỉ lấy N câu đầu để chạy thử")
    ap.add_argument("--iters", type=int, default=1000)
    ap.add_argument("--mock", action="store_true", help="chạy thử không cần GPU")
    a = ap.parse_args()
    os.makedirs(a.work, exist_ok=True)

    qmap, items = load(a)
    deadline = time.time() + a.deadline_min * 60 if a.deadline_min else None
    a.judge_model = a.judge_model or a.model
    use = a.judge_model if a.stage == "judge" else a.model
    gen_factory = (lambda: MockGenerator()) if a.mock else (lambda: VLLMGenerator(use, a.max_model_len, tp=a.tp))

    if a.stage == "reader":
        ok = stage_reader(a, qmap, items, gen_factory, deadline)
    elif a.stage == "judge":
        ok = stage_judge(a, qmap, gen_factory, deadline)
    else:
        stage_aggregate(a, qmap); ok = True
    print("[done]" if ok else "[chưa xong — chạy lại cùng lệnh để tiếp tục]")


if __name__ == "__main__":
    main()
