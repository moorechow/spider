#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Project : spider
@File    : redis_monitor.py
@Author  : Moore
@Date    : 2025/11/11 16:45
@Desc    : 
"""
import redis
import json
import sys

def monitor_redis():
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

        r.ping()
        print("Connected Redis successfully...")

        # 获取统计信息
        total_urls = r.llen('sina:news:urls')
        unique_urls = r.scard('sina:news:dupefilter')

        print(f"待爬取URL数量: {total_urls}")
        print(f"唯一URL数量: {unique_urls}")

        # 显示最新的几个URL
        if total_urls > 0:
            print("\n最新5个URL:")
            recent_urls = r.lrange('sina:news:urls', 0, 4)
            for i, url_data in enumerate(recent_urls):
                data = json.loads(url_data)
                print(f"{i+1}. {data.get('title', '无标题')}")
                print(f"   URL: {data.get('url')}")
                print(f"   时间: {data.get('publish_time', '未知')}")
                print()

    except Exception as e:
        print("Redis数据库的信息爬取错误:", e)
        sys.exit(1)

if __name__ == '__main__':
    monitor_redis()