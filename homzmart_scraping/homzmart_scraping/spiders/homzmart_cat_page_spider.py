from gc import callbacks
from sys import dont_write_bytecode
import sys
sys.path.append('/home/oelmaria/python_projects/homzmart_project/homzmart_scraping') # OR Insert this in the terminal --> export PYTHONPATH="${PYTHONPATH}:/home/oelmaria/homzmart_scraping/homzmart_scraping"
import scrapy
from scrapy_playwright.page import PageCoroutine, PageMethod
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from homzmart_scraping.items import CatPageItem
from scrapy.loader import ItemLoader
import json

# Access the output of the "homzmart_home_page_spider" script stored in the JSON file 'Output_Home_Page.json'
with open('Output_Home_Page.json', 'r') as file:
    data = json.load(file)

urls_from_home_page = [d['cat_url'] for d in data] # No need to define first_url in the spider class below anymore as we are reading the output of the previous script

class CatPageSpider(scrapy.Spider): # Extract the sub-cateogry names and URLs from the category pages
    name = 'cat_page_spider'
    allowed_domains = ['homzmart.com']
    custom_settings = {"FEEDS":{"Output_Cat_Page.json":{"format":"json", "overwrite": True}}}

    def start_requests(self):
        for url in urls_from_home_page:
            yield scrapy.Request(url, callback = self.parse, meta = dict(
                playwright = True,
                playwright_include_page = True,
                playwright_page_methods = [PageMethod('wait_for_selector', 'div[role=tabpanel]')]
            ))
    
    async def parse(self, response):
        for sub_cat in response.css('div[role=tabpanel]'):
            l = ItemLoader(item = CatPageItem(), selector = sub_cat)
            l.add_css('sub_cat_name', 'a div.header::text')
            l.add_css('sub_cat_url', 'a::attr(href)')
            l.add_value('response_url', response.url)

            yield l.load_item()

#Run the spider
process = CrawlerProcess(settings = {
    # Playwright
    "DOWNLOAD_HANDLERS": {
        "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    },
    "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    
    # Rotating through proxies and user agents
    "PROXY_POOL_ENABLED": True,
    "DOWNLOADER_MIDDLEWARES": {
        'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
        'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,
        'scrapy_proxy_pool.middlewares.ProxyPoolMiddleware': 610,
        'scrapy_proxy_pool.middlewares.BanDetectionMiddleware': 620,
    },
    "CONCURRENT_REQUESTS_PER_IP": 32,
    "CONCURRENT_REQUESTS": 32,
    "COOKIES_ENABLED": False,
    "DOWNLOAD_DELAY": 3,
    "ROBOTSTXT_OBEY": False, # Saves one API call

    # Autothrottling and being polite to the server
    "AUTOTHROTTLE_ENABLED": True,
    # The initial download delay
    "AUTOTHROTTLE_START_DELAY": 5,
    # The maximum download delay to be set in case of high latencies
    "AUTOTHROTTLE_MAX_DELAY": 60,
    # The average number of requests Scrapy should be sending in parallel to each remote server
    "AUTOTHROTTLE_TARGET_CONCURRENCY": 1,
    # Enable showing throttling stats for every response received:
    "AUTOTHROTTLE_DEBUG": True
})
process.crawl(CatPageSpider)
process.start()