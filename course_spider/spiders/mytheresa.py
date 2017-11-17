# -*- coding: utf-8 -*-
import datetime
import json

import scrapy
from scrapy.loader import ItemLoader

from course_spider.items import Product



class Mytheresa(scrapy.Spider):
    name = 'mytheresa'
    retailer = 'MYTHERESA'
    site = 'www.mytheresa.com'

    start_url = {
        'https://www.mytheresa.com/en-us/': 'us',
        # 'https://www.mytheresa.com/en-gb/': 'uk',
        # 'https://www.mytheresa.com/en-fr/': 'fr',
        # 'https://www.mytheresa.com/en-de/': 'de',
        # 'https://www.mytheresa.com/en-au/': 'au',
        # 'https://www.mytheresa.com/en-jp/': 'jp',
        # 'https://www.mytheresa.com/en-hk/': 'hk',
        # 'https://www.mytheresa.com/en-cn/': 'cn',
        # 'https://www.mytheresa.com/en-kr/': 'kr',
        # 'https://www.mytheresa.com/eu_en/': 'ru'
    }

    category_urls = [
        'sale.html',
        'clothing/dresses.html',
        'shoes.html',
        'bags.html',
        'accessories.html',
    ]
    marketplace_code = {
        'united states': 'US',
        'united kingdom': 'GB',
        'france': 'FR',
        'germany': 'DE',
        'australia': 'AU',
        'japan': 'JP',
        'hong kong': 'HK',
        'china': 'CH',
        'republic of korea': 'KR',
        'russian federation': 'EU',
    }

    currencies = {
        'United States': 'USD',
        'United Kingdom': 'GBP',
        'France': 'EUR',
        'Germany': 'EUR',
        'Australia': 'AUD',
        'Japan': 'YPY',
        'Hong Kong': 'HKD',
        'China': 'EUR',
        'Republic of Korea': 'EUR',
        'Russian Federation': 'EUR',
    }

    url_part_by_country = {
        'united states': '/en-us/',
        'united kingdom': '/en-gb/',
        'france': '/en-fr/',
        'germany': '/en-de/',
        'australia': '/en-au/',
        'japan': '/en-jp/',
        'hong kong': '/en-hk/',
        'china': '/en-cn/',
        'republic of korea': '/en-kr/',
        'russian federation': '/eu_en/'
    }

    def start_requests(self):
        for url, code in self.start_url.items():
            yield scrapy.Request(url=url,
                                 callback=self.parse,
                                 meta={
                                     'code': code,
                                 })

    def parse(self, response):
        meta = {
            'code': response.meta.get('code'),
        }
        for url in self.category_urls:
            yield scrapy.Request(url=response.url + url, callback=self.parse_pages,
                                 meta=meta, dont_filter=True)

    def parse_pages(self, response):
        meta = {
            'code': response.meta.get('code'),
        }
        pages = response.xpath(
            '//div[@class="pages"]/ul/li[@class="last"]/a/@href').re_first(
            r'\?p=(\d+)')
        if 'clothing' in response.url:
            clothing_categories = response.xpath(
                '//div[@class="block-subnavigation"]/div[@class="block-content"]/ul/li/a/@href').extract()
            for category_url in clothing_categories:
                if 'fur' in category_url:
                    continue
                yield scrapy.Request(url=category_url, callback=self.parse_category_pages,
                                     meta=meta, dont_filter=True)
        else:
            if pages:
                for page in range(1, int(pages)):
                    url = response.url + '?p={}'.format(page)
                    yield scrapy.Request(url=url, callback=self.parse_items,
                                         meta=meta, dont_filter=True)
            else:
                yield scrapy.Request(url=response.url, callback=self.parse_items,
                                     meta=meta, dont_filter=True)

    def parse_category_pages(self, response):
        meta = {
            'code': response.meta.get('code'),
        }
        pages = response.xpath(
            '//div[@class="pages"]/ul/li[@class="last"]/a/@href').re_first(
            r'\?p=(\d+)')
        if pages:
            for page in range(1, int(pages)):
                url = response.url + '?p={}'.format(page)
                yield scrapy.Request(url=url, callback=self.parse_items,
                                     meta=meta,
                                     dont_filter=True
                                     )
        else:
            yield scrapy.Request(url=response.url, callback=self.parse_items,
                                 meta=meta,
                                 dont_filter=True
                                 )

    def parse_items(self, response):
        meta = {
            'code': response.meta.get('code'),
        }
        items = response.xpath('//div[@class="category-products"]/'
                               'ul[contains(@class, "products-grid")]/'
                               'li[contains(@class, "item")]/a/@href').extract()
        for item in items:
            yield scrapy.Request(url=item, callback=self.parse_detail,
                                 meta=meta, dont_filter=True)

    def parse_detail(self, response):
        site_product_id = self.parse_site_product_id(response)
        if not site_product_id:
            return
        name = self.parse_name(response)
        brand = self.parse_brand_name(response)
        categories = self.parse_categories(response)
        description = self.parse_description(response)

        material = self.parse_material(response)
        made_in = self.parse_made_in(response)
        image_urls = self.parse_images(response)
        market = self.parse_market(response)

        product_loader = ItemLoader(item=Product(), response=response)
        product_loader.add_value('market', market)
        product_loader.add_value('site_product_id', site_product_id)
        product_loader.add_value('site', self.site)
        product_loader.add_value('name', name)
        product_loader.add_value('brand', brand)
        product_loader.add_value('url', response.url)
        product_loader.add_value('categories', categories)
        product_loader.add_value('description', description)
        product_loader.add_value('material', material)
        product_loader.add_value('made_in', made_in)
        product_loader.add_value('image_urls', image_urls)
        product_loader.add_value('has_color_selection', False)

        yield product_loader.load_item()


    def parse_site_product_id(self, response):
        site_product_id = response.xpath(
            '//div[@class="product-sku"]/span/text()'
        ).re_first(r'item no\.(.*)')
        if site_product_id:
            return site_product_id.strip()

    def parse_name(self, response):
        name = response.xpath(
            '//div[@class="product-name"]/h1/text()').extract_first()

        return name

    def parse_brand_name(self, response):
        page_info = self.get_page_info(response)
        brand = page_info.get('page', {}).get('brand')
        if brand:
            return brand

    def get_page_info(self, response):
        info = response.xpath('//div[@class="off-canvas-main"]/div/'
                              'following-sibling::script/text()').re_first(r'({.*})')

        return json.loads(info)

    def parse_categories(self, response):
        categories = response.xpath(
            '//div[@class="breadcrumbs"]/ul/li[contains(@class, "category")]/a'
            '/span/text()').extract()
        brand_name = self.parse_brand_name(response)
        try:
            index = categories.index(brand_name)
            categories.pop(index)
        except:
            pass
        if categories:
            if "Designers" in categories:
                categories = []
                page_info = self.get_page_info(response)
                main_product_group = page_info.get('page', {}).get('mainProductGroup')
                category = page_info.get('page', {}).get('category')
                sub_category = page_info.get('page', {}).get('subCategory')
                if main_product_group:
                    categories.append(main_product_group)
                if category:
                    categories.append(category)
                if sub_category:
                    categories.append(sub_category)
            return categories
        else:
            return ''

    def parse_description(self, response):
        description = response.xpath(
            '//p[contains(@class, "product-description")]/text()').extract_first()

        return description

    def parse_material(self, response):
        material = response.xpath(
            '//ul[@class="disc featurepoints"]/li[contains(text(), "material")]/'
            'text()').re_first(r'material: (.*)')

        return material

    def parse_made_in(self, response):
        made_in = response.xpath(
            '//ul[@class="disc featurepoints"]/li[contains(text(), "Made")]/'
            'text()').re_first(r'Made in (.*)')
        if made_in:
            return made_in.strip()

    def parse_images(self, response):
        image_urls = response.xpath(
            '//img[contains(@id, "image") and contains(@class, "gallery-image")]'
            '/@src').extract()

        return ['http:' + i for i in image_urls]

    def parse_market(self, response):
        market = response.xpath('//span[contains(@id, "country")]/'
                                'text()').extract_first()

        if market.lower() == 'america':
            market = 'United States'
        elif market.lower() == 'europe far':
            market = 'Russian Federation'
        elif market.lower() == 'south korea':
            market = 'Republic of Korea'

        return market
