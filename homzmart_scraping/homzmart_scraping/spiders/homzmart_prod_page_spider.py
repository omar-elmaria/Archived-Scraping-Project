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
from homzmart_scraping.items import ProdPageItem
from scrapy.loader import ItemLoader
import numpy as np
import json
from scraper_api import ScraperAPIClient

# Access the output of the "homzmart_subcat_page_spider" script stored in the JSON file 'Output_SubCat_Page.json'
with open('Output_SubCat_Page.json', 'r') as file:
    data = json.load(file)

urls_from_subcat_page = [d['prod_url'] for d in data] # No need to define first_url in the spider class below anymore as we are reading the output of the previous script

# The same product may appear on multiple page loads due to Homzmart's website sorting algorithm
# Delete all the duplicate URLs that get generated due to the random product sorting followed by Homzmart's website
urls_from_subcat_page = np.unique(urls_from_subcat_page) # You can use [0:20] and print(len(urls_from_subcat_page)) FOR TESTING purposes

# Load environment variables
load_dotenv()
# Scrapper API for rotating through proxies
client = ScraperAPIClient(os.environ['SCRAPER_API_KEY'])

class ProdPageSpider(scrapy.Spider):
    name = 'prod_page_spider'
    allowed_domains = ['homzmart.com']
    custom_settings = {"FEEDS":{"Output_Prod_Page.json":{"format":"json", "overwrite": True}}}
    
    def start_requests(self):
        for url in urls_from_subcat_page:
            yield scrapy.Request(client.scrapyGet(url = url, render=True, country_code='de'), callback = self.parse, dont_filter = True)
    
    async def parse(self, response):
        for info in response.css('div.product-details'):
            l = ItemLoader(item = ProdPageItem(), selector = info)
            # General page info
            if l.add_css('prod_disp_name', 'h3.name') is None: # Product display name
                l.add_value('prod_disp_name', 'NA')
            else:
                l.add_css('prod_disp_name', 'h3.name')

            # # Merchandising data
            if l.add_css('main_img_link', 'div.zoomer-cont img::attr(src)') is None:
                l.add_value('main_img_link', 'NA')
            else:
                l.add_css('main_img_link', 'div.zoomer-cont img::attr(src)') # Main image link

            if l.add_css('all_img_links', 'div.v-image__image.v-image__image--contain::attr(style)') is None:
                l.add_value('all_img_links', 'NA')
            else:
                l.add_css('all_img_links', 'div.v-image__image.v-image__image--contain::attr(style)') # All image links

            if l.add_css('img_num', 'div.v-image__image.v-image__image--contain::attr(style)') is None:
                l.add_value('img_num', 'NA')
            else:
                l.add_css('img_num', 'div.v-image__image.v-image__image--contain::attr(style)') # Number of images
            
            if l.add_xpath('prod_desc', '//*[contains(@class, "product-data")]//li/text() | //*[contains(@class, "product-data")]//p/text()') is None:
                l.add_value('prod_desc', 'NA')
            else:
                l.add_xpath('prod_desc', '//*[contains(@class, "product-data")]//li/text() | //*[contains(@class, "product-data")]//p/text()') # Product description
            
            # Price data
            if l.add_css('curr_price', 'div h3.price') is None:
                l.add_value('curr_price', 'NA')
            else:
                l.add_css('curr_price', 'div h3.price') # Current price

            if l.add_css('discount_tag', 'div h3.price span.sale') is None:
                if l.add_css('discount_tag', 'div h3.price span.Flashsale') is not None:
                    l.add_css('discount_tag', 'div h3.price span.Flashsale')
                else: 
                    l.add_value('discount_tag', 'NA')
            else:
                l.add_css('discount_tag', 'div h3.price span.sale') # Discount tag
            
            if l.add_css('original_price', 'div h3.price span.original-price') is None:
                l.add_value('original_price', 'NA')
            else:
                l.add_css('original_price', 'div h3.price span.original-price') # Original price
            
            # # Product Info List
            if l.add_css('vendor_name', 'div.flex ul li h3 a') is None:
                l.add_value('vendor_name', 'NA')
            else:
                l.add_css('vendor_name', 'div.flex ul li h3 a') # Vendor name
            
            if l.add_css('vendor_url_homzmart', 'div.flex ul li h3 a::attr(href)') is None:
                l.add_value('vendor_url_homzmart', 'NA')
            else:
                l.add_css('vendor_url_homzmart', 'div.flex ul li h3 a::attr(href)') # Vendor URL on Homzmart's website
            
            if l.add_xpath('promised_delivery', '//div/ul/li[h4[contains(text(), "Delivery")]]') is None:
                l.add_value('promised_delivery', 'NA')
            else: 
                l.add_xpath('promised_delivery', '//div/ul/li[h4[contains(text(), "Delivery")]]') # Promised delivery

            if l.add_xpath('avail_type', '//div/ul/li[h4[contains(text(), "Available")]]') is None:
                l.add_value('avail_type', 'NA')
            else:
                l.add_xpath('avail_type', '//div/ul/li[h4[contains(text(), "Available")]]') # Availability type
            
            if l.add_xpath('dims', '//div/ul/li[h4[contains(text(), "Dimension")]]') is None:
                l.add_value('dims', 'NA')
            else:
                l.add_xpath('dims', '//div/ul/li[h4[contains(text(), "Dimension")]]') # Dimensions
            
            if l.add_xpath('material', '//div/ul/li[h4[contains(text(), "Material")]]') is None:
                l.add_value('material', 'NA')
            else:
                l.add_xpath('material', '//div/ul/li[h4[contains(text(), "Material")]]') # Material
            
            if l.add_xpath('country_origin', '//div/ul/li[h4[contains(text(), "Made")]]') is None:
                l.add_value('country_origin', 'NA')
            else:
                l.add_xpath('country_origin', '//div/ul/li[h4[contains(text(), "Made")]]') # Country of origin
            
            if l.add_xpath('sku_name', '//div/ul/li[h4[contains(text(), "SKU")]]') is None:
                l.add_value('sku_name', 'NA')
            else:
                l.add_xpath('sku_name', '//div/ul/li[h4[contains(text(), "SKU")]]') # SKU name
            
            # Response URL
            l.add_value('response_url', response.headers['Sa-Final-Url'])
            yield l.load_item()


#Run the spiders
process = CrawlerProcess(settings = {
    # Adjusting the scraping behavior to rotate appropriately through proxies and user agents
    "AUTOTHROTTLE_ENABLED": False,
    "CONCURRENT_REQUESTS_PER_IP": 4, # The maximum number of concurrent (i.e. simultaneous) requests that will be performed to any single IP
    "CONCURRENT_REQUESTS": 4, # The maximum number of concurrent (i.e. simultaneous) requests that will be performed by the Scrapy downloader
    "DOWNLOAD_TIMEOUT": 60, # Setting the timeout parameter to 60 seconds as per the ScraperAPI documentation
    "ROBOTSTXT_OBEY": False, # Saves one API call
})
process.crawl(ProdPageSpider)
process.start()