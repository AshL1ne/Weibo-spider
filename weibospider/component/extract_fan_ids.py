import glob
import json
from datetime import datetime

# python extract_fan_ids.py

def main():
    # 自动找到所有 fan_mobile_spider_*.jsonl 文件
    jsonl_files = glob.glob("../../output/fan_mobile_spider_*.jsonl")
    # jsonl_files = glob.glob("../../output/fan_fan_user/merged_fan_fan.jsonl")
    # jsonl_files = glob.glob("../../output/fan_mobile_spider_20260415_182250.jsonl")
    fan_ids = set()

    # 逐文件处理
    for file in jsonl_files:
        with open(file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    # 确认 item 是粉丝关系类型，并包含 fan_id 字段
                    if obj.get("relation_type") == "fan" and "fan_id" in obj:
                        fan_ids.add(str(obj["fan_id"]))
                except Exception:
                    continue

    # 结果输出文件，防止覆盖老文件，带日期时间戳
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = f"../output/fan_ids_{ts}.txt"
    with open(out_file, "w", encoding="utf-8") as fw:
        fw.write(",".join(fan_ids))
    print(f"已提取 {len(fan_ids)} 个 fan_id，保存至 {out_file}")

if __name__ == "__main__":
    main()