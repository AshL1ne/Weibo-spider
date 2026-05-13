# -*- coding: utf-8 -*-

"""
python run_spider.py user_mobile
python run_spider.py fan_mobile
python run_spider.py follow_mobile
python run_spider.py tweet_mobile
"""

BOT_NAME = 'spider'

SPIDER_MODULES = ['spiders']
NEWSPIDER_MODULE = 'spiders'

ROBOTSTXT_OBEY = False

with open('cookie.txt', 'rt', encoding='utf-8') as f:
    cookie = f.read().strip()
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
    'Referer': 'https://m.weibo.cn/',
    # 'Referer': 'https://weibo.com/',
    'X-Requested-With': 'XMLHttpRequest',
    # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Cookie': cookie
}

#CONCURRENT_REQUESTS = 16

#DOWNLOAD_DELAY = 1

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None,
    'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': None,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 101,
}

ITEM_PIPELINES = {
    'pipelines.JsonWriterPipeline': 300,
}



CONCURRENT_REQUESTS = 1  # 减少并发，避免被封IP
DOWNLOAD_DELAY = 8  # 增加延迟
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 30
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5

# 增加内存控制
SCHEDULER_MEMORY_QUEUE = 'scrapy.squeues.FifoMemoryQueue'
SCHEDULER_DISK_QUEUE = 'scrapy.squeues.PickleFifoDiskQueue'
SCHEDULER_PRIORITY_QUEUE = 'scrapy.pqueues.DownloaderAwarePriorityQueue'

# 增加重试设置
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408]  # 去掉403，403重试无效
RETRY_PRIORITY_ADJUST = -1

def check_cookie_validity(spider, response):
    if 'passport.weibo.com' in response.url or 'login.sina.com.cn' in response.url:
        spider.logger.error("Cookie已失效，需要重新登录！")