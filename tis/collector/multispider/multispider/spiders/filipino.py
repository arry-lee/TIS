from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from multispider.items import ArticleItem


class FilipinoSpider(CrawlSpider):
    """菲律宾新闻文本图像爬虫"""

    name = "filipino"
    allowed_domains = ["gmanetwork.com"]
    start_urls = ["https://www.gmanetwork.com/news/"]
    custom_settings = dict(
        CLOSESPIDER_ITEMCOUNT=10,
        # LOG_LEVEL="INFO",
        IMAGES_STORE=r"E:\00IT\P\uniform\multispider\images\filipino",
        CLOSESPIDER_PAGECOUNT=20,
    )
    rules = (
        Rule(
            LinkExtractor(allow=r"news/balitambayan/"),
            callback="parse_item",
            follow=True,
        ),
    )

    def parse_item(self, response):
        item = ArticleItem()
        item["content"] = " ".join(
            response.xpath('//article/div[@class="article-body"]//p//text()').getall()
        )
        item["image_urls"] = response.xpath("//article//img/@src").getall()
        yield item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl filipino -o filipino.json".split())
