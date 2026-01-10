import os

# ===== CONFIG =====
PROJECT_DIR = "."   # โฟลเดอร์โปรเจค Django ของคุณ
OUTPUT_PART1 = "django_project_part1.txt"
OUTPUT_PART2 = "django_project_part2.txt"
EXTENSIONS = (".py", ".html")          # ประเภทไฟล์ที่ต้องการรวม
# ==================

all_contents = []

# เดินลูปทุกไฟล์ในโปรเจค
for root, dirs, files in os.walk(PROJECT_DIR):
    # ข้ามโฟลเดอร์ที่ไม่ต้องการ
    skip_dirs = ["venv", "__pycache__", "static", "media", "node_modules", "migrations"]
    if any(s in root for s in skip_dirs):
        continue

    for filename in files:
        if filename.endswith(EXTENSIONS):
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, PROJECT_DIR)

            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except:
                with open(full_path, "r", encoding="latin-1") as f:
                    content = f.read()

            # ใส่ header แสดงชื่อไฟล์ก่อนคัดลอกโค้ด
            block = f"\n\n=== {rel_path} ===\n{content}\n"
            all_contents.append(block)

# รวมทั้งหมดเป็นข้อความก้อนเดียว
full_text = "".join(all_contents)

# แบ่งเป็น 2 ไฟล์ (ครึ่งหนึ่ง)
mid = len(full_text) // 2
part1 = full_text[:mid]
part2 = full_text[mid:]

# เขียนลงไฟล์
with open(OUTPUT_PART1, "w", encoding="utf-8") as f:
    f.write(part1)

with open(OUTPUT_PART2, "w", encoding="utf-8") as f:
    f.write(part2)

print("Done! Created:", OUTPUT_PART1, "and", OUTPUT_PART2)
