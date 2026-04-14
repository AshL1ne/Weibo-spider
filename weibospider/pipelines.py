# -*- coding: utf-8 -*-
import datetime
import json
import os.path
import time


class JsonWriterPipeline(object):
    """
    写入json文件的pipline
    """

    def __init__(self):
        self.file = None
        self.item_count = 0
        if not os.path.exists('../output'):
            os.mkdir('../output')

    def process_item(self, item, spider):
        """
        处理item
        """
        if not self.file:
            now = datetime.datetime.now()
            file_name = f"{spider.name}_{now.strftime('%Y%m%d_%H%M%S')}.jsonl"
            self.file = open(f'../output/{file_name}', 'wt', encoding='utf-8')

        # 添加统一的元数据
        # item['crawl_time'] = int(time.time())
        # item['spider_name'] = spider.name

        # 格式化输出
        line = json.dumps(dict(item), ensure_ascii=False,
                          separators=(',', ':')) + "\n"
        self.file.write(line)
        self.file.flush()

        # 每1000条数据记录一次
        self.item_count += 1
        if self.item_count % 1000 == 0:
            spider.logger.info(f"已采集 {self.item_count} 条数据")

        return item

    def close_spider(self, spider):
        if self.file:
            self.file.close()
            spider.logger.info(f"爬虫结束，共采集 {self.item_count} 条数据")