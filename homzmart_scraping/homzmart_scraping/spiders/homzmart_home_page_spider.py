from gc import callbacks
from sys import dont_write_bytecode
import sys
sys.path.append('/home/oelmaria/python_projects/homzmart_project/homzmart_scraping') # OR Insert this in the terminal --> export PYTHONPATH="${PYTHONPATH}:/home/oelmaria/homzmart_scraping/homzmart_scraping"
import os
from dotenv import load_dotenv
import scrapy
from scrapy_playwright.page import PageCoroutine, PageMethod
from scrapy.crawler import CrawlerProcess
from scrapy.signalmanager import dispatcher
from scrapy.utils.project import get_project_settings
from homzmart_scraping.items import HomePageItem
from scrapy.loader import ItemLoader
from scraper_api import ScraperAPIClient

# Load environment variables
load_dotenv()
# Scrapper API for rotating through proxies
client = ScraperAPIClient(os.environ['SCRAPER_API_KEY'])

class HomePageSpider(scrapy.Spider): # Extract the names and URLs of the categories from the homepage
    name = 'home_page_spider'
    allowed_domains = ['homzmart.com']
    first_url = 'https://homzmart.com/en'
    custom_settings = {"FEEDS":{"Output_Home_Page.json":{"format":"json", "overwrite": True}}}

    def start_requests(self):
        yield scrapy.Request(client.scrapyGet(url = HomePageSpider.first_url, render=True, country_code='de'), callback = self.parse)

    async def parse(self, response):
        for cat in response.css('div.site-menu__item'):
            l = ItemLoader(item = HomePageItem(), selector = cat)
            l.add_css('cat_name', 'a')
            l.add_css('cat_url', 'a::attr(href)')
            l.add_value('response_url', response.headers['Sa-Final-Url'])
            
            yield l.load_item()

#Run the spider
process = CrawlerProcess(settings = {
    # Adjusting the scraping behavior to rotate appropriately through proxies and user agents
    "AUTOTHROTTLE_ENABLED": False,
    "CONCURRENT_REQUESTS_PER_IP": 3, # The maximum number of concurrent (i.e. simultaneous) requests that will be performed to any single IP
    "CONCURRENT_REQUESTS": 3, # The maximum number of concurrent (i.e. simultaneous) requests that will be performed by the Scrapy downloader
    "DOWNLOAD_TIMEOUT": 60, # Setting the timeout parameter to 60 seconds as per the ScraperAPI documentation
    "ROBOTSTXT_OBEY": False, # Saves one API call
})
process.crawl(HomePageSpider)
process.start()