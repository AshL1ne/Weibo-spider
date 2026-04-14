#!/usr/bin/env python
# encoding: utf-8
"""
移动端用户信息采集爬虫
【毕设优化版】支持批量用户ID输入，全量节点基础信息采集
基于移动端API，避免PC端反爬机制
"""
import json
import time
import random
from scrapy import Spider
from scrapy.http import Request
from .seed_user_config import SEED_USERS, CRAWL_DELAY


class UserMobileSpider(Spider):
    """
    移动端用户信息采集
    命令行示例：scrapy crawl user_mobile -a user_ids=123456,789012 -a user_type=normal
    """
    name = "user_mobile_spider"

    def __init__(self, user_ids=None, user_type='normal', **kwargs):
        super().__init__(**kwargs)
        # 初始化用户ID到标签的映射
        self.user_id_to_type = {}
        if user_ids:
            # 如果通过命令行传入用户ID，使用统一的标签
            user_id_list = user_ids.split(',')
            for uid in user_id_list:
                self.user_id_to_type[uid] = user_type
        else:
            # 使用配置文件，保持标签区分
            for uid in SEED_USERS["normal"]:
                self.user_id_to_type[uid] = "normal"
            for uid in SEED_USERS["malicious"]:
                self.user_id_to_type[uid] = "malicious"

        # 获取所有用户ID
        self.user_ids = list(self.user_id_to_type.keys())
        random.shuffle(self.user_ids)

        self.batch_size = CRAWL_DELAY["batch_size"]
        self.delay_min = CRAWL_DELAY["min"]
        self.delay_max = CRAWL_DELAY["max"]

    def start_requests(self):
        """
        爬虫入口
        """
        for i in range(0, len(self.user_ids), self.batch_size):
            batch = self.user_ids[i:i + self.batch_size]
            for user_id in batch:
                url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={user_id}"
                time.sleep(random.uniform(self.delay_min, self.delay_max))
                yield Request(
                    url,
                    callback=self.parse_user_info,
                    meta={
                        'user_id': user_id,
                        'user_type': self.user_id_to_type[user_id],
                        'retry_count': 0,
                        'max_retries': 2
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

    def parse_user_info(self, response):
        """
        解析用户信息，新增样本类型标注
        """
        try:
            data = json.loads(response.text)
            user_id = response.meta['user_id']
            user_type = response.meta['user_type']

            if data.get('ok') != 1:
                self.logger.warning(f"用户 {user_id} 信息获取失败")
                return

            user_info = data.get('data', {}).get('userInfo', {})
            if user_info:
                item = self.parse_user_data(user_info, user_type)
                yield item
        except json.JSONDecodeError:
            self.logger.error(f"JSON解析失败: {response.text[:200]}")
        except Exception as e:
            self.logger.error(f"解析用户信息失败: {e}")

    def parse_user_data(self, data, user_type):
        """
        解析移动端用户信息，新增样本标签
        """
        item = {
            '_id': str(data.get('id', '')),
            'user_type': user_type,  # 新增：用户类型标注 normal/malicious/unknown
            'nick_name': data.get('screen_name', ''),
            # 头像图片url，没必要
            # 'avatar_hd': data.get('profile_image_url', ''),
            'verified': data.get('verified', False),
            'description': data.get('description', ''),
            'followers_count': data.get('followers_count', 0),
            'follow_count': data.get('follow_count', 0),
            'statuses_count': data.get('statuses_count', 0),
            'gender': data.get('gender', ''),
            # 移动端接口不包含
            #'location': data.get('location', ''),
            'mbrank': data.get('mbrank', 0),
            'mbtype': data.get('mbtype', 0),
            # 移动端接口不包含
            # 'created_at': data.get('created_at', ''),
            # 没啥用
            # 'crawl_time': int(time.time()),
            # 'spider_name': self.name,
            # 'data_source': 'mobile_weibo',
        }
        if data.get('verified'):
            item['verified_type'] = data.get('verified_type', -1)
            # item['verified_reason'] = data.get('verified_reason', '')
        return item