from gc import callbacks
from sys import dont_write_bytecode
import sys
sys.path.append('/home/oelmaria/python_projects/homzmart_project/homzmart_scraping') # OR Insert this in the terminal --> export PYTHONPATH="${PYTHONPATH}:/home/oelmaria/homzmart_scraping/homzmart_scraping"
import scrapy
from scrapy_playwright.page import PageCoroutine, PageMethod
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from homzmart_scraping.items import ProdPageItem
from scrapy.loader import ItemLoader
import numpy as np
import json

# Access the output of the "homzmart_subcat_page_spider" script stored in the JSON file 'Output_SubCat_Page.json'
with open('Output_SubCat_Page.json', 'r') as file:
    data = json.load(file)

urls_from_subcat_page = [d['prod_url'] for d in data] # No need to define first_url in the spider class below anymore as we are reading the output of the previous script

# The same product may appear on multiple page loads due to Homzmart's website sorting algorithm
# Delete all the duplicate URLs that get generated due to the random product sorting followed by Homzmart's website
urls_from_subcat_page = np.unique(urls_from_subcat_page)[0:20] # 0:20 FOR TESTING purposes
# print(len(urls_from_subcat_page)) # For TESTING purposes

class ProdPageSpider(scrapy.Spider):
    name = 'prod_page_spider'
    allowed_domains = ['homzmart.com']
    custom_settings = {"FEEDS":{"Output_Prod_Page.json":{"format":"json", "overwrite": True}}}
    
    def start_requests(self):
        for url in urls_from_subcat_page:
            yield scrapy.Request(url, callback = self.parse, dont_filter = True, meta = dict(
                playwright = True,
                playwright_include_page = True,
                playwright_page_methods = [PageMethod('wait_for_selector', 'div.product-details')]
            ))
    
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
            l.add_value('response_url', response.url)
            yield l.load_item()


#Run the spiders
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
process.crawl(ProdPageSpider)
process.start()