from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from multispider.items import ArticleItem


class KhmerSpider(CrawlSpider):
    """柬埔寨新闻文本图像爬虫"""

    name = "khmer"
    allowed_domains = ["news.sabay.com.kh"]
    start_urls = ["https://news.sabay.com.kh/"]
    custom_settings = dict(
        CLOSESPIDER_ITEMCOUNT=10,
        LOG_LEVEL="INFO",
        IMAGES_STORE=r"E:\00IT\P\uniform\multispider\images\khmer",
        CLOSESPIDER_PAGECOUNT=20,
    )
    rules = (
        Rule(LinkExtractor(allow=r"article/\d+"), callback="parse_item", follow=True),
    )

    def parse_item(self, response):
        item = ArticleItem()
        item["content"] = " ".join(
            response.xpath('//*[@id="post_content"]/div[2]/p/text()').getall()
        )
        item["image_urls"] = []
        for url in response.xpath(
            '//*[@class="content-grp-img"]/picture/source[1]/@srcset'
        ):
            item["image_urls"].append(url.get())
        yield item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl khmer -o khmer.json".split())
