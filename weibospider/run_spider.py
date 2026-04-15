#!/usr/bin/env python
# encoding: utf-8
"""
Author: nghuyong
Mail: nghuyong@163.com
Created Time: 2019-12-07 21:27
"""
#!/usr/bin/env python
# encoding: utf-8
"""
Author: nghuyong
Mail: nghuyong@163.com
Created Time: 2019-12-07 21:27
"""
import os
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
# from spiders.tweet_by_user_id import TweetSpiderByUserID
# from spiders.tweet_by_keyword import TweetSpiderByKeyword
# from spiders.tweet_by_tweet_id import TweetSpiderByTweetID
# from spiders.comment import CommentSpider
# from spiders.follower import FollowerSpider
# from spiders.user import UserSpider
# from spiders.fan import FanSpider
# from spiders.repost import RepostSpider
from spiders.tweet_mobile import TweetMobileSpider
# 添加新的移动端爬虫
from spiders.user_mobile import UserMobileSpider
from spiders.fan_mobile import FanMobileSpider
from spiders.follow_mobile import FollowMobileSpider
from spiders.comment_mobile import CommentMobileSpider
#from spiders.fan_mobile_pagination_test import FanMobilePaginationTestSpider


if __name__ == '__main__':
    mode = sys.argv[1]

    os.environ['SCRAPY_SETTINGS_MODULE'] = 'settings'

    settings = get_project_settings()
    process = CrawlerProcess(settings)
    mode_to_spider = {
        # 'comment': CommentSpider,
        # 'fan': FanSpider,
        # 'follow': FollowerSpider,
        # 'user': UserSpider,
        # 'repost': RepostSpider,
        # 'tweet_by_tweet_id': TweetSpiderByTweetID,
        # 'tweet_by_user_id': TweetSpiderByUserID,
        # 'tweet_by_keyword': TweetSpiderByKeyword,
        'tweet_mobile': TweetMobileSpider,
        # 添加新的移动端爬虫
        'user_mobile': UserMobileSpider,
        'fan_mobile': FanMobileSpider,
        'follow_mobile': FollowMobileSpider,
        'comment_mobile': CommentMobileSpider,
        #'fan_mobile_pagination_test': FanMobilePaginationTestSpider,  # 测试移动端分页请求可行性

    }

    # ========== [MODIFY] 支持 user_ids 参数文件 ==========
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
            # 如果直接给的是逗号分隔的 user_ids 字符串
            user_ids = sys.argv[2]
            extra_kwargs['user_ids'] = user_ids

    process.crawl(mode_to_spider[mode], **extra_kwargs)
    # the script will block here until the crawling is finished
    process.start()
