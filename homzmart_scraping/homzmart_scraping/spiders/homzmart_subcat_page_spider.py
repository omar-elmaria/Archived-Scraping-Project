from gc import callbacks
from sys import dont_write_bytecode
import sys
sys.path.append('/home/oelmaria/python_projects/homzmart_project/homzmart_scraping') # OR Insert this in the terminal --> export PYTHONPATH="${PYTHONPATH}:/home/oelmaria/homzmart_scraping/homzmart_scraping"
import scrapy
from scrapy_playwright.page import PageCoroutine, PageMethod
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from homzmart_scraping.items import SubCatPageItem
from scrapy.loader import ItemLoader
import json
from unidecode import unidecode

# Access the output of the "homzmart_cat_page_spider" script stored in the JSON file 'Output_Cat_Page.json'
with open('Output_Cat_Page.json', 'r') as file:
    data = json.load(file)

urls_from_cat_page = [d['sub_cat_url'] for d in data] # No need to define first_url in the spider class below anymore as we are reading the output of the previous script
urls_from_cat_page = urls_from_cat_page[-3:-2:1] # For TESTING purposes (Strength & Weight Equipment sub-category ONLY - 4 page with 65 products)

class SubCatPageSpider(scrapy.Spider): # Extract the individual product page links from the sub-category pages
    name = 'sub_cat_page_spider'
    allowed_domains = ['homzmart.com']
    custom_settings = {"FEEDS":{"Output_SubCat_Page.json":{"format":"json", "overwrite": True}}}

    def start_requests(self):
        for url in urls_from_cat_page:
            yield scrapy.Request(url, callback = self.parse, dont_filter = True, meta = dict(
                playwright = True,
                playwright_include_page = True,
                playwright_page_methods = [PageMethod('wait_for_selector', 'div.card-body')],
                playwright_context_kwargs = dict(
                    proxy = {
                        "server": "proxy.zyte.com:8011",
                        "username": "3c9fb0a16f1e4af084e65c6b2037ea3e",
                        "password": "12345",
                    },
                )
            ))

    async def parse(self, response):
        last_page = response.xpath('//ul[contains(@class, "v-pagination")]/li[last() - 1]/button/text()').get()
        current_page = response.xpath('//*[contains(@aria-label, "Current Page")]/text()').get()

        if last_page is not None and current_page is not None:
            if int(current_page) == 1:
                for i in range(2, int(last_page)+1): 
                    yield scrapy.Request(response.url.replace('#1','#{}').format(i), callback = self.parse, dont_filter = True, meta = dict(
                        playwright = True,
                        playwright_include_page = True,
                        playwright_page_methods = [PageMethod('wait_for_selector', 'div.card-body')],
                        playwright_context_kwargs = dict(
                            proxy = {
                                "server": "proxy.zyte.com:8011",
                                "username": "3c9fb0a16f1e4af084e65c6b2037ea3e",
                                "password": "12345",
                            },
                        )
                    ))

        for prod in response.css('div.card-body'):
            l = ItemLoader(item = SubCatPageItem(), selector = prod)
            l.add_css('prod_name', 'a h3')
            l.add_xpath('last_pg', '//ul[contains(@class, "v-pagination")]/li[last() - 1]/button')
            l.add_xpath('prod_pg_rank', '//*[contains(@aria-label, "Current Page")]')
            l.add_css('prod_url', 'a::attr(href)')
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
    "ZYTE_SMARTPROXY_ENABLED": True,
    "ZYTE_SMARTPROXY_APIKEY": '3c9fb0a16f1e4af084e65c6b2037ea3e',
    "AUTOTHROTTLE_ENABLED": False,
    "DOWNLOAD_TIMEOUT": 600,
    "DOWNLOADER_MIDDLEWARES": {
        'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
        'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,
        # 'scrapy_proxy_pool.middlewares.ProxyPoolMiddleware': 610, # Free proxy pool
        # 'scrapy_proxy_pool.middlewares.BanDetectionMiddleware': 620, # Free proxy pool
        'scrapy_zyte_smartproxy.ZyteSmartProxyMiddleware': 610
    },
    # "PROXY_POOL_ENABLED": True, # Free proxy pool
    "CONCURRENT_REQUESTS_PER_IP": 32,
    "CONCURRENT_REQUESTS": 32,
    "COOKIES_ENABLED": False,
    "DOWNLOAD_DELAY": 3,
    "ROBOTSTXT_OBEY": False, # Saves one API call

    "PLAYWRIGHT_LAUNCH_OPTIONS": {
        "proxy": {
            "server": "proxy.zyte.com:8011",
            "username": "3c9fb0a16f1e4af084e65c6b2037ea3e",
            "password": "12345",
        },
    }
    
    # # Autothrottling and being polite to the server
    # "AUTOTHROTTLE_ENABLED": True,
    # # The initial download delay
    # "AUTOTHROTTLE_START_DELAY": 5,
    # # The maximum download delay to be set in case of high latencies
    # "AUTOTHROTTLE_MAX_DELAY": 60,
    # # The average number of requests Scrapy should be sending in parallel to each remote server
    # "AUTOTHROTTLE_TARGET_CONCURRENCY": 1,
    # # Enable showing throttling stats for every response received:
    # "AUTOTHROTTLE_DEBUG": True
})
process.crawl(SubCatPageSpider)
process.start()