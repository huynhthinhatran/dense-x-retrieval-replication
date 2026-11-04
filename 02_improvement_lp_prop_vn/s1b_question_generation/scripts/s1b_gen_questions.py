"""
s1b_gen_questions.py — LP-Prop v2: sinh lại câu hỏi có điều kiện, mỗi câu gắn với MỘT gold span
(quy tắc + điều kiện/ngoại lệ), sao cho muốn trả lời đúng thì bắt buộc phải nêu điều kiện.

Giai đoạn:
  gen    : sinh câu hỏi bằng LLM (vLLM), có checkpoint, chạy lại sẽ làm tiếp phần còn thiếu
  select : kiểm tra tự động + chọn đúng --target câu (mặc định 1.200) cho tập eval

Kiểm tra tự động (mọi câu phải qua hết):
  json_ok          : đọc được JSON, đủ 3 trường
  q_form           : câu hỏi 8–90 từ, kết thúc bằng '?'
  cond_in_answer   : đáp án chứa điều kiện (>=50% cụm 4 từ, hoặc >=70% từ)
  rule_in_answer   : đáp án chứa quy tắc (>=40% từ)
  no_copy          : câu hỏi KHÔNG chép nguyên văn điều kiện (<80% cụm 4 từ)
  ignored_differs  : đáp án "bỏ qua điều kiện" không chứa điều kiện và khác đáp án đúng
  short_answer     : đáp án <= 130 từ

Dùng:
  python s1b_gen_questions.py --stage gen    --data /kaggle/working/data_v2 --out /kaggle/working/questions_v2
  python s1b_gen_questions.py --stage select --data /kaggle/working/data_v2 --out /kaggle/working/questions_v2
"""
import argparse, json, os, random, re, time, unicodedata
from collections import Counter, defaultdict

DEFAULT_MODEL = "Qwen/Qwen2.5-14B-Instruct-AWQ"
STOP = set("của và các là được có cho theo với trong này đó những một người phải thì".split())


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

def phrase_frac(span, text, n=4):
    c, a = toks(span), toks(text)
    if len(c) < n:
        return 1.0 if c and " ".join(c) in " ".join(a) else 0.0
    ag = {tuple(a[i:i + n]) for i in range(len(a) - n + 1)}
    cg = [tuple(c[i:i + n]) for i in range(len(c) - n + 1)]
    return sum(g in ag for g in cg) / len(cg)

