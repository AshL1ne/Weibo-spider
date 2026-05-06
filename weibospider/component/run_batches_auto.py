import os
import subprocess
import time
import random

# 直接运行即可，无参
batch_dir = "../output/fan_fan_batches/118"  # 分割后的小文件目录
cmd_tmpl = 'python run_spider.py tweet_mobile "{path}"'

# 根据实际情况调整顺序（确保按数字顺序）
all_files = sorted(
    [f for f in os.listdir(batch_dir) if f.endswith('.txt')],
    key=lambda x: int(os.path.splitext(x)[0])
)

error_records = []  # 存储错误记录

for f in all_files:
    batch_path = os.path.join(batch_dir, f)
    print(f'正在采集 {batch_path} ......')

    # 调用主爬虫
    ret = subprocess.run(cmd_tmpl.format(path=batch_path), shell=True)

    if ret.returncode != 0:
        error_msg = f"爬虫 {batch_path} 时出错，已跳过，returncode={ret.returncode}"
        print(error_msg)
        error_records.append({
            'file': batch_path,
            'returncode': ret.returncode,
            'message': error_msg
        })
    else:
        print(f"{batch_path} 采集完成。\n")

    # 5-10秒之间的随机间隔时间
    sleep_time = random.uniform(5, 10)
    # 可选的：显示等待时间
    print(f"等待 {sleep_time:.1f} 秒后继续...")
    time.sleep(sleep_time)

print("\n" + "=" * 50)
print("全部批次采集完毕！")
print("=" * 50)

# 如果有错误，重新输出错误信息
if error_records:
    print("\n" + "=" * 50)
    print("错误记录汇总：")
    print("=" * 50)
    for i, error in enumerate(error_records, 1):
        print(f"{i}. {error['message']}")
    print(f"总计 {len(error_records)} 个批次采集失败")
    print("=" * 50)
else:
    print("\n✓ 所有批次均成功采集，无错误！")