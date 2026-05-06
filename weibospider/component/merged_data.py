import os
import glob

# 设置输出目录
output_dir = "../../output"
merged_file = "../../output/merged_tweet.jsonl"

# 获取所有 .jsonl 文件，并按文件名中的时间戳排序
jsonl_files = sorted(
    glob.glob(os.path.join(output_dir, "*.jsonl")),
    key=lambda x: os.path.basename(x).split('_')[3]  # 按时间戳部分排序，如 005612
)

# 合并文件
with open(merged_file, 'w', encoding='utf-8') as outfile:
    for file in jsonl_files:
        with open(file, 'r', encoding='utf-8') as infile:
            for line in infile:
                outfile.write(line)

print(f"合并完成！共合并 {len(jsonl_files)} 个文件，输出到: {merged_file}")