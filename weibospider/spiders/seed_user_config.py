#!/usr/bin/env python
# encoding: utf-8

import datetime
from datetime import timezone

# 种子用户id
# 种子用户：
SEED_USERS = {
    # 正常用户
    "normal": [
        # 官方媒体
        '2803301701',  # 人民日报
        '6189120710',  # 央视军事
        '3937348351',  # 共青团中央

        # 娱乐明星
        '1669879400',  # 迪丽热巴
        '5331040243',  # 沈月
        '1195354434',  # 林俊杰

        # 网红/大V
        '3951865584',  # 一雯黑
        '1044980795',  # 影视飓风
        '3099016097',  # 英国报姐
        '1961381224',  # 抬头看风景nono

        # 企业账号
        '1771925961',  # 小米公司
        '1839167003',  # 华为终端
        '1846456085',  # 腾讯公司

        # 学者/专家
        '2610429597',  # 罗翔说刑法
        '1393017020',  # 无穷小亮微博

        #普通人
        '1819457014',#万紫千红的红_15
        '6387236244',#屿雾yu_
        '3739579742',#復筱_狱
        '7918156285',#狂沙满满
        '5772795860',#都都都挺好的hhh



    ],
    # 恶意用户
    "malicious": [
        '3791019734',#可轩芮儿
        '7570102808',#风扬起思念m
        '6567896402',#梦幻里的鱼
        '6146792230',#迅猛龙你月
        '7497388593',#好运加满11

    ]
}

# 采集页数配置
CRAWL_PAGES = {
    "seed_follow": 1,        # 种子用户关注列表采集页数
    "neighbor_follow": 1,    # 一层邻居关注列表采集页数
    "seed_fan": 1,           # 种子用户粉丝采集页数
    "neighbor_fan": 1,       # 一层邻居粉丝采集页数
    "user_tweet": 2,         # 单个用户博文最大采集页数
    "tweet_comment": 2,      # 单条博文评论最大采集页数
}

# 博文采集时间范围：默认近6个月
TWEET_START_TIME = datetime.datetime.now(timezone.utc) - datetime.timedelta(days=180)
TWEET_END_TIME = datetime.datetime.now(timezone.utc)

# ===================== 反爬配置 =====================
CRAWL_DELAY = {
    "min": 5,    # 请求最小延迟（秒）
    "max": 10,
    "batch_size": 3,  # 每批处理用户数
}

# 输出
OUTPUT_PATH = "../../output"
USER_ID_FILE = "../output/user_id_list.txt"