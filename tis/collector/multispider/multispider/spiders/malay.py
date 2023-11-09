from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from multispider.items import ArticleItem


class MalaySpider(CrawlSpider):
    """马来西亚新闻语料及图片爬虫"""

    name = "malay"
    allowed_domains = ["bernama.com"]
    start_urls = ["https://www.bernama.com/bm/"]
    custom_settings = dict(
        CLOSESPIDER_ITEMCOUNT=10,
        LOG_LEVEL="INFO",
        IMAGES_STORE=r"E:\00IT\P\uniform\multispider\images\malay",
        CLOSESPIDER_PAGECOUNT=20,
    )
    # https://www.bernama.com/bm/news.php?id=2113636
    rules = (
        Rule(LinkExtractor(allow=r"news.php"), callback="parse_item", follow=True),
    )

    def parse_item(self, response):
        item = ArticleItem()
        item["content"] = "\n".join(
            response.xpath(
                '//div[@id="topstory"]/../div[@class="row"]//p/text()'
            ).getall()
        )
        item["image_urls"] = response.xpath(
            '//div[@id="topstory"]//img/@data-src'
        ).getall()
        yield item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl malay -o malay.json".split())
