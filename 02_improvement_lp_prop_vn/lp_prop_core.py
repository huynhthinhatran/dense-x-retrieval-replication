"""
lp_prop_core.py - Core Engine for Condition Pointer Retrieval (LP-Prop)
Kế thừa nguyên bản pipeline của Dense X (Chen et al., EMNLP 2024),
bổ sung cơ chế Condition Pointer (Con trỏ Điều kiện 2 chiều) thuần Python dict.
Không phụ thuộc NetworkX, hoàn toàn tương thích với Kaggle GPU/CPU.
"""

import json
import re
from collections import Counter
from typing import List, Dict, Any, Tuple, Optional


# =====================================================================
# 1. PARSING & DATA PREPARATION
# =====================================================================

def parse_llm_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Trích xuất JSON an toàn từ phản hồi của Qwen-2.5-7B
    (xử lý sạch sẽ các khối markdown ```json ... ``` hoặc text thừa).
    """
    if not raw_text or not isinstance(raw_text, str):
        return None
    raw_text = raw_text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
    if match:
        raw_text = match.group(1).strip()
    try:
        return json.loads(raw_text)
    except Exception:
        # Fallback: tìm đoạn bao giữa cặp ngoặc nhọn đầu tiên và cuối cùng
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(raw_text[start : end + 1])
            except Exception:
                pass
    return None


def build_pointers(
    propositions_data: List[Dict[str, Any]]
) -> Tuple[Dict[str, str], Dict[str, List[str]], Dict[str, List[str]]]:
    """
    Xây dựng Condition Pointers (thuần Python dict, KHÔNG dùng NetworkX).
    
    Returns:
        props: {pid: text}
        condition_ids: {rule_pid: [modifier_pid1, modifier_pid2, ...]} (Chiều xuôi)
        rule_of: {modifier_pid: [rule_pid1, rule_pid2, ...]}           (Chiều ngược)
    """
    props = {}
    condition_ids = {}

    for item in propositions_data:
        aid = item.get("aid", "")
        # Nạp propositions
        for p in item.get("propositions", []):
            pid = f"{aid}_{p['pid']}" if aid else p["pid"]
            props[pid] = p["text"]

        # Nạp cạnh logic (edges / pointers)
        for e in item.get("edges", []):
            h = f"{aid}_{e['head']}" if aid else e["head"]
            t = f"{aid}_{e['tail']}" if aid else e["tail"]
            condition_ids.setdefault(h, []).append(t)

    # Tự động suy ra rule_of (chiều ngược)
    rule_of = {}
    for h, tails in condition_ids.items():
        for t in tails:
            rule_of.setdefault(t, []).append(h)

    return props, condition_ids, rule_of


# =====================================================================
# 2. RETRIEVAL EXPANSION VỚI NGÂN SÁCH TỪ B (DENSE X STANDARD)
# =====================================================================

def lp_context(
    retrieved_pids: List[str],
    props: Dict[str, str],
    condition_ids: Dict[str, List[str]],
    rule_of: Dict[str, List[str]],
    B: int = 100,
    expansion_mode: str = "both"
) -> List[str]:
    """
    Tạo context truy xuất với cơ chế Condition Pointer 2 chiều trong ngân sách B từ.
    Đúng chuẩn đánh giá công bằng của Dense X (Chen et al., EMNLP 2024).

    Args:
        retrieved_pids: Danh sách ID các proposition lấy từ FAISS (đã sort điểm giảm dần).
        props: Dict mapping {pid: text}.
        condition_ids: Chiều xuôi {nguyên_tắc: [ngoại_lệ_1, ngoại_lệ_2]}.
        rule_of: Chiều ngược {ngoại_lệ: [nguyên_tắc_1, nguyên_tắc_2]}.
        B: Ngân sách từ tối đa (mặc định 100 hoặc 500 từ).
        expansion_mode: 'both' (2 chiều), 'out' (chỉ xuôi), 'none' (không mở rộng - baseline).
    """
    ctx, seen, used = [], set(), 0

    for p in retrieved_pids:
        if p not in props:
            continue

        if expansion_mode == "both":
            # Kéo cả: [Nguyên tắc của p] + [Chính p] + [Các ngoại lệ của p]
            candidates = rule_of.get(p, []) + [p] + condition_ids.get(p, [])
        elif expansion_mode == "out":
            candidates = [p] + condition_ids.get(p, [])
        else:  # none
            candidates = [p]

        for q in candidates:
            if q in seen or used >= B or q not in props:
                continue
            words = props[q].split()[: B - used]
            if not words:
                continue
            ctx.append(" ".join(words))
            seen.add(q)
            used += len(words)

        if used >= B:
            break

    return ctx


# =====================================================================
# 3. CHỈ SỐ ĐÁNH GIÁ (METRICS: CCR & LFR)
# =====================================================================

def _tokenize(text: str) -> List[str]:
    """Tách từ đơn giản và loại bỏ ký tự đặc biệt."""
    return re.findall(r"\w+", text.lower())


def span_coverage(gold_span: str, retrieved_texts: List[str]) -> float:
    """Đo độ phủ (coverage) của một đoạn văn bản vàng trong context được truy xuất."""
    span_toks = _tokenize(gold_span)
    if not span_toks:
        return 0.0
    context_bag = Counter(w for t in retrieved_texts for w in _tokenize(t))
    matched = sum(1 for w in span_toks if context_bag[w] > 0)
    return matched / len(span_toks)


def calculate_ccr(
    queries: List[Dict[str, Any]],
    contexts: Dict[str, List[str]],
    tau: float = 0.6
) -> Dict[str, float]:
    """
    Conditional Coverage Recall (CCR) trên tập câu hỏi có điều kiện:
    Một truy vấn được tính là thành công nếu CẢ vế nguyên tắc (head) 
    VÀ vế ngoại lệ (condition) đều đạt độ phủ >= tau trong ngân sách B.
    """
    if not queries:
        return {"CCR": 0.0, "OrphanRuleRate": 0.0, "HeadRecall": 0.0}

    both, orphan, head_ok = 0, 0, 0
    n = len(queries)

    for q in queries:
        qid = q["qid"]
        c = contexts.get(qid, [])
        h_covered = span_coverage(q["head_span"], c) >= tau
        c_covered = span_coverage(q["condition_span"], c) >= tau

        if h_covered:
            head_ok += 1
            if c_covered:
                both += 1
            else:
                orphan += 1  # Bắt trúng nguyên tắc nhưng bỏ quên ngoại lệ (nguy hiểm!)

    return {
        "CCR": both / n,
        "OrphanRuleRate": orphan / n,
        "HeadRecall": head_ok / n
    }


def calculate_lfr_rule(
    predictions: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Đo Legal Fallacy Rate (LFR) bằng luật (Rule-based Fallacy Detector):
    Một câu trả lời bị xem là Ngụy biện pháp lý nếu:
    - Trùng khớp với 'đáp án nếu bỏ qua điều kiện' (answer_if_condition_ignored)
    - Khác với 'đáp án chuẩn' (ground_truth_answer).
    """
    if not predictions:
        return {"LFR": 0.0, "Accuracy": 0.0}

    fallacies = 0
    correct = 0
    n = len(predictions)

    for item in predictions:
        pred = item["pred_answer"].strip().lower()
        gold = item["ground_truth_answer"].strip().lower()
        fallacy_ans = item.get("answer_if_condition_ignored", "").strip().lower()

        # Kiểm tra đúng
        if gold in pred or pred in gold:
            correct += 1
        # Kiểm tra ngụy biện
        elif fallacy_ans and (fallacy_ans in pred or pred in fallacy_ans):
            fallacies += 1

    return {
        "LFR": fallacies / n,
        "Accuracy": correct / n
    }


