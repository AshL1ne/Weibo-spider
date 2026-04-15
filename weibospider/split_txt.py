import os

def split_txt_to_batches(input_file, out_dir, batch_size=100):
    # 1. 读取所有id（英文逗号分割）
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if "," in content:
            user_ids = [i.strip() for i in content.split(",") if i.strip()]
        else:
            # 支持每行一个id的情况
            user_ids = [line.strip() for line in content.splitlines() if line.strip()]

    # 2. 创建输出目录
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    total = len(user_ids)
    num_batches = (total + batch_size - 1) // batch_size

    for i in range(num_batches):
        batch_ids = user_ids[i*batch_size:(i+1)*batch_size]
        out_path = os.path.join(out_dir, f"{i+1}.txt")
        with open(out_path, "w", encoding="utf-8") as fw:
            fw.write(",".join(batch_ids))
        print(f"已写入 {out_path} ({len(batch_ids)} 个id)")

    print(f"总共拆分为 {num_batches} 个文件，总id数：{total}")

if __name__ == "__main__":
    # 使用方法示例：python split_txt.py ../output/fan_ids_20260415_230316.txt ../output/fan_batches 100
    import sys
    if len(sys.argv) < 3:
        print("用法: python split_txt_by_batch.py <原txt路径> <输出文件夹> [每批数量,默认100]")
    else:
        input_file = sys.argv[1]
        out_dir = sys.argv[2]
        batch_size = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        split_txt_to_batches(input_file, out_dir, batch_size)