# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class Product(scrapy.Item):
    site = scrapy.Field()
    market = scrapy.Field()
    site_product_id = scrapy.Field()
    designer_color_id = scrapy.Field()
    color = scrapy.Field()
    name = scrapy.Field()
    designer_product_id = scrapy.Field()
    designer_style_id = scrapy.Field()
    brand = scrapy.Field()
    url = scrapy.Field()
    categories = scrapy.Field()
    description = scrapy.Field()
    material = scrapy.Field()
    made_in = scrapy.Field()
    image_urls = scrapy.Field()
    has_color_selection = scrapy.Field()
