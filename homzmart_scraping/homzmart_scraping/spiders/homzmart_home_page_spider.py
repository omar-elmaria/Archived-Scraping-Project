from gc import callbacks
from sys import dont_write_bytecode
import sys
sys.path.append('/home/oelmaria/python_projects/homzmart_project/homzmart_scraping') # OR Insert this in the terminal --> export PYTHONPATH="${PYTHONPATH}:/home/oelmaria/homzmart_scraping/homzmart_scraping"
import scrapy
from scrapy_playwright.page import PageCoroutine, PageMethod
from scrapy.crawler import CrawlerProcess
from scrapy.signalmanager import dispatcher
from scrapy.utils.project import get_project_settings
from homzmart_scraping.items import HomePageItem
from scrapy.loader import ItemLoader

class HomePageSpider(scrapy.Spider): # Extract the names and URLs of the categories from the homepage
    name = 'home_page_spider'
    allowed_domains = ['homzmart.com']
    first_url = 'https://homzmart.com/en'
    custom_settings = {"FEEDS":{"Output_Home_Page.json":{"format":"json", "overwrite": True}}}

    def start_requests(self):
        yield scrapy.Request(HomePageSpider.first_url, callback = self.parse, meta = dict(
            playwright = True,
            playwright_include_page = True,
            playwright_page_methods = [PageMethod('wait_for_selector', 'div.site-menu__item')] # Category info from home page
        ))

    async def parse(self, response):
        for cat in response.css('div.site-menu__item'):
            l = ItemLoader(item = HomePageItem(), selector = cat)
            l.add_css('cat_name', 'a')
            l.add_css('cat_url', 'a::attr(href)')
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
process.crawl(HomePageSpider)
process.start()