#!/usr/bin/env python
# encoding: utf-8
"""
移动端微博数据采集
【毕设优化版】支持时间范围筛选、分页采集、批量用户ID输入，完善发文行为特征
专门为毕设"基于用户画像的恶意行为检测与可视分析"优化
"""
# import datetime
import json
import time
from datetime import datetime, timezone, timedelta
import random
from collections import defaultdict
from scrapy import Spider
from scrapy.http import Request
from .seed_user_config import CRAWL_PAGES, CRAWL_DELAY, SEED_USERS, TWEET_START_TIME, TWEET_END_TIME


class TweetMobileSpider(Spider):
    """
    移动端微博数据采集
    命令行示例：scrapy crawl tweet_mobile -a user_ids=123456,789012 -a max_pages=10
    """
    name = "tweet_mobile_spider"

    def __init__(self, user_ids=None, max_pages=None, **kwargs):
        super().__init__(**kwargs)
        # 初始化用户列表
        if user_ids:
            self.user_ids = user_ids.split(',')
        else:
            self.user_ids = SEED_USERS["normal"] + SEED_USERS["malicious"]

        self.max_pages = int(max_pages) if max_pages else CRAWL_PAGES["user_tweet"]
        self.start_time = TWEET_START_TIME
        self.end_time = TWEET_END_TIME
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
                    callback=self.parse_user_container,
                    meta={
                        'user_id': user_id,
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

    def parse_user_container(self, response):
        """
        解析用户容器信息，获取微博列表容器ID
        """
        try:
            data = json.loads(response.text)
            user_id = response.meta['user_id']
            if data.get('ok') != 1:
                self.logger.warning(f"用户 {user_id} 容器信息获取失败")
                return

            # 提取用户信息
            user_info = data.get('data', {}).get('userInfo', {})
            # 获取微博列表容器ID
            tabs = data.get('data', {}).get('tabsInfo', {}).get('tabs', [])
            weibo_tab = next((tab for tab in tabs if tab.get('title') == '微博'), None)

            if weibo_tab and weibo_tab.get('containerid'):
                containerid = weibo_tab.get('containerid')
                weibo_url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={user_id}&containerid={containerid}&page=1"
                time.sleep(random.uniform(self.delay_min, self.delay_max))
                yield Request(
                    weibo_url,
                    callback=self.parse_weibo_list,
                    meta={
                        'user_id': user_id,
                        'page': 1,
                        'max_pages': self.max_pages,
                        'containerid': containerid,
                        'user_info': user_info
                    },
                    headers=self.get_mobile_headers(),
                    priority=10
                )
        except json.JSONDecodeError:
            self.logger.error(f"JSON解析失败: {response.text[:200]}")
        except Exception as e:
            self.logger.error(f"解析用户容器失败: {e}")

    def parse_weibo_list(self, response):
        """
        解析微博列表，核心分页逻辑，时间范围过滤
        """
        try:
            data = json.loads(response.text)
            user_id = response.meta['user_id']
            current_page = response.meta['page']
            max_pages = response.meta['max_pages']
            containerid = response.meta['containerid']
            user_info = response.meta.get('user_info', {})

            self.logger.info(f"正在采集用户 {user_id} 第 {current_page} 页博文")

            if data.get('ok') != 1:
                self.logger.warning(f"用户 {user_id} 第 {current_page} 页博文获取失败")
                return

            cards = data.get('data', {}).get('cards', [])
            post_times = []
            has_valid_data = False
            out_of_time_range = False

            for card in cards:
                if card.get('card_type') == 9:  # 微博卡片固定类型
                    mblog = card.get('mblog', {})
                    if mblog:
                        # 时间范围过滤：仅采集配置时间范围内的博文
                        created_at_str = mblog.get('created_at', '')
                        try:
                            created_at = datetime.strptime(created_at_str, '%a %b %d %H:%M:%S %z %Y')                            # created_at = created_at.replace(tzinfo=None)

                            # 统一UTC时区，和配置时间精准匹配
                            if created_at < self.start_time:
                                out_of_time_range = True
                                break
                            if created_at > self.end_time:
                                continue
                            formatted_created_at = created_at.strftime('%Y-%m-%d %H:%M:%S')
                        except Exception as e:
                            self.logger.warning(f"时间解析失败 {created_at_str}: {e}")
                            continue

                        has_valid_data = True
                        item = self.parse_weibo_info(mblog, user_info)
                        post_times.append(created_at_str)
                        yield item

            # 超出时间范围，终止分页
            if out_of_time_range:
                self.logger.info(f"用户 {user_id} 博文已超出配置时间范围，终止采集")
                return

            # 无有效数据，终止分页
            if not has_valid_data:
                self.logger.info(f"用户 {user_id} 第 {current_page} 页无有效博文，终止采集")
                return

            # 分页逻辑
            if current_page < max_pages:
                next_page = current_page + 1
                next_url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={user_id}&containerid={containerid}&page={next_page}"
                time.sleep(random.uniform(self.delay_min, self.delay_max))
                yield Request(
                    next_url,
                    callback=self.parse_weibo_list,
                    meta={
                        'user_id': user_id,
                        'page': next_page,
                        'max_pages': max_pages,
                        'containerid': containerid,
                        'user_info': user_info
                    },
                    headers=self.get_mobile_headers()
                )
            else:
                self.logger.info(f"用户 {user_id} 博文采集完成，共采集 {current_page} 页")
                # 仅在全量采集完成后生成行为摘要，避免重复/错误计算
                total_post_times = post_times + response.meta.get('post_times', [])
                total_count = len(post_times) + response.meta.get('total_tweet_count', 0)
                if total_post_times and total_count > 1:
                    yield self.generate_behavior_summary(user_id, total_post_times, total_count)



        except json.JSONDecodeError:
            self.logger.error(f"微博列表JSON解析失败: {response.text[:200]}")
        except Exception as e:
            self.logger.error(f"解析微博列表失败: {e}")

    def generate_behavior_summary(self, user_id, post_times, tweet_count):
        """
        生成用户发文行为特征摘要（毕设核心：用于用户画像与GCN节点特征）
        """
        hours = []
        valid_dates = []
        for time_str in post_times:
            try:
                dt = datetime.strptime(time_str, '%a %b %d %H:%M:%S %z %Y')
                hours.append(dt.hour)
                valid_dates.append(dt.date())
            except:
                continue
        if not valid_dates:
            return None

        hour_distribution = defaultdict(int)
        for hour in hours:
            hour_distribution[hour] += 1
        active_hours = sorted(hour_distribution.items(), key=lambda x: x[1], reverse=True)[:3]

        # 修正日均发文数：按实际采集的时间跨度计算，而非固定180天
        date_span = (max(valid_dates) - min(valid_dates)).days + 1
        avg_tweets_per_day = round(tweet_count / date_span, 4) if date_span > 0 else 0

        return {
            'user_id': user_id,
            'data_type': 'behavior_summary',
            'tweet_count': tweet_count,
            'active_hours': [{'hour': h, 'count': c} for h, c in active_hours],
            'avg_tweets_per_day': avg_tweets_per_day,
            'date_span_days': date_span,
            # 'crawl_time': int(time.time()),
            # 'spider_name': self.name,
        }

    # 新增长文本解析方法
    def parse_long_tweet(self, response):
        try:
            data = json.loads(response.text)
            if data.get('ok') == 1:
                item = response.meta['item']
                item['content'] = data.get('data', {}).get('longTextContent', item['content']).replace('\u200b', '')
                yield item
        except Exception as e:
            self.logger.error(f"长文本解析失败: {e}")
            yield response.meta['item']

    def parse_weibo_info(self, mblog, user_info):
        """
        解析单条微博信息，完善特征字段
        """
        item = {
            '_id': str(mblog.get('id', '')),
            # 'mblogid': mblog.get('mblogid', ''),
            'user_id': str(mblog.get('user', {}).get('id', '')),
            'created_at': mblog.get('created_at', ''),
             'reposts_count': mblog.get('reposts_count', 0),
            #'comments_count': mblog.get('comments_count', 0),
             'attitudes_count': mblog.get('attitudes_count', 0),
            # 'source': mblog.get('source', ''),
            'content': mblog.get('text', '').replace('\u200b', ''),
            'is_retweet': mblog.get('retweeted_status') is not None,

             'is_long_text': mblog.get('isLongText', False),

            # 'crawl_time': int(time.time()),
            # 'spider_name': self.name,
            # 'data_source': 'mobile_weibo',
        }
        # 用户信息
        # 没必要，上面有user_id了
        # if user_info:
        #     item['user_info'] = {
        #         '_id': str(user_info.get('id', '')),
        #         'nick_name': user_info.get('screen_name', ''),
        #         'verified': user_info.get('verified', False),
        #         'followers_count': user_info.get('followers_count', 0),
        #         'friends_count': user_info.get('friends_count', 0),
        #         'statuses_count': user_info.get('statuses_count', 0),
        #     }

        #     不考虑收集
        # # 图片信息
        # pics = mblog.get('pics', [])
        # if pics:
        #     item['pic_urls'] = [pic.get('url', '') for pic in pics if pic.get('url')]
        #     item['pic_num'] = len(item['pic_urls'])
        # # 视频信息
        # page_info = mblog.get('page_info', {})
        # if page_info and page_info.get('type') == 'video':
        #     item['video'] = page_info.get('media_info', {}).get('stream_url', '')
        #     item['video_online_numbers'] = page_info.get('media_info', {}).get('online_users_number', 0)

        # 转发微博信息
        retweeted = mblog.get('retweeted_status')
        if retweeted:
            item['retweet_info'] = {
                '_id': str(retweeted.get('id', '')),
                'user_id': str(retweeted.get('user', {}).get('id', '')),
                'content': retweeted.get('text', ''),
                'is_long_text': retweeted.get('isLongText', False),
            }
            # 长文本发起单独请求
            if item['is_long_text']:
                long_text_url = f"https://m.weibo.cn/statuses/extend?id={item['_id']}"
                time.sleep(random.uniform(self.delay_min, self.delay_max))
                return Request(
                    long_text_url,
                    callback=self.parse_long_tweet,
                    meta={'item': item},
                    headers=self.get_mobile_headers(),
                    priority=20
                )
        return item
