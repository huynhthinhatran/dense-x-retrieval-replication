"""Stage 2 Post-processing: Rule-based Pointer Refinement and Proposition Repair (§4.2).

Builds the cleaned proposition variants (`props_lp_edge_only.jsonl`, `props_lp.jsonl`,
and `props_std.jsonl`) from raw propositionizer outputs (`props_lp_raw.jsonl`,
`props_std_raw.jsonl`) and cleaned articles (`articles_v2.jsonl`).

Note: This script operates strictly on `articles_v2.jsonl` and raw propositionizer
outputs; it never reads `gold_spans.jsonl`.
"""
import argparse
import json
import os
import re
import unicodedata
from collections import Counter

# =====================================================================
# 1. Legal Condition Cue Lexicon & Clause Splitting Helpers
# =====================================================================
CUES = {
    "TRỪ_TRƯỜNG_HỢP": [
        "trừ trường hợp quy định tại", "trừ trường hợp luật có quy định khác",
        "trừ trường hợp các bên có thỏa thuận khác", "ngoại trừ trường hợp",
        "ngoại trừ các trường hợp", "trừ trường hợp", "trừ khi",
        "ngoại trừ", "trừ các trường hợp", "trừ những trường hợp", "trừ phi",
    ],
    "KHÔNG_ÁP_DỤNG": [
        "không áp dụng đối với", "không áp dụng trong trường hợp", "không bao gồm",
    ],
    "VỚI_ĐIỀU_KIỆN": [
        "khi có đủ các điều kiện sau", "phải đáp ứng các điều kiện sau",
        "với điều kiện là", "chỉ khi", "trong trường hợp", "trường hợp", "nếu",
    ],
    "NHƯNG_PHẢI": ["nhưng không được", "nhưng không quá", "nhưng phải", "song phải"],
    "GIỚI_HẠN": ["không quá", "tối đa", "tối thiểu", "ít nhất", "chậm nhất là"],
    "HIỆU_LỰC": ["có hiệu lực từ", "hết hiệu lực", "bị bãi bỏ", "được thay thế bởi", "chấm dứt khi"],
    "DẪN_CHIẾU": ["theo quy định tại", "quy định tại khoản"],
}
STRONG = ["TRỪ_TRƯỜNG_HỢP", "KHÔNG_ÁP_DỤNG", "VỚI_ĐIỀU_KIỆN", "NHƯNG_PHẢI"]
LOGIC_TYPES = set(CUES)
STOP = set("của và các là được có cho theo với trong này đó những một người phải thì".split())

_ALL = sorted(((c, t) for t, cs in CUES.items() for c in cs), key=lambda x: -len(x[0]))
_CUE_RE = re.compile("|".join(r"\b" + re.escape(c) + r"\b" for c, _ in _ALL), re.I)
_TYPE = {c.lower(): t for c, t in _ALL}
_KHOAN_RE = re.compile(r"(?m)^\s*(\d+)\.\s+")
_HEADING_RE = re.compile(r"(?m)^\s*(?:Mục|Chương|Phần|MỤC|CHƯƠNG|PHẦN|Điều|ĐIỀU)\s+[0-9IVXLCDM]+(?:\.|\b)")
_SENT = re.compile(r"(?<=[.;])\s+")
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


def norm(s):
    s = unicodedata.normalize("NFC", s or "")
    s = re.sub(
        r"([a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ])(thì\s+)",
        r"\1 \2", s
    )
    s = re.sub(
        r"([a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ])"
        r"([A-ZÀÁẢÃẠĂẮẰẲẴẶÂẤẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ])",
        r"\1. \2", s
    )
    return s


