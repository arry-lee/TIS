from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from multispider.items import ArticleItem


class LaoSpider(CrawlSpider):
    """老挝新闻语料及图片爬虫"""

    name = "lao"
    allowed_domains = ["vientianetimeslao.la"]
    start_urls = ["https://www.vientianetimeslao.la/"]
    custom_settings = dict(
        CLOSESPIDER_ITEMCOUNT=10,
        LOG_LEVEL="INFO",
        IMAGES_STORE=r"E:\00IT\P\uniform\multispider\images\lao",
        CLOSESPIDER_PAGECOUNT=20,
    )
    rules = (
        Rule(LinkExtractor(allow=r"%.{20,100}/"), callback="parse_item", follow=True),
    )

    def parse_item(self, response):
        item = ArticleItem()
        item["content"] = " ".join(
            response.xpath('//*[@class="entry-content"]/p/text()').getall()
        )
        item["image_urls"] = response.xpath(
            '//div[@class="entry-thumbnail-area "]/img/@src'
        ).getall()
        yield item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl lao -o lao.json".split())
