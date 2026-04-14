#!/usr/bin/env python
# encoding: utf-8
"""
移动端粉丝关系采集爬虫
【毕设优化版】支持since_id分页、层级采集、批量用户ID输入
基于移动端API，避免PC端反爬机制
【已优化】用户信息与user_mobile.py完全对齐
"""
import json
import time
import random
from scrapy import Spider
from scrapy.http import Request
from .seed_user_config import CRAWL_PAGES, CRAWL_DELAY, SEED_USERS


class FanMobileSpider(Spider):
    """
    移动端粉丝关系采集
    命令行示例：scrapy crawl fan_mobile -a user_ids=123456,789012 -a max_pages=2 -a level=1
    """
    name = "fan_mobile_spider"

    def __init__(self, user_ids=None, max_pages=None, level=0, **kwargs):
        super().__init__(**kwargs)
        if user_ids:
            self.user_ids = user_ids.split(',')
        else:
            self.user_ids = SEED_USERS["normal"] + SEED_USERS["malicious"]
        self.max_pages = int(max_pages) if max_pages else CRAWL_PAGES.get("seed_fan", 2)
        self.node_level = int(level)
        random.shuffle(self.user_ids)
        self.batch_size = CRAWL_DELAY["batch_size"]
        self.delay_min = CRAWL_DELAY["min"]
        self.delay_max = CRAWL_DELAY["max"]

    def start_requests(self):
        for i in range(0, len(self.user_ids), self.batch_size):
            batch = self.user_ids[i:i + self.batch_size]
            for user_id in batch:
                containerid = f"231051_-_fans_-_{user_id}"
                url = f"https://m.weibo.cn/api/container/getIndex?containerid={containerid}&since_id=1"
                time.sleep(random.uniform(self.delay_min, self.delay_max))
                yield Request(
                    url,
                    callback=self.parse_fan_list,
                    meta={
                        'user_id': user_id,
                        'containerid': containerid,
                        'current_page': 1,
                        'max_pages': self.max_pages,
                        'node_level': self.node_level
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

    def parse_user_data(self, data, user_type='unknown'):
        """
        【与user_mobile.py完全一致的用户信息解析逻辑】
        保证用户字段100%对齐
        """
        item = {
            '_id': str(data.get('id', '')),
            'user_type': user_type,
            'nick_name': data.get('screen_name', ''),
            # 'avatar_hd': data.get('profile_image_url', ''),
            'verified': data.get('verified', False),
            'description': data.get('description', ''),
            'followers_count': data.get('followers_count', 0),
            'follow_count': data.get('follow_count', 0),
            'statuses_count': data.get('statuses_count', 0),
            'gender': data.get('gender', ''),
            # 'location': data.get('location', ''),
            'mbrank': data.get('mbrank', 0),
            'mbtype': data.get('mbtype', 0),
            # 'created_at': data.get('created_at', ''),
            # 'crawl_time': int(time.time()),
            # 'spider_name': self.name,
            # 'data_source': 'mobile_weibo',
        }

        if data.get('verified'):
            item['verified_type'] = data.get('verified_type', -1)
            # item['verified_reason'] = data.get('verified_reason', '')
        return item

    def parse_fan_list(self, response):
        try:
            data = json.loads(response.text)
            user_id = response.meta['user_id']
            current_page = response.meta['current_page']
            max_pages = response.meta['max_pages']
            node_level = response.meta['node_level']
            self.logger.info(f"正在采集用户 {user_id} 第 {current_page} 页粉丝列表，节点层级：{node_level}")

            if data.get('ok') != 1:
                self.logger.warning(f"用户 {user_id} 第 {current_page} 页粉丝列表获取失败，终止分页")
                return

            cards = data.get('data', {}).get('cards', [])
            has_valid_data = False

            for card in cards:
                card_group = card.get('card_group', [])
                for user_card in card_group:
                    user_info = user_card.get('user', {})
                    if user_info:
                        has_valid_data = True
                        # 1. 输出与user_mobile.py完全一致的用户信息item
                        user_item = self.parse_user_data(user_info)
                        yield user_item
                        # 2. 输出原有的粉丝关系item，内部fan_info与用户字段对齐
                        relation_item = self.parse_fan_relation(user_id, user_info, node_level)
                        yield relation_item

            if not has_valid_data:
                self.logger.info(f"用户 {user_id} 第 {current_page} 页无有效数据，分页结束")
                return

            # 核心分页逻辑
            cardlist_info = data.get('data', {}).get('cardlistInfo', {})
            next_since_id = cardlist_info.get('since_id')
            if current_page < max_pages and next_since_id:
                next_page = current_page + 1
                next_url = f"https://m.weibo.cn/api/container/getIndex?containerid={response.meta['containerid']}&since_id={next_since_id}"
                time.sleep(random.uniform(self.delay_min, self.delay_max))
                yield Request(
                    next_url,
                    callback=self.parse_fan_list,
                    meta={
                        'user_id': user_id,
                        'containerid': response.meta['containerid'],
                        'current_page': next_page,
                        'max_pages': max_pages,
                        'node_level': node_level
                    },
                    headers=self.get_mobile_headers()
                )
            else:
                self.logger.info(f"用户 {user_id} 粉丝列表采集完成，共采集 {current_page} 页")
        except json.JSONDecodeError:
            self.logger.error(f"JSON解析失败: {response.text[:200]}")
        except Exception as e:
            self.logger.error(f"解析粉丝列表失败: {str(e)}")

    def parse_fan_relation(self, followed_id, user_data, node_level):
        """
        解析粉丝关系，fan_info字段与user_mobile.py用户结构完全对齐
        """
        # 复用统一的用户解析逻辑，保证字段100%一致
        full_user_info = self.parse_user_data(user_data)
        item = {
            '_id': f"{followed_id}_{user_data.get('id', '')}",
            'followed_id': followed_id,
            'fan_id': str(user_data.get('id', '')),
            'node_level': node_level,
            'source_user_type': 'seed' if node_level == 0 else 'neighbor',
            'fan_info': full_user_info,  # 与user_mobile完全一致的用户信息
            'relation_type': 'fan',
            # 'crawl_time': int(time.time()),
            # 'spider_name': self.name,
            # 'data_source': 'mobile_weibo',
        }
        return item