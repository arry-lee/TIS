from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from multispider.items import ArticleItem


class SinhalaSpider(CrawlSpider):
    """斯里兰卡/僧伽罗新闻语料及图片爬虫"""

    name = "sinhala"
    allowed_domains = ["dinamina.lk"]
    # https://www.gossiplankanews.com/ 图床连不上
    # http://epaper.dinamina.lk/ 电子报纸

    start_urls = ["http://www.dinamina.lk/"]
    custom_settings = dict(
        CLOSESPIDER_ITEMCOUNT=10,
        # LOG_LEVEL='INFO',
        IMAGES_STORE=r"E:\00IT\P\uniform\multispider\images\sinhala",
        CLOSESPIDER_PAGECOUNT=20,
    )
    # https://www.bernama.com/bm/news.php?id=2113636
    rules = (
        Rule(
            LinkExtractor(allow=r"\d{4}/\d{2}/\d{2}/.+"),
            callback="parse_item",
            follow=True,
        ),
    )

    def parse_item(self, response):
        item = ArticleItem()
        item["content"] = "\n".join(
            response.xpath(
                '//article//div[@class="field-items"]//p/text()'
                # '//article//div[@style]/text()'
            ).getall()
        )
        if not item["content"]:
            item["content"] = "\n".join(
                response.xpath("//article//div[@style]/text()").getall()
            )
        item["image_urls"] = response.xpath("//article//img/@src").getall()
        yield item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl sinhala -o sinhala.json".split())