def find_cues(text):
    text = norm(text)
    out = []
    for m in _CUE_RE.finditer(text):
        s, e = m.start(), m.end()
        cue_str = m.group(0)
        low_cue = cue_str.lower()
        t = _TYPE.get(low_cue)
        if not t:
            continue
        sent_start = max(text.rfind(".", 0, s), text.rfind(";", 0, s), text.rfind("\n", 0, s)) + 1
        pre_sent = text[sent_start:s]
        if pre_sent.count("(") > pre_sent.count(")"):
            continue
        if low_cue == "nếu":
            sub_around = text[max(0, s - 2):min(len(text), e + 25)]
            if re.search(r"\(\s*nếu\s+(?:có|được\s+yêu\s+cầu)\s*\)", sub_around, re.I):
                continue
            pre_text = text[max(0, s - 15):s].strip().lower()
            if pre_text.endswith("hậu quả"):
                continue
        if low_cue in ("trường hợp", "trong trường hợp"):
            pre_word = text[max(0, s - 35):s].strip().lower()
            if any(pre_word.endswith(w) for w in [
                "các", "những", "mọi", "thuộc", "từng", "trong các", "một số",
                "cho", "vào", "về", "đối với", "tùy", "tuỳ", "trừ", "ngoại trừ",
                "hoặc", "hay", "dẫn đến", "kể cả", "như", "xử lý", "giải quyết"
            ]):
                continue
            if re.search(r"\b(?:trừ|ngoại trừ)\s+[^.;:\n]{1,50}(?:,|và|hoặc)\s*$", pre_sent, re.I):
                continue
            if re.match(r"^\s*(?:[a-zđ]\)\s*|\d+\.\s*)?(?:trong\s+)?trường\s+hợp\b", pre_sent, re.I) and " thì " not in pre_sent.lower() and "," not in pre_sent:
                continue
            if "đặc xá" in pre_word and text[e:e + 15].strip().lower().startswith("đặc biệt"):
                continue
        out.append((t, cue_str, s, e))
    return out


def _clean_article_raw(article):
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
    article = _clean_article_raw(article)
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


def fallback_props(article):
    return [s.strip() for t in split_khoan(article).values() for s in _SENT.split(t) if len(s.split()) >= 3]


def toks(s):
    return [w for w in re.findall(r"\w+", norm(s).lower()) if w not in STOP]


def coverage(span, texts):
    st = toks(span)
    if not st:
        return 0.0
    bag = set(w for t in texts for w in toks(t))
    return sum(1 for w in st if w in bag) / len(st)


# =====================================================================
# 2. Pointer Refinement (Prune, Invert, Attach) & Proposition Repair
# =====================================================================
def next_pid_num(props):
    mx = 0
    for p in props:
        uid = p.get("uid", "")
        m = re.search(r":p(\d+)$", uid)
        if m:
            mx = max(mx, int(m.group(1)))
    return mx + 1


def recover_omitted_cue_sentences(props, aid, article_text):
    """Proposition repair (§4.2): re-insert clause sentences containing STRONG cues
    if no existing proposition covers at least 60% of their content tokens."""
    existing_texts = [p["text"] for p in props]
    recovered_uids = set()
    for fb_sent in fallback_props(article_text):
        strong_cues = [c for c in find_cues(fb_sent) if c[0] in STRONG]
        if not strong_cues:
            continue
        max_single_cov = max((coverage(fb_sent, [t]) for t in existing_texts), default=0.0)
        if max_single_cov < 0.60:
            nid = next_pid_num(props)
            uid = f"{aid}:p{nid}"
            props.append({"uid": uid, "aid": aid, "text": fb_sent, "role": "FACT"})
            existing_texts.append(fb_sent)
            recovered_uids.add(uid)
    return props, recovered_uids


def assign_khoan_idx(prop_text, khoan_items):
    if len(khoan_items) <= 1:
        return 0
    best_k, best_cov = 0, -1.0
    for idx, (_, k_txt) in enumerate(khoan_items):
        c = coverage(prop_text, [k_txt])
        if c > best_cov:
            best_cov = c
            best_k = idx
    return best_k


