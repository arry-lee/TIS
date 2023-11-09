from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from multispider.items import ArticleItem


class BengaliSpider(CrawlSpider):
    """孟加拉新闻文本图像爬虫"""

    name = "bengali"
    allowed_domains = ["webbangladesh.com"]
    start_urls = ["https://www.webbangladesh.com/"]
    custom_settings = dict(
        CLOSESPIDER_ITEMCOUNT=10,
        # LOG_LEVEL="INFO",
        IMAGES_STORE=r"E:\00IT\P\uniform\multispider\images\bengali",
        CLOSESPIDER_PAGECOUNT=20,
    )
    rules = (
        Rule(LinkExtractor(allow=r"%.{20,100}/"), callback="parse_item", follow=True),
    )

    def parse_item(self, response):
        item = ArticleItem()
        item["content"] = " ".join(
            response.xpath('//div[@class="entry-content"]//p/text()').getall()
        )
        item["image_urls"] = response.xpath(
            '//div[@class="post-thumb"]/img/@src'
        ).getall()
        yield item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl bengali -o bengali.json".split())
