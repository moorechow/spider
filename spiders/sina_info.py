import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

import scrapy
from scrapy import cmdline, Spider
from scrapy.http import HtmlResponse,Request
from scrapy.exceptions import CloseSpider
from urllib.parse import urlencode
from sina_news.items import SinaNewsItem
import time
import json
import re

class SinaInfoSpider(scrapy.Spider):
    name = "sina_info"
    # 定义板块优先级（数值越小优先级越高）
    section_priority = {
        '国内新闻': 1000,
        # '国际新闻': 1001,
        # '体育新闻': 1002,
        # '科技新闻': 1003
    }
    def __init__(self):
        super().__init__()
        self.max_page = 100
        self.news_num = 20
        # 爬取页数范围,暂定1-5页
        self.start_page = 124
        self.end_page = 200
        # 添加连续空数据计数器
        self.empty_data_count = 0
        self.empty_count = 3

    def start_requests(self):
        """生成初始请求"""
        base_params = {
            'pageid': '121',
            'lid': '1356',
            'num': self.news_num,
            'versionNumber': '1.2.4',
            'encode': 'utf-8',
            'callback': 'feedCardJsonpCallback',
        }

        # start_urls = [#('国内新闻',"https://news.sina.com.cn/china/"),
        #               # ('国际新闻',"https://news.sina.com.cn/world/"),
        #               # ('体育新闻',"https://sports.sina.com.cn/"),
        #               # ('科技新闻',"https://tech.sina.com.cn/")
        #                 ('国内新闻', f"https://feed.sina.com.cn/api/roll/get?pageid=121&lid=1356&num=20&versionNumber=1.2.4&page={}&encode=utf-8&callback=feedCardJsonpCallback&_=1762736972625"),
        #               ]

        for page in range(int(self.start_page), int(self.end_page) + 1):
            # priority = self.section_priority[section_name]
            params = base_params.copy()
            params['page'] = int(page)
            params['_'] = str(int(time.time() * 1000))  # 时间戳
            url = f"https://feed.sina.com.cn/api/roll/get?{urlencode(params)}"

            yield scrapy.Request(
                            url=url,
                            callback=self.parse_section,
                            meta={'page': page},
                            headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                                'Referer': 'https://news.sina.com.cn/',
                                'Accept': 'application/json, text/javascript, */*; q=0.01',
                            },
                            dont_filter=True
                            #priority=priority
            )

    def parse_section(self, response: HtmlResponse):
        """解析API的响应信息"""
        page = response.meta['page']
        print(f"正在爬取第 {page} 页")

        # 处理JSONP响应
        json_data = self.parse_jsonp_response(response.text)
        # print("json数据:", json_data)
        if not json_data:
            print(f"爬取第 {page} 页失败")
            # 如果解析JSON失败，也视为空数据
            self.empty_data_count += 1
            if self.empty_data_count >= self.empty_count:
                raise CloseSpider(f"连续{self.empty_count}次获取数据失败，终止爬虫")
            return

        # 提取新闻数据
        news_list = self.extract_news_data(json_data)
        # print("新闻list:", news_list)
        if not news_list:
            print(f'第 {page} 页无数据')
            self.empty_data_count += 1
            if self.empty_data_count >= self.empty_count:
                raise CloseSpider(f"连续{self.empty_count}页无数据，终止爬虫")
            return
        else:
            # 重置计数器，因为获取到了数据
            self.empty_data_count = 0

        for news_item in news_list:
            item = self.process_news_item(news_item, page)
            print("item内容:", item['title'], item['url'])
            if item:
                yield item

    def parse_jsonp_response(self, text):
        """解析JSONP响应为JSON"""
        try:
            # print(f"原始响应长度: {len(text)}")
            # print(f"响应前300字符: {text[:300]}")

            # 方法1: 精确匹配JSONP回调函数，包含完整的JSON对象
            json_match = re.search(r'feedCardJsonpCallback\s*\(\s*(\{.*\})\s*\);?', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                # print(f"方法1匹配成功，JSON长度: {len(json_str)}")
                # print(f"JSON前200字符: {json_str[:200]}")

                # 清理可能的JavaScript注释或其他非JSON字符
                json_str = self.clean_json_string(json_str)

                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误: {e}")
                    print(f"错误位置: {e.pos}")
                    print(f"错误行: {json_str[max(0, e.pos-50):e.pos+50]}")
                    return None

            print("JSONP模式匹配失败")
            return None

        except Exception as e:
            print(f"JSON解析失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def clean_json_string(self, json_str):
        """清理JSON字符串中的非标准字符"""
        # 移除可能的JavaScript注释
        json_str = re.sub(r'//.*?\n', '', json_str)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)

        # 处理可能的尾随逗号
        json_str = re.sub(r',\s*}(?=,|\s|$)', '}', json_str)
        json_str = re.sub(r',\s*\](?=,|\s|$)', ']', json_str)

        # 处理可能的控制字符
        json_str = ''.join(char for char in json_str if ord(char) >= 32 or char in '\n\r\t')

        return json_str.strip()

            # 上面如果匹配不成功
            # json_match1 = re.search(r'\w+\s*\(\s*(\{.*\})\s*\)', text, re.DOTALL)
            # if json_match1:
            #     json_str = json_match1.group(1)
            #     print(f"方法2匹配成功，JSON长度: {len(json_str)}")
            #     return json.loads(json_str)

    def extract_news_data(self, data):
        """从API响应中提取新闻列表"""
        # 根据实际API响应结构调整提取逻辑
        extraction_paths = [
            data.get('result', {}).get('data', []),
            data.get('data', []),
            data.get('list', []),
        ]

        for path in extraction_paths:
            # print("path是:", path)
            if path and isinstance(path, list) and len(path) > 0:
                return path

        if isinstance(data, list):
            return data
        return []

    def process_news_item(self, news_data,page):
        """处理单个新闻项"""
        try:
            item = SinaNewsItem()

            # 基础信息
            item['docid'] = news_data.get('docid')
            item['title'] = news_data.get('title', '')
            item['url'] = news_data.get('url', '')
            item['wapurl'] = news_data.get('wapurl', '')

            # 时间信息
            item['publish_time'] = news_data.get('mtime')
            item['ctime'] = news_data.get('ctime')
            item['mtime'] = news_data.get('mtime')

            # 内容信息
            item['summary'] = news_data.get('summary', '')
            item['intro'] = news_data.get('intro', '')
            item['media_name'] = news_data.get('media_name', '')
            item['author'] = news_data.get('author', '')
            item['keywords'] = news_data.get('keywords', '')

            # 分类信息
            item['channelid'] = news_data.get('channelid', '')
            item['categoryid'] = news_data.get('categoryid', '')
            item['lids'] = news_data.get('lids', '')

            # 爬虫元数据
            item['crawl_time'] = time.time()
            item['page'] = page

            return item

        except Exception as e:
            self.logger.error(f'处理新闻项错误: {e}, 数据: {news_data}')
            return None

if __name__ == '__main__':
    os.chdir(project_root)
    cmdline.execute('scrapy crawl sina_info'.split())