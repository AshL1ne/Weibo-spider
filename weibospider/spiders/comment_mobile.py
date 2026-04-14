#!/usr/bin/env python
# encoding: utf-8
"""
移动端评论采集爬虫
【毕设优化版】支持分页采集、批量博文ID输入，完善评论特征提取
基于移动端API，避免PC端反爬机制
"""
import json
import time
import random
from scrapy import Spider
from scrapy.http import Request
from .seed_user_config import CRAWL_PAGES, CRAWL_DELAY


class CommentMobileSpider(Spider):
    """
    移动端评论采集
    命令行示例：scrapy crawl comment_mobile -a tweet_ids=123456,789012 -a max_pages=3
    """
    name = "comment_mobile_spider"

    def __init__(self, tweet_ids=None, max_pages=None, **kwargs):
        super().__init__(**kwargs)
        # 初始化博文ID列表
        if tweet_ids:
            self.tweet_ids = tweet_ids.split(',')
        else:
            self.tweet_ids = []

        self.max_pages = int(max_pages) if max_pages else CRAWL_PAGES["tweet_comment"]
        random.shuffle(self.tweet_ids)
        self.batch_size = CRAWL_DELAY["batch_size"]
        self.delay_min = CRAWL_DELAY["min"]
        self.delay_max = CRAWL_DELAY["max"]

    def start_requests(self):
        """
        爬虫入口
        """
        for i in range(0, len(self.tweet_ids), self.batch_size):
            batch = self.tweet_ids[i:i + self.batch_size]
            for tweet_id in batch:
                url = f"https://m.weibo.cn/api/comments/show?id={tweet_id}&page=1"
                time.sleep(random.uniform(self.delay_min, self.delay_max))
                yield Request(
                    url,
                    callback=self.parse_comment_list,
                    meta={
                        'tweet_id': tweet_id,
                        'page': 1,
                        'max_pages': self.max_pages,
                    },
                    headers=self.get_mobile_headers()
                )

    def get_mobile_headers(self):
        return {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
            'Referer': 'https://m.weibo.cn/',
            'X-Requested-With': 'XMLHttpRequest',
        }

    def parse_comment_list(self, response):
        """
        解析评论列表，分页逻辑
        """
        try:
            data = json.loads(response.text)
            tweet_id = response.meta['tweet_id']
            current_page = response.meta['page']
            max_pages = response.meta['max_pages']

            self.logger.info(f"正在采集博文 {tweet_id} 第 {current_page} 页评论")

            if data.get('ok') != 1:
                self.logger.warning(f"博文 {tweet_id} 第 {current_page} 页评论获取失败")
                return

            # 解析评论数据
            comments = data.get('data', {}).get('data', [])
            for comment in comments:
                item = self.parse_comment_data(tweet_id, comment)
                yield item

            # 分页逻辑
            max_page = data.get('data', {}).get('max', 0)
            if current_page < max_pages and current_page < max_page:
                next_page = current_page + 1
                next_url = f"https://m.weibo.cn/api/comments/show?id={tweet_id}&page={next_page}"
                time.sleep(random.uniform(self.delay_min, self.delay_max))
                yield Request(
                    next_url,
                    callback=self.parse_comment_list,
                    meta={
                        'tweet_id': tweet_id,
                        'page': next_page,
                        'max_pages': max_pages,
                    },
                    headers=self.get_mobile_headers()
                )
            else:
                self.logger.info(f"博文 {tweet_id} 评论采集完成，共采集 {current_page} 页")

        except json.JSONDecodeError:
            self.logger.error(f"JSON解析失败: {response.text[:200]}")
        except Exception as e:
            self.logger.error(f"解析评论列表失败: {e}")

    def parse_comment_data(self, tweet_id, comment_data):
        """
        解析评论数据，完善特征字段
        """
        item = {
            '_id': str(comment_data.get('id', '')),
            'tweet_id': tweet_id,
            'created_at': comment_data.get('created_at', ''),
            'like_counts': comment_data.get('like_counts', 0),
            'content': comment_data.get('text', '').replace('\u200b', ''),
            'is_reply': comment_data.get('reply_comment') is not None,
            'crawl_time': int(time.time()),
            'spider_name': self.name,
            'data_source': 'mobile_weibo',
        }
        # 评论用户信息
        user = comment_data.get('user', {})
        if user:
            item['comment_user'] = {
                '_id': str(user.get('id', '')),
                'nick_name': user.get('screen_name', ''),
                'avatar_hd': user.get('profile_image_url', ''),
                'verified': user.get('verified', False),
                'followers_count': user.get('followers_count', 0),
                'friends_count': user.get('friends_count', 0),
                'statuses_count': user.get('statuses_count', 0),
            }
        # 回复信息
        reply_comment = comment_data.get('reply_comment', {})
        if reply_comment:
            item['reply_info'] = {
                'reply_id': str(reply_comment.get('id', '')),
                'reply_user_id': str(reply_comment.get('user', {}).get('id', '')),
                'reply_content': reply_comment.get('text', ''),
            }
        return item