# =====================================================================
# 4. CHIA TẬP DOCUMENT-LEVEL (CHỐNG DATA LEAKAGE)
# =====================================================================

def select_and_split_documents(
    dataset_rows: List[Dict[str, Any]],
    n_exc: int = 500,
    n_ctrl: int = 500,
    dev_frac: float = 0.1,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Trích xuất 1,000 Điều luật từ thangvip:
    - 500 Điều chứa từ khóa ngoại lệ
    - 500 Điều đối chứng (không ngoại lệ)
    Chia dev/eval theo tên văn bản luật (doc_name) để kiểm tra khả năng tổng quát.
    """
    import random
    random.seed(seed)

    EXC_KEYWORDS = [
        "trừ trường hợp", "ngoại trừ", "trừ khi",
        "với điều kiện", "nhưng phải", "không áp dụng đối với"
    ]
    pattern = re.compile("|".join(EXC_KEYWORDS), re.IGNORECASE)

    exc_docs = []
    ctrl_docs = []

    for idx, r in enumerate(dataset_rows):
        content = r.get("article_content", "")
        has_exc = bool(pattern.search(content))
        item = {
            "aid": f"art_{idx:05d}",
            "doc_name": r.get("doc_name", "Unknown"),
            "doc_type": r.get("doc_type_name", "Luật"),
            "article_content": content,
            "has_exc": has_exc,
            "generated_qa_pairs": r.get("generated_qa_pairs", [])
        }
        if has_exc:
            exc_docs.append(item)
        else:
            ctrl_docs.append(item)

    random.shuffle(exc_docs)
    random.shuffle(ctrl_docs)

    selected = exc_docs[:n_exc] + ctrl_docs[:n_ctrl]
    random.shuffle(selected)

    # Chia train/dev/test theo doc_name (Document-level)
    unique_laws = list(set(d["doc_name"] for d in selected))
    random.shuffle(unique_laws)

    n_dev_laws = max(1, int(len(unique_laws) * dev_frac))
    dev_laws = set(unique_laws[:n_dev_laws])

    for d in selected:
        d["split"] = "dev" if d["doc_name"] in dev_laws else "eval"

    return selected
