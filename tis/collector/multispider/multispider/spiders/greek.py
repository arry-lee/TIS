from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from multispider.items import ArticleItem


class GreekSpider(CrawlSpider):
    """希腊新闻文本图像爬虫"""

    name = "greek"
    allowed_domains = ["news247.gr"]
    start_urls = ["https://www.news247.gr/"]
    custom_settings = dict(
        CLOSESPIDER_ITEMCOUNT=10,
        # LOG_LEVEL="INFO",
        IMAGES_STORE=r"E:\00IT\P\uniform\multispider\images\greek",
        CLOSESPIDER_PAGECOUNT=20,
    )
    rules = (
        Rule(LinkExtractor(allow=r"\w+/.+html"), callback="parse_item", follow=True),
    )

    def parse_item(self, response):
        item = ArticleItem()
        item["content"] = " ".join(
            response.xpath('//div[@class="article-body "]//p//text()').getall()
        )
        item["image_urls"] = response.xpath(
            '//figure[@class="article-body__picture"]/img/@src'
        ).getall()
        yield item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl greek -o greek.json".split())
