# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import TakeFirst, MapCompose
from datetime import datetime
import re

def clean_title(title: str):
    """清洗标题，处理Unicode转义字符"""
    if '\\u' in title:
        try:
            title = title.encode('utf-8').decode('unicode_escape')
        except:
            pass

    return title.strip()

def timestamp_to_datetime(timestamp_str):
    """时间戳转datetime对象"""
    if timestamp_str and timestamp_str.is_digit():
        return datetime.fromtimestamp(int(timestamp_str))
    return None

class SinaNewsItem(scrapy.Item):
    # 基本信息
    docid = scrapy.Field(output_processor=TakeFirst())
    title = scrapy.Field(
        input_processor=MapCompose(clean_title),
        output_processor=TakeFirst()
    )
    url = scrapy.Field(output_processor=TakeFirst())
    wapurl = scrapy.Field(output_processor=TakeFirst())

    # 时间信息
    publish_time = scrapy.Field(
        input_processor=MapCompose(timestamp_to_datetime),
        output_processor=TakeFirst()
    )
    ctime = scrapy.Field(output_processor=TakeFirst())
    mtime = scrapy.Field(output_processor=TakeFirst())

    # 内容信息
    summary = scrapy.Field(output_processor=TakeFirst())
    intro = scrapy.Field(output_processor=TakeFirst())
    media_name = scrapy.Field(output_processor=TakeFirst())
    author = scrapy.Field(output_processor=TakeFirst())
    keywords = scrapy.Field(output_processor=TakeFirst())

    # 分类信息
    channelid = scrapy.Field(output_processor=TakeFirst())
    categoryid = scrapy.Field(output_processor=TakeFirst())
    lids = scrapy.Field(output_processor=TakeFirst())

    # 爬虫元数据
    crawl_time = scrapy.Field(output_processor=TakeFirst())
    page = scrapy.Field(output_processor=TakeFirst())