def refine_lp_record(rec, article_text, recover_sents=True, stats_counter=None):
    aid = rec["aid"]
    props = [dict(p) for p in rec["props"]]
    recovered_uids = set()
    if recover_sents:
        props, recovered_uids = recover_omitted_cue_sentences(props, aid, article_text)
        if stats_counter is not None:
            stats_counter["recovered_sents"] += len(recovered_uids)

    p_by_uid = {p["uid"]: p for p in props}
    p_cues = {p["uid"]: find_cues(p["text"]) for p in props}
    p_strong_cues = {u: [(t, c, s, e) for t, c, s, e in cs if t in STRONG] for u, cs in p_cues.items()}

    khoan_items = list(split_khoan(article_text).items())
    p_khoan = {p["uid"]: assign_khoan_idx(p["text"], khoan_items) for p in props}

    cleaned_ptrs = []
    seen_pairs = set()

    for e in rec.get("pointers", []):
        h, t, ty, cue = e["head"], e["tail"], e["type"], e.get("cue", "").strip()
        if h not in p_by_uid or t not in p_by_uid or h == t:
            continue

        cue_matches = find_cues(cue) if cue else []
        h_has_cue = bool(p_cues[h])
        t_has_cue = bool(p_cues[t])

        # Operation 1 (Prune): Drop unsupported HIỆU_LỰC / conjunction edges
        if ty == "HIỆU_LỰC":
            if not any(ct == "HIỆU_LỰC" for ct, *_ in (cue_matches + p_cues[t] + p_cues[h])):
                if stats_counter is not None:
                    stats_counter["pruned"] += 1
                continue
        elif ty not in STRONG:
            if not (cue_matches or t_has_cue or h_has_cue):
                if stats_counter is not None:
                    stats_counter["pruned"] += 1
                continue
        else:
            if cue.lower() in ("và", "hoặc", "") and not (t_has_cue or h_has_cue) and p_by_uid[t].get("role") != "MODIFIER" and p_by_uid[h].get("role") != "MODIFIER":
                if stats_counter is not None:
                    stats_counter["pruned"] += 1
                continue

        # Operation 2 (Invert): Normalize MODIFIER -> RULE into RULE -> MODIFIER
        h_role = p_by_uid[h].get("role", "FACT")
        t_role = p_by_uid[t].get("role", "FACT")
        h_starts_cond = bool(p_strong_cues[h] and p_strong_cues[h][0][2] < 20)
        t_starts_cond = bool(p_strong_cues[t] and p_strong_cues[t][0][2] < 20)

        if (h_role == "MODIFIER" and t_role == "RULE" and not t_starts_cond) or (h_starts_cond and not t_starts_cond and t_role == "RULE"):
            h, t = t, h
            if stats_counter is not None:
                stats_counter["inverted"] += 1

        if (h, t) not in seen_pairs:
            seen_pairs.add((h, t))
            cleaned_ptrs.append({"head": h, "tail": t, "type": ty, "cue": cue})

    # Operation 3 (Attach): Link unlinked MODIFIER / cue-initial propositions to nearest RULE in the same clause
    linked_nodes = {e["head"] for e in cleaned_ptrs} | {e["tail"] for e in cleaned_ptrs}
    uids = [p["uid"] for p in props]
    for idx, u in enumerate(uids):
        if u in recovered_uids:
            continue
        starts_with_strong = bool(p_strong_cues[u] and p_strong_cues[u][0][2] < 20)
        is_mod = (p_by_uid[u].get("role") == "MODIFIER") or starts_with_strong
        if not is_mod or u in linked_nodes:
            continue
        sc = p_strong_cues[u][0] if p_strong_cues[u] else ("VỚI_ĐIỀU_KIỆN", "", 0, 0)
        u_k = p_khoan[u]

        same_k_rules = [
            ru for ru in uids
            if ru != u and ru not in recovered_uids and p_khoan[ru] == u_k and (
                p_by_uid[ru].get("role") == "RULE"
                or not (p_strong_cues[ru] and p_strong_cues[ru][0][2] < 20)
            )
        ]
        same_k_rules.sort(key=lambda ru: abs(uids.index(ru) - idx))
        if same_k_rules:
            ru = same_k_rules[0]
            if (ru, u) not in seen_pairs:
                seen_pairs.add((ru, u))
                cleaned_ptrs.append({"head": ru, "tail": u, "type": sc[0], "cue": sc[1]})
                if stats_counter is not None:
                    stats_counter["attached_same_khoan"] += 1

    out = dict(rec)
    out["props"] = props
    out["pointers"] = cleaned_ptrs
    return out


