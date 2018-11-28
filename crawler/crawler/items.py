# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class CrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class MovieItem(scrapy.Item):
    name = scrapy.Field()
    star = scrapy.Field()
    releasetime = scrapy.Field()
    boxoffice_realtime = scrapy.Field()
    boxoffice_total = scrapy.Field()
    link = scrapy.Field()
    score = scrapy.Field()
