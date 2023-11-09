from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from multispider.items import ArticleItem


class DutchSpider(CrawlSpider):
    """荷兰新闻文本图像爬虫"""

    name = "dutch"
    allowed_domains = ["nrc.nl"]
    start_urls = ["https://www.nrc.nl/"]
    custom_settings = dict(
        CLOSESPIDER_ITEMCOUNT=10,
        # LOG_LEVEL="INFO",
        IMAGES_STORE=r"E:\00IT\P\uniform\multispider\images\dutch",
        CLOSESPIDER_PAGECOUNT=20,
    )
    rules = (Rule(LinkExtractor(allow=r"nieuws/"), callback="parse_item", follow=True),)

    def parse_item(self, response):
        item = ArticleItem()
        item["content"] = " ".join(
            response.xpath(
                '//div[@class="content article__content"]//p//text()'
            ).getall()
        )
        item["image_urls"] = response.xpath("//picture//img/@src").getall()
        yield item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl dutch -o dutch.json".split())
