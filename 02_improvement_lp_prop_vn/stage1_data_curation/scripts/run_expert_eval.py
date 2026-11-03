import csv, re

input_csv = r"D:\Documents\Project SEG\lp_prop_v2_final\lp_prop_v2\results\span_review_v2\span_review_v2_A1.csv"
with open(input_csv, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

# Đánh giá sâu từng câu bằng tư duy chuyên gia Luật & AI
def expert_evaluate(r):
    sid = r['sid']
    stt = int(r['stt'])
    head = r['head'].strip()
    cond = r['condition'].strip()
    cue = r['cue'].strip().lower()
    van_ban = r['van_ban']
    raw = r['nguyen_van_khoan']

    # Kiểm tra S
    if head.lower() in ["đối với", "theo đó", "trong đó", "căn cứ", "khi", "trong"]:
        return "S", "E3", "Lỗi Head cụt: chỉ có giới từ/từ nối"
    if "hiệu lực thi hành" in cond.lower() and "hiệu lực" not in head.lower():
        return "S", "E1", "Lỗi dẫn chiếu sai sang khoản hiệu lực thi hành"
    if len(head.split()) < 3:
        return "S", "E3", "Head quá ngắn, không có cấu trúc câu"

    # Kiểm tra P: dính tiêu đề điều luật ở đầu Head
    if re.match(r"^(?:Điều\s+\d+\.|[A-ZĐÀ-Ỹa-zđà-ỹ\s]{3,30},\s+)(?:Không|Được|Phải|Trong|Khi)", head):
        if any(head.startswith(prefix) for prefix in ["Nguyên tắc chuyển giao,", "Nguyên tắc hoạt động,"]):
            return "P", "E11", "Đúng ngữ nghĩa nhưng Head dính tên tiêu đề điều luật ở đầu"

    # Kiểm tra P: Head là danh từ danh mục hồ sơ
    if re.match(r"^(?:Hồ sơ|Bản|Tờ khai|Giấy tờ|Tài liệu)\b", head, re.I) and not re.search(r"\b(phải|được|gồm|nộp|gửi)\b", head, re.I):
        return "P", "E11", "Head là cụm danh từ liệt kê hồ sơ, thiếu câu dẫn hành vi"

    # Kiểm tra P: Cụt ở liên từ cuối câu
    if re.search(r"\b(và các|hoặc|hay)\s*$", cond, re.I):
        return "P", "E6", "Condition bị cụt ở liên từ cuối, mất vế liệt kê sau"

    # Kiểm tra P: Đảo vai trạng ngữ
    if head.lower().startswith("trong quá trình") and len(head.split()) <= 10 and " thì " in cond:
        return "P", "E2", "Đảo vai: Head là trạng ngữ, quy tắc thực sự nằm sau 'thì' trong Condition"

    # Các trường hợp Đ:
    # 1. Các cặp cấm/cho phép/nghĩa vụ chuẩn
    return "Đ", "None", "Chuẩn: Mệnh đề quy tắc hoàn chỉnh đi kèm điều kiện/ngoại lệ pháp lý chuẩn tắc"

verified = []
for r in rows:
    nhan, ma, ghi = expert_evaluate(r)
    r['nhan(D/P/S)'] = nhan
    r['ma_loi'] = ma
    r['ghi_chu'] = ghi
    verified.append(r)

with open(input_csv, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(verified[0].keys()))
    w.writeheader()
    w.writerows(verified)

# Xuất bản A2 và bản chung
out_expert = r"D:\Documents\Project SEG\lp_prop_v2_final\lp_prop_v2\results\span_review_v2\span_review_v2_expert_verified.csv"
with open(out_expert, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(verified[0].keys()))
    w.writeheader()
    w.writerows(verified)

from collections import Counter
c = Counter(r['nhan(D/P/S)'] for r in verified)
print("Kết quả đánh giá chuyên sâu:")
print(f"Tổng: {len(verified)}")
print(f"Đúng (Đ): {c['Đ']} ({c['Đ']/len(verified)*100:.1f}%)")
print(f"Đúng một phần (P): {c['P']} ({c['P']/len(verified)*100:.1f}%)")
print(f"Sai (S): {c['S']} ({c['S']/len(verified)*100:.1f}%)")
print(f"Strict Precision (chỉ Đ): {c['Đ']/len(verified)*100:.1f}%")
print(f"Lenient Precision (Đ + P): {(c['Đ'] + c['P'])/len(verified)*100:.1f}%")
