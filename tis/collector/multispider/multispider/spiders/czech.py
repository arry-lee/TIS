from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from multispider.items import ArticleItem


class CzechSpider(CrawlSpider):
    """捷克新闻文本图像爬虫"""

    name = "czech"
    allowed_domains = ["novinky.cz"]
    start_urls = ["https://www.novinky.cz/"]
    custom_settings = dict(
        CLOSESPIDER_ITEMCOUNT=10,
        # LOG_LEVEL="INFO",
        IMAGES_STORE=r"E:\00IT\P\uniform\multispider\images\czech",
        CLOSESPIDER_PAGECOUNT=20,
    )
    rules = (Rule(LinkExtractor(allow=r"clanek/"), callback="parse_item", follow=True),)

    def parse_item(self, response):
        item = ArticleItem()
        item["content"] = " ".join(
            response.xpath('//article[@role="article"]//p//text()').getall()
        )
        item["image_urls"] = [
            "https:" + url
            for url in response.xpath(
                '//figure[@data-dot="mol-figure"]//img/@src'
            ).getall()
        ]
        yield item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl czech -o czech.json".split())