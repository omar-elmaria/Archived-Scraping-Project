from gc import callbacks
from sys import dont_write_bytecode
import sys
sys.path.append('/home/oelmaria/python_projects/homzmart_project/homzmart_scraping') # OR Insert this in the terminal --> export PYTHONPATH="${PYTHONPATH}:/home/oelmaria/homzmart_scraping/homzmart_scraping"
import os
from dotenv import load_dotenv
import scrapy
from scrapy_playwright.page import PageCoroutine, PageMethod
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from homzmart_scraping.items import CatPageItem
from scrapy.loader import ItemLoader
import json
from scraper_api import ScraperAPIClient

# Load environment variables
load_dotenv()
# Scrapper API for rotating through proxies
client = ScraperAPIClient(os.environ['SCRAPER_API_KEY'])

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
            yield scrapy.Request(client.scrapyGet(url = url, render=True, country_code='de'), callback = self.parse)
    
    async def parse(self, response):
        for sub_cat in response.css('div[role=tabpanel]'):
            l = ItemLoader(item = CatPageItem(), selector = sub_cat)
            l.add_css('sub_cat_name', 'a div.header::text')
            l.add_css('sub_cat_url', 'a::attr(href)')
            l.add_value('response_url', response.headers['Sa-Final-Url']) # Use this instead of response.url if you are using a proxy rotation service such as ScraperAPI

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
process.crawl(CatPageSpider)
process.start()