def read_jsonl(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for l in f:
            l = l.strip()
            if l:
                try:
                    out.append(json.loads(l))
                except json.JSONDecodeError:
                    pass
    return out

def write_jsonl(path, rows, mode="w"):
    with open(path, mode, encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# ---------------- prompt ----------------
SYS = ("Bạn là chuyên gia pháp luật Việt Nam, soạn câu hỏi kiểm tra việc hiểu ĐIỀU KIỆN áp dụng của quy định pháp luật. "
       "Chỉ trả về đúng một đối tượng JSON, không giải thích.")

EXAMPLE = """VÍ DỤ
VĂN BẢN: Bộ luật Lao động (ví dụ minh hoạ)
QUY TẮC: Người lao động được nghỉ hằng năm 12 ngày làm việc
ĐIỀU KIỆN/NGOẠI LỆ: nếu làm việc đủ 12 tháng cho một người sử dụng lao động
JSON:
{"question": "Theo Bộ luật Lao động, người lao động mới làm việc 8 tháng cho một công ty có được nghỉ hằng năm 12 ngày làm việc không?",
 "answer": "Chưa được hưởng đủ 12 ngày. Theo Bộ luật Lao động, người lao động chỉ được nghỉ hằng năm 12 ngày làm việc nếu đã làm việc đủ 12 tháng cho một người sử dụng lao động.",
 "answer_if_condition_ignored": "Có, người lao động được nghỉ hằng năm 12 ngày làm việc."}
"""

def article_window(text, head, max_words=900):
    w = text.split()
    if len(w) <= max_words:
        return text
    key = " ".join(head.split()[:6])
    pos = text.find(key)
    start_w = len(text[:pos].split()) if pos >= 0 else 0
    s = max(0, start_w - max_words // 3)
    return ("… " if s > 0 else "") + " ".join(w[s:s + max_words]) + " …"

def gen_messages(c):
    user = (
        f"{EXAMPLE}\nBÂY GIỜ LÀM VỚI QUY ĐỊNH SAU\n"
        f"VĂN BẢN: {c['doc_name']}\n"
        f"ĐIỀU LUẬT:\n{article_window(c['article'], c['head'])}\n\n"
        f"QUY TẮC: {c['head']}\n"
        f"ĐIỀU KIỆN/NGOẠI LỆ: {c['condition']}\n\n"
        "Viết MỘT câu hỏi tiếng Việt sao cho muốn trả lời đúng thì BẮT BUỘC phải nêu điều kiện/ngoại lệ trên.\n"
        "Yêu cầu:\n"
        "- Câu hỏi nêu tên văn bản luật để biết đang hỏi luật nào (không cần số Điều).\n"
        "- Câu hỏi hỏi về quy tắc (ai phải/được làm gì, thời hạn, thẩm quyền, trường hợp cụ thể...). "
        "KHÔNG chép nguyên văn điều kiện vào câu hỏi; có thể nêu một tình huống cụ thể mà điều kiện quyết định câu trả lời.\n"
        "- Trả lời mà bỏ qua điều kiện/ngoại lệ thì sẽ sai hoặc khái quát quá mức.\n"
        "- answer: 1–3 câu, nêu quy tắc VÀ nêu rõ điều kiện/ngoại lệ, chỉ dựa vào Điều luật trên.\n"
        "- answer_if_condition_ignored: câu trả lời nghe hợp lý nhưng bỏ mất điều kiện/ngoại lệ.\n"
        'Chỉ trả về JSON: {"question": "...", "answer": "...", "answer_if_condition_ignored": "..."}'
    )
    return [{"role": "system", "content": SYS}, {"role": "user", "content": user}]

def parse_json(raw):
    t = (raw or "").strip()
    t = re.sub(r"^```(?:json)?|```$", "", t, flags=re.M).strip()
    m = re.search(r"\{.*\}", t, flags=re.S)
    if not m:
        return None
    try:
        js = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    if not all(isinstance(js.get(k), str) and js[k].strip() for k in ("question", "answer", "answer_if_condition_ignored")):
        return None
    return {k: js[k].strip() for k in ("question", "answer", "answer_if_condition_ignored")}

def checks(c, js):
    if js is None:
        return {"json_ok": False}
    q, ans, ign = js["question"], js["answer"], js["answer_if_condition_ignored"]
    return {
        "json_ok": True,
        "q_form": 8 <= len(q.split()) <= 90 and q.rstrip().endswith("?"),
        "cond_in_answer": phrase_frac(c["condition"], ans) >= 0.5 or coverage(c["condition"], [ans]) >= 0.7,
        "rule_in_answer": coverage(c["head"], [ans]) >= 0.4,
        "no_copy": phrase_frac(c["condition"], q) < 0.8,
        "ignored_differs": phrase_frac(c["condition"], ign) < 0.5 and norm(ign).strip() != norm(ans).strip(),
        "short_answer": len(ans.split()) <= 130,
    }


# ---------------- generator ----------------
class VLLMGenerator:
    def __init__(self, model, tp=1, max_model_len=6144, gpu_util=0.90):
        from vllm import LLM
        print(f"[vllm] nạp {model} (tensor_parallel={tp})", flush=True)
        self.llm = LLM(model, dtype="half", max_model_len=max_model_len, tensor_parallel_size=tp,
                       gpu_memory_utilization=gpu_util, seed=42)

    def generate(self, msgs, max_tokens=512):
        from vllm import SamplingParams
        sp = SamplingParams(temperature=0.0, max_tokens=max_tokens, seed=42)
        return [o.outputs[0].text for o in self.llm.chat(msgs, sp, use_tqdm=True)]

class MockGenerator:
    def generate(self, msgs, max_tokens=512):
        out = []
        for m in msgs:
            u = m[1]["content"].split("BÂY GIỜ LÀM VỚI QUY ĐỊNH SAU")[1]
            head = re.search(r"QUY TẮC: (.*)", u).group(1); cond = re.search(r"ĐIỀU KIỆN/NGOẠI LỆ: (.*)", u).group(1)
            doc = re.search(r"VĂN BẢN: (.*)", u).group(1)
            out.append(json.dumps({"question": f"Theo {doc}, {head.split(',')[0].lower()} trong những trường hợp nào?",
                                   "answer": f"{head}, {cond}.", "answer_if_condition_ignored": f"{head}."}, ensure_ascii=False))
        return out


# ---------------- ứng viên ----------------
def build_candidates(data, max_candidates, seed):
    arts = {x["aid"]: x for x in read_jsonl(os.path.join(data, "articles_v2.jsonl"))}
    spans = [g for g in read_jsonl(os.path.join(data, "gold_spans.jsonl"))
             if arts.get(g["aid"], {}).get("split") == "eval" and g.get("condition") and g.get("head")]
    by_a = defaultdict(list)
    for g in spans:
        by_a[g["aid"]].append(g)
    rng = random.Random(seed)
    aids = sorted(by_a); rng.shuffle(aids)
    for a in aids:
        rng.shuffle(by_a[a])
    cands, rnd = [], 0
    while len(cands) < max_candidates and any(len(by_a[a]) > rnd for a in aids):
        for a in aids:
            if len(by_a[a]) > rnd and len(cands) < max_candidates:
                g = by_a[a][rnd]; x = arts[a]
                cands.append({"sid": g["sid"], "aid": a, "round": rnd, "type": g["type"], "cue": g.get("cue", ""),
                              "head": g["head"], "condition": g["condition"], "khoan": g.get("khoan"),
                              "doc_name": x["doc_name"], "article": x["article_content"], "has_exc": x.get("has_exc")})
        rnd += 1
    return cands


def stage_gen(a):
    cands = build_candidates(a.data, a.max_candidates, a.seed)
    out = os.path.join(a.out, "gen_raw.jsonl")
    done = {r["sid"] for r in read_jsonl(out) if parse_json(r["raw"]) is not None}
    todo = [c for c in cands if c["sid"] not in done]
    print(f"[gen] {len(cands)} ứng viên, còn {len(todo)} cần sinh -> {out}", flush=True)
    if not todo:
        return True
    gen = MockGenerator() if a.mock else VLLMGenerator(a.model, a.tp)
    deadline = time.time() + a.deadline_min * 60 if a.deadline_min else None
    t0 = time.time()
    for i in range(0, len(todo), a.batch):
        if deadline and time.time() > deadline:
            print("[checkpoint] chạm deadline, dừng để lưu"); return False
        chunk = todo[i:i + a.batch]
        raws = gen.generate([gen_messages(c) for c in chunk])
        write_jsonl(out, [{"sid": c["sid"], "raw": r} for c, r in zip(chunk, raws)], mode="a")
        n = i + len(chunk)
        print(f"[gen] {n}/{len(todo)} — {(time.time() - t0) / n:.2f} s/câu", flush=True)
    return True


def stage_select(a):
    cands = {c["sid"]: c for c in build_candidates(a.data, a.max_candidates, a.seed)}
    raw = {}
    for r in read_jsonl(os.path.join(a.out, "gen_raw.jsonl")):
        if r["sid"] in cands and (r["sid"] not in raw or parse_json(raw[r["sid"]]) is None):
            raw[r["sid"]] = r["raw"]
    rows, fail = [], Counter()
    for sid, c in cands.items():
        if sid not in raw:
            fail["not_generated"] += 1; continue
        js = parse_json(raw[sid]); ck = checks(c, js)
        bad = [k for k, v in ck.items() if not v]
        for k in bad:
            fail[k] += 1
        if bad:
            continue
        rows.append({"c": c, "js": js})
    # chọn: ưu tiên vòng 0 (mỗi Điều 1 câu), rồi mới tới vòng sau
    rng = random.Random(a.seed)
    rows.sort(key=lambda r: r["c"]["sid"]); rng.shuffle(rows)
    rows.sort(key=lambda r: r["c"]["round"])
    chosen = rows[:a.target]
    per_aid = Counter()
    out = []
    for r in rows:
        c, js = r["c"], r["js"]
        k = per_aid[c["aid"]]; per_aid[c["aid"]] += 1
        out.append({"qid": f"{c['aid']}:c{k}", "aid": c["aid"], "sid": c["sid"], "split": "eval", "has_exc": c["has_exc"],
                    "question": js["question"], "answer": js["answer"], "answer_if_condition_ignored": js["answer_if_condition_ignored"],
                    "difficulty": "n/a", "question_type": "conditional", "is_conditional": True,
                    "condition_type": c["type"], "condition_cue": c["cue"], "head": c["head"],
                    "condition": c["condition"], "condition_needed": c["condition"], "gen_round": c["round"]})
    chosen_sids = {r["c"]["sid"] for r in chosen}
    sel = [q for q in out if q["sid"] in chosen_sids]
    write_jsonl(os.path.join(a.out, "cond_questions_v2_all_valid.jsonl"), out)
    write_jsonl(os.path.join(a.out, f"cond_questions_v2_eval_{a.target}.jsonl"), sel)
    n_gen = len(cands) - fail["not_generated"]
    stats = {"candidates": len(cands), "generated": n_gen, "valid": len(out), "selected": len(sel),
             "pass_rate": round(len(out) / max(n_gen, 1), 4), "fail_counts": dict(fail),
             "selected_types": dict(Counter(q["condition_type"] for q in sel)),
             "selected_rounds": dict(Counter(q["gen_round"] for q in sel)),
             "selected_articles": len({q["aid"] for q in sel}), "target_met": len(sel) >= a.target}
    json.dump(stats, open(os.path.join(a.out, "gen_stats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # 20 câu mẫu để đọc nhanh
    L = ["# 20 câu hỏi mẫu (LP-Prop v2)", ""]
    for q in random.Random(1).sample(sel, min(20, len(sel))):
        L += [f"**{q['qid']}** ({q['condition_type']})", f"- Hỏi: {q['question']}", f"- Đáp án: {q['answer']}",
              f"- Bỏ điều kiện: {q['answer_if_condition_ignored']}", f"- Điều kiện gốc: _{q['condition']}_", ""]
    open(os.path.join(a.out, "sample_questions.md"), "w", encoding="utf-8").write("\n".join(L))
    print(json.dumps(stats, ensure_ascii=False, indent=1))
    if not stats["target_met"]:
        print(f"[!] chỉ có {len(sel)} câu hợp lệ < {a.target}: tăng --max_candidates rồi chạy lại --stage gen và select")
    return stats["target_met"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["gen", "select"], required=True)
    ap.add_argument("--data", default="/kaggle/working/data_v2")
    ap.add_argument("--out", default="/kaggle/working/questions_v2")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--tp", type=int, default=2)
    ap.add_argument("--target", type=int, default=1200)
    ap.add_argument("--max_candidates", type=int, default=2400)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--deadline_min", type=float, default=0)
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    ok = stage_gen(a) if a.stage == "gen" else stage_select(a)
    print("[done]" if ok else "[chưa xong]")


if __name__ == "__main__":
    main()