def repair_std_record(rec, article_text):
    props = [dict(p) for p in rec["props"]]
    props, _ = recover_omitted_cue_sentences(props, rec["aid"], article_text)
    out = dict(rec)
    out["props"] = props
    return out


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser(description="S2 Pointer Refinement & Proposition Repair")
    ap.add_argument("--data_dir", required=True, help="Directory containing articles_v2.jsonl, props_lp_raw.jsonl, props_std_raw.jsonl")
    ap.add_argument("--out_dir", default=None, help="Output directory (defaults to --data_dir)")
    args = ap.parse_args()
    out_dir = args.out_dir or args.data_dir
    os.makedirs(out_dir, exist_ok=True)

    arts = read_jsonl(os.path.join(args.data_dir, "articles_v2.jsonl"))
    by_aid = {a["aid"]: a for a in arts}
    lp_raw = [r for r in read_jsonl(os.path.join(args.data_dir, "props_lp_raw.jsonl")) if r["aid"] in by_aid]
    std_raw = [r for r in read_jsonl(os.path.join(args.data_dir, "props_std_raw.jsonl")) if r["aid"] in by_aid]

    stats_all, stats_eval, stats_dev = Counter(), Counter(), Counter()
    lp_edge_only, lp_clean, std_clean = [], [], []

    for r in lp_raw:
        art = by_aid[r["aid"]]
        txt = art["article_content"]
        split = art.get("split", "eval")
        st_split = stats_eval if split == "eval" else stats_dev
        lp_edge_only.append(refine_lp_record(r, txt, recover_sents=False))
        rec_clean = refine_lp_record(r, txt, recover_sents=True, stats_counter=st_split)
        for k, v in st_split.items():
            pass
        lp_clean.append(rec_clean)

    for k in set(stats_eval) | set(stats_dev):
        stats_all[k] = stats_eval[k] + stats_dev[k]

    for r in std_raw:
        std_clean.append(repair_std_record(r, by_aid[r["aid"]]["article_content"]))

    write_jsonl(os.path.join(out_dir, "props_lp_edge_only.jsonl"), lp_edge_only)
    write_jsonl(os.path.join(out_dir, "props_lp.jsonl"), lp_clean)
    write_jsonl(os.path.join(out_dir, "props_std.jsonl"), std_clean)

    raw_ptrs = sum(len(r.get("pointers", [])) for r in lp_raw)
    clean_ptrs = sum(len(r.get("pointers", [])) for r in lp_clean)
    p_raw = {(r["aid"], e["head"], e["tail"]) for r in lp_raw for e in r.get("pointers", [])}
    p_lp = {(r["aid"], e["head"], e["tail"]) for r in lp_clean for e in r.get("pointers", [])}
    inv = {(a, t, h) for (a, h, t) in p_raw} & p_lp - p_raw
    att = p_lp - p_raw - inv
    pru = p_raw - p_lp - {(a, t, h) for (a, h, t) in inv}

    print(f"Processed {len(lp_clean)} articles (eval={sum(1 for a in arts if a.get('split')=='eval')}, dev={sum(1 for a in arts if a.get('split')=='dev')})")
    print(f"Pointers: raw={raw_ptrs} (unique pairs={len(p_raw)}) -> refined={clean_ptrs}")
    print(f"  - Pruned:              {len(pru)} (eval={sum(1 for a,_,_ in pru if by_aid[a].get('split')=='eval')}, dev={sum(1 for a,_,_ in pru if by_aid[a].get('split')=='dev')})")
    print(f"  - Inverted:            {len(inv)} (eval={sum(1 for a,_,_ in inv if by_aid[a].get('split')=='eval')}, dev={sum(1 for a,_,_ in inv if by_aid[a].get('split')=='dev')})")
    print(f"  - Newly attached:      {len(att)} (eval={sum(1 for a,_,_ in att if by_aid[a].get('split')=='eval')}, dev={sum(1 for a,_,_ in att if by_aid[a].get('split')=='dev')})")
    print(f"  - Repaired sentences:  {stats_all['recovered_sents']} (eval={stats_eval['recovered_sents']}, dev={stats_dev['recovered_sents']})")


if __name__ == "__main__":
    main()
