from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from multispider.items import ArticleItem


class IndonesianSpider(CrawlSpider):
    """印尼新闻文本图像爬虫"""

    name = "indonesian"
    allowed_domains = ["suara.com"]
    start_urls = ["https://www.suara.com/"]
    custom_settings = dict(
        CLOSESPIDER_ITEMCOUNT=10,
        # LOG_LEVEL="INFO",
        IMAGES_STORE=r"E:\00IT\P\uniform\multispider\images\indonesian",
        CLOSESPIDER_PAGECOUNT=20,
    )
    rules = (
        Rule(
            LinkExtractor(allow=r"news/\d{4}/\d{2}/\d{2}/.+"),
            callback="parse_item",
            follow=True,
        ),
    )

    def parse_item(self, response):
        item = ArticleItem()
        item["content"] = " ".join(
            response.xpath('//article[@class="content-article"]//p//text()').getall()
        )
        item["image_urls"] = response.xpath(
            '//article[@class="content-article"]//figure/img/@src'
        ).getall()
        yield item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl indonesian -o indonesian.json".split())
