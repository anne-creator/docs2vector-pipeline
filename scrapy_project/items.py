"""Scrapy item definitions."""

import scrapy


class AmazonSellerItem(scrapy.Item):
    """Item for scraped Amazon Seller help pages."""

    url = scrapy.Field()
    title = scrapy.Field()
    html_content = scrapy.Field()
    text_content = scrapy.Field()
    last_updated = scrapy.Field()
    breadcrumbs = scrapy.Field()
    related_links = scrapy.Field()
    things_to_know = scrapy.Field()
    things_to_do = scrapy.Field()
    things_to_avoid = scrapy.Field()
    metadata = scrapy.Field()
    scraped_at = scrapy.Field()

