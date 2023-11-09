from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from multispider.items import ArticleItem


class NepaliSpider(CrawlSpider):
    """尼泊尔新闻语料及图片爬虫"""

    name = "nepali"
    allowed_domains = ["setopati.com"]
    start_urls = ["https://www.setopati.com/"]
    custom_settings = dict(
        CLOSESPIDER_ITEMCOUNT=10,
        # LOG_LEVEL='INFO',
        IMAGES_STORE=r"E:\00IT\P\uniform\multispider\images\nepali",
        CLOSESPIDER_PAGECOUNT=20,
    )
    # https://www.bernama.com/bm/news.php?id=2113636
    rules = (Rule(LinkExtractor(allow=r"\w+/\d+"), callback="parse_item", follow=True),)

    def parse_item(self, response):
        item = ArticleItem()
        item["content"] = "\n".join(
            response.xpath('//div[@class="editor-box"]//p/text()').getall()
        )

        item["image_urls"] = response.xpath(
            '//div[@id="featured-images"]/figure/img/@src'
        ).getall()
        yield item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl nepali -o nepali.json".split())
