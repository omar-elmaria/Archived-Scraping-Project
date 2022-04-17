from gc import callbacks
from ssl import VERIFY_DEFAULT
from sys import dont_write_bytecode
import sys
sys.path.append('/home/oelmaria/python_projects/homzmart_project/homzmart_scraping') # OR Insert this in the terminal --> export PYTHONPATH="${PYTHONPATH}:/home/oelmaria/homzmart_scraping/homzmart_scraping"
import os
from dotenv import load_dotenv
import scrapy
from scrapy_playwright.page import PageCoroutine, PageMethod
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from homzmart_scraping.items import SubCatPageItem
from scrapy.loader import ItemLoader
import json
from unidecode import unidecode
import logging
from playwright.async_api import Response, Request
from scraper_api import ScraperAPIClient

# Access the output of the "homzmart_cat_page_spider" script stored in the JSON file 'Output_Cat_Page.json'
with open('Output_Cat_Page.json', 'r') as file:
    data = json.load(file)

urls_from_cat_page = [d['sub_cat_url'] for d in data] # No need to define first_url in the spider class below anymore as we are reading the output of the previous script
urls_from_cat_page = urls_from_cat_page[-3:-2:1] # For TESTING purposes (Strength & Weight Equipment sub-category ONLY - 4 page with 65 products)

# Load environment variables
load_dotenv()
# Scrapper API for rotating through proxies
client = ScraperAPIClient(os.environ['SCRAPER_API_KEY'])

class SubCatPageSpider(scrapy.Spider): # Extract the individual product page links from the sub-category pages
    name = 'sub_cat_page_spider'
    allowed_domains = ['homzmart.com']
    custom_settings = {"FEEDS":{"Output_SubCat_Page.json":{"format":"json", "overwrite": True}}}

    def start_requests(self):
        for url in urls_from_cat_page:
            yield scrapy.Request(client.scrapyGet(url = url, render=True, country_code='de'), callback = self.parse, dont_filter = True, meta = dict(master_url = url))

    async def parse(self, response):
        last_page = response.xpath('//ul[contains(@class, "v-pagination")]/li[last() - 1]/button/text()').get()
        current_page = response.xpath('//*[contains(@aria-label, "Current Page")]/text()').get()
        
        if last_page is not None and current_page is not None:
            if int(current_page) == 1:
                for i in range(2, int(last_page)+1): 
                    yield scrapy.Request(client.scrapyGet(url = response.meta['master_url'].replace('#1', '#{}').format(i), render=True, country_code='de'), callback = self.parse, dont_filter = True)

        for prod in response.css('div.card-body'):
            l = ItemLoader(item = SubCatPageItem(), selector = prod)
            l.add_css('prod_name', 'a h3')
            l.add_xpath('last_pg', '//ul[contains(@class, "v-pagination")]/li[last() - 1]/button')
            l.add_xpath('prod_pg_rank', '//*[contains(@aria-label, "Current Page")]')
            l.add_css('prod_url', 'a::attr(href)')
            l.add_value('response_url', response.headers['Sa-Final-Url'])
            
            yield l.load_item()

#Run the spider
process = CrawlerProcess(settings = {
    # Adjusting the scraping behavior to rotate appropriately through proxies and user agents
    "AUTOTHROTTLE_ENABLED": False,
    "CONCURRENT_REQUESTS_PER_IP": 4, # The maximum number of concurrent (i.e. simultaneous) requests that will be performed to any single IP
    "CONCURRENT_REQUESTS": 4, # The maximum number of concurrent (i.e. simultaneous) requests that will be performed by the Scrapy downloader
    "DOWNLOAD_TIMEOUT": 60, # Setting the timeout parameter to 60 seconds as per the ScraperAPI documentation
    "ROBOTSTXT_OBEY": False, # Saves one API call
})
process.crawl(SubCatPageSpider)
process.start()