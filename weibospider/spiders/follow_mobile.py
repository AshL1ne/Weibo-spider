#!/usr/bin/env python
# encoding: utf-8

# 支持since_id分页、层级采集、批量用户ID输入

import json
import time
import random
from scrapy import Spider
from scrapy.http import Request
# 导入统一配置
from .seed_user_config import CRAWL_PAGES, CRAWL_DELAY, SEED_USERS


class FollowMobileSpider(Spider):

    name = "follow_mobile_spider"

    def __init__(self, user_ids=None, max_pages=None, **kwargs):
        super().__init__(**kwargs)
        # 初始化用户列表：优先命令行传入，否则使用种子正常用户
        if user_ids:
            self.user_ids = user_ids.split(',')
        else:
            self.user_ids = SEED_USERS["normal"] + SEED_USERS["malicious"]
        # 初始化采集页数：优先命令行传入，否则使用配置
        self.max_pages = int(max_pages) if max_pages else CRAWL_PAGES["seed_follow"]
        # # 节点层级标签：0=种子用户，1=一阶邻居，2=二阶邻居
        # self.node_level = int(level)
        # 随机打乱用户顺序，避免模式化
        random.shuffle(self.user_ids)
        self.batch_size = CRAWL_DELAY["batch_size"]
        self.delay_min = CRAWL_DELAY["min"]
        self.delay_max = CRAWL_DELAY["max"]

    def start_requests(self):

        # 分批处理用户，降低风控风险
        for i in range(0, len(self.user_ids), self.batch_size):
            batch = self.user_ids[i:i + self.batch_size]
            for user_id in batch:
                # 移动端关注接口containerid固定格式
                containerid = f"231051_-_followers_-_{user_id}"
                # 第一页固定since_id=1
                url = f"https://m.weibo.cn/api/container/getIndex?containerid={containerid}&since_id=1"
                # 添加随机延迟
                time.sleep(random.uniform(self.delay_min, self.delay_max))
                yield Request(
                    url,
                    callback=self.parse_follow_list,
                    meta={
                        'user_id': user_id,
                        'containerid': containerid,
                        'current_page': 1,
                        'max_pages': self.max_pages,
                        # 'node_level': self.node_level
                    },
                    headers=self.get_mobile_headers()
                )

    # 获取移动端标准请求头
    def get_mobile_headers(self):

        return {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
            'Referer': 'https://m.weibo.cn/',
            'X-Requested-With': 'XMLHttpRequest',
        }

    # 解析用户数据，对齐user_mobile.py的用户信息结构
    def parse_user_data(self, data, user_type='unknown'):

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

        }

        # 认证就行
        # if data.get('verified'):
        #     item['verified_type'] = data.get('verified_type', -1)
        #     # item['verified_reason'] = data.get('verified_reason', '')
        return item

    # 解析关注列表，核心分页逻辑
    def parse_follow_list(self, response):

        try:
            data = json.loads(response.text)
            user_id = response.meta['user_id']
            current_page = response.meta['current_page']
            max_pages = response.meta['max_pages']
            self.logger.info(f"正在采集用户 {user_id} 第 {current_page} 页关注列表")

            # 请求失败处理
            if data.get('ok') != 1:
                self.logger.warning(f"用户 {user_id} 第 {current_page} 页关注列表获取失败，终止分页")
                return

            # 解析当前页关注用户数据
            cards = data.get('data', {}).get('cards', [])
            has_valid_data = False
            for card in cards:
                card_group = card.get('card_group', [])
                for user_card in card_group:
                    user_info = user_card.get('user', {})
                    if user_info:
                        has_valid_data = True
                        # # 1. 输出与user_mobile.py完全一致的用户信息item
                        # user_item = self.parse_user_data(user_info)
                        # yield user_item
                        # 2. 输出原有的关注关系item，内部follow_info与用户字段对齐
                        relation_item = self.parse_follow_relation(user_id, user_info)
                        yield relation_item

            # 无数据时终止分页
            if not has_valid_data:
                self.logger.info(f"用户 {user_id} 第 {current_page} 页无有效数据，分页结束")
                return

            # 获取下一页since_id（微博移动端分页专用参数）
            cardlist_info = data.get('data', {}).get('cardlistInfo', {})
            next_since_id = cardlist_info.get('since_id')

            # # 调试，检测接口是否返回since_id
            # self.logger.debug(f"用户 {user_id} 第 {current_page} 页 cardlistInfo: {cardlist_info}, since_id: {next_since_id}")

            # 未到最大页数+有下一页ID，继续采集
            if current_page < max_pages and next_since_id:
                next_page = current_page + 1
                next_url = f"https://m.weibo.cn/api/container/getIndex?containerid={response.meta['containerid']}&since_id={next_since_id}"
                # 随机延迟
                time.sleep(random.uniform(self.delay_min, self.delay_max))
                self.logger.info(f"准备采集用户 {user_id} 第 {next_page} 页，since_id={next_since_id}")
                yield Request(
                    next_url,
                    callback=self.parse_follow_list,
                    meta={
                        'user_id': user_id,
                        'containerid': response.meta['containerid'],
                        'current_page': next_page,
                        'max_pages': max_pages,
                        # 'node_level': node_level
                    },
                    headers=self.get_mobile_headers()
                )
            else:
                self.logger.info(f"用户 {user_id} 关注列表采集完成，共采集 {current_page} 页")
        except json.JSONDecodeError:
            self.logger.error(f"JSON解析失败: {response.text[:200]}")
        except Exception as e:
            self.logger.error(f"解析关注列表失败: {str(e)}")


    def parse_follow_relation(self, fan_id, user_data):

        # 复用统一的用户解析逻辑，保证字段100%一致
        full_user_info = self.parse_user_data(user_data)
        item = {
            '_id': f"{fan_id}_{user_data.get('id', '')}",
            'fan_id': fan_id,
            'follow_id': str(user_data.get('id', '')),
            # 'node_level': node_level,
            # 'source_user_type': 'seed' if node_level == 0 else 'neighbor',
            'follow_info': full_user_info,  # 与user_mobile完全一致的用户信息
            'relation_type': 'follow',
            # 'crawl_time': int(time.time()),
            # 'spider_name': self.name,
            # 'data_source': 'mobile_weibo',
        }
        return item