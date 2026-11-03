"""
Script: scan_logic_errors.py
Mục đích: Quét toàn bộ corpus (Passage vs Proposition) để kiểm định hiện tượng
rơi rụng điều kiện logic (Logic Loss / Conditional Connective Truncation)
khi phân rã văn bản bằng Propositionizer (Chen et al., 2024).

Dữ liệu đầu ra:
- potential_logic_errors.csv: Danh sách các passage bị mất điều kiện ngoại lệ/logic,
  kèm theo proposition tương ứng và cờ đánh dấu lỗi.
"""

import os
import re
import json
import argparse
import pandas as pd
from collections import defaultdict

def scan_corpus_logic_errors(corpus_dir, output_csv):
    pass_file = os.path.join(corpus_dir, "passage.jsonl")
    prop_file = os.path.join(corpus_dir, "proposition.jsonl")

    if not os.path.exists(pass_file) or not os.path.exists(prop_file):
        raise FileNotFoundError(f"Không tìm thấy passage.jsonl hoặc proposition.jsonl tại: {corpus_dir}")

    # Các từ khóa điều kiện, ngoại lệ, phủ định, tình thái mạnh
    keywords = [
        r"\bunless\b",
        r"\bprovided that\b",
        r"\bonly if\b",
        r"\bas long as\b",
        r"\bexcept (that|when|if|in)\b",
        r"\bnot all\b",
        r"\bno longer\b"
    ]
    regex_kw = re.compile("|".join(keywords), re.IGNORECASE)

    print(f"[*] Đang quét toàn bộ passage trong {pass_file}...")
    matched_passages = {}
    total_passages = 0
    with open(pass_file, "r", encoding="utf-8") as f:
        for line in f:
            total_passages += 1
            d = json.loads(line)
            text = d.get("text", "")
            m = regex_kw.search(text)
            if m:
                matched_passages[d["id"]] = {
                    "title": d.get("title", ""),
                    "passage_text": text,
                    "keyword_matched": m.group(0).lower()
                }

    print(f" -> Tổng số passage quét: {total_passages:,}")
    print(f" -> Số passage chứa liên từ logic/điều kiện: {len(matched_passages):,}")

    print(f"[*] Đang đọc và ánh xạ propositions từ {prop_file}...")
    props_by_pid = defaultdict(list)
    total_props = 0
    with open(prop_file, "r", encoding="utf-8") as f:
        for line in f:
            total_props += 1
            d = json.loads(line)
            pid = d.get("pid")
            if pid in matched_passages:
                props_by_pid[pid].append(d.get("text", ""))

    print(f" -> Tổng số propositions quét: {total_props:,}")

    print("[*] Đang phân tích mức độ bảo tồn logic...")
    rows = []
    for pid, info in matched_passages.items():
        props = props_by_pid.get(pid, [])
        props_str = "\n".join([f"[{i+1}] {p}" for i, p in enumerate(props)])
        
        # Kiểm tra xem từ khóa logic có bị mất trong TẤT CẢ các proposition không
        kw = info["keyword_matched"]
        kw_in_props = any(re.search(r"\b" + re.escape(kw) + r"\b", p, re.IGNORECASE) for p in props)
        
        rows.append({
            "pid": pid,
            "title": info["title"],
            "keyword": kw,
            "keyword_preserved_in_props": kw_in_props,
            "passage_text": info["passage_text"],
            "propositions": props_str,
            "num_propositions": len(props)
        })

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(os.path.abspath(output_csv)), exist_ok=True)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"[+] Đã xuất file kết quả: {output_csv} ({len(df)} hàng)")

    dropped = df[df["keyword_preserved_in_props"] == False]
    pct = (len(dropped) / len(df) * 100) if len(df) > 0 else 0
    print("\n" + "="*50)
    print("           BÁO CÁO THỰC NGHIỆM ĐỘNG LỰC LP-PROP")
    print("="*50)
    print(f"Tổng số passage có liên từ logic : {len(df):,}")
    print(f"Số passage BỊ MẤT ĐIỀU KIỆN LOGIC : {len(dropped):,} ({pct:.1f}%)")
    print("\nTop các từ khóa bị mất nhiều nhất:")
    print(dropped["keyword"].value_counts().to_string())
    print("="*50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quét lỗi mất điều kiện logic trong Propositionizer")
    default_corpus = r"D:\Documents\Project SEG\results\results_run_2\densex\corpus"
    if not os.path.exists(default_corpus):
        default_corpus = r"D:\Documents\Project SEG\results\results_run_1\densex\corpus"
    
    default_out = r"D:\Documents\Project SEG\results\04_logic_error_analysis\potential_logic_errors.csv"
    
    parser.add_argument("--corpus_dir", type=str, default=default_corpus, help="Đường dẫn thư mục chứa passage.jsonl và proposition.jsonl")
    parser.add_argument("--output_csv", type=str, default=default_out, help="Đường dẫn file CSV xuất ra")
    
    args = parser.parse_args()
    scan_corpus_logic_errors(args.corpus_dir, args.output_csv)
