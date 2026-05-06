#!/usr/bin/env python
# encoding: utf-8

import os
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from spiders.tweet_mobile import TweetMobileSpider
from spiders.user_mobile import UserMobileSpider
from spiders.fan_mobile import FanMobileSpider
from spiders.follow_mobile import FollowMobileSpider
from spiders.comment_mobile import CommentMobileSpider


if __name__ == '__main__':
    mode = sys.argv[1]

    os.environ['SCRAPY_SETTINGS_MODULE'] = 'settings'

    settings = get_project_settings()
    process = CrawlerProcess(settings)
    mode_to_spider = {
        'tweet_mobile': TweetMobileSpider,
        'user_mobile': UserMobileSpider,
        'fan_mobile': FanMobileSpider,
        'follow_mobile': FollowMobileSpider,
        'comment_mobile': CommentMobileSpider,

    }

    # ========== 支持 user_ids 参数文件 ==========
    #  python run_spider.py fan_mobile ../output/fan_batches/19.txt
    #  python run_spider.py tweet_mobile ../output/fan_batches/12.txt
    user_ids = None
    extra_kwargs = {}
    if len(sys.argv) > 2:
        user_id_file = sys.argv[2]
        # 判断是不是一个存在的文本文件
        if os.path.isfile(user_id_file):
            with open(user_id_file, "r", encoding='utf-8') as f:
                # 去掉空行并 strip
                user_ids = ','.join([line.strip() for line in f if line.strip()])
            extra_kwargs['user_ids'] = user_ids
        else:
            # 逗号分隔的 user_ids 字符串
            user_ids = sys.argv[2]
            extra_kwargs['user_ids'] = user_ids

    process.crawl(mode_to_spider[mode], **extra_kwargs)
    # the script will block here until the crawling is finished
    process.start()
