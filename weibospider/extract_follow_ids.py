import glob
import json
from datetime import datetime

# python extract_follow_ids.py

def main():
    # 自动找到所有 follow_mobile_spider_*.jsonl 文件
    jsonl_files = glob.glob("../output/follow_mobile_spider_*.jsonl")
    follow_ids = set()

    for file in jsonl_files:
        with open(file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    # 确认 item 是关注关系类型，并包含 follow_id 字段
                    if obj.get("relation_type") == "follow" and "follow_id" in obj:
                        follow_ids.add(str(obj["follow_id"]))
                except Exception:
                    continue

    # 结果输出文件，防止覆盖老文件，带日期时间戳
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = f"../output/follow_ids_{ts}.txt"
    with open(out_file, "w", encoding="utf-8") as fw:
        fw.write(",".join(follow_ids))
    print(f"已提取 {len(follow_ids)} 个 follow_id，保存至 {out_file}")

if __name__ == "__main__":
    main()