import time
from typing import Iterable, Any

import scrapy
from scrapy.http import Response
from typing import List


class StoneSpider(scrapy.Spider):
    name = "royal_stone"
    start_urls = [
        "https://royalestones.co.uk/categories/garden-paving.html",
        "https://royalestones.co.uk/categories/floor-tiles.html",
        "https://royalestones.co.uk/categories/wall-tiles.html",
        "https://royalestones.co.uk/categories/bathroom-tiles-1.html",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for i in response.css("div#products"):

            title = i.xpath(".//div/p[1]/text()").getall()
            image = i.xpath(".//figure/a/img/@data-src").getall()
            on_mouse_image: List[str] = i.xpath(".//figure/a/img/@onmouseover")
            price = i.xpath(".//div/p[2]/span[1]/text()").getall()
            discount_price = i.xpath(".//div/p[2]/span/text()").getall()

            for no, items in enumerate(image):
                yield {
                    "title": title[no],
                    "image": f"https://royalestones.co.uk/{image[no]}",
                    "price": price[no],
                    "discount_price": discount_price[no],
                }
        next_page = response.css("li.page-item a::attr(href)").getall()
        if next_page is not None:
            time.sleep(2)
            yield response.follow(next_page[-1], callback=self.parse)


class StoneScraper2(scrapy.Spider):
    name = "stonemart"
    start_urls = [
        "https://www.thestonemart.co.uk/collections/indian-sandstone-paving",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for items in response.css("div.collection"):
            image = items.xpath(".//li/div/div/div/div/a/img/@src")
            title = items.xpath(".//li/div/div/div/div[1]/a/@data-product-title")
            price = items.xpath(".//li/div/div/div/div[1]/div/div/span[" "1]/text()")
            discount_price = items.xpath(
                ".//li/div/div/div/div[" "1]/div/div/span[2]/text()"
            )
            for no, i in image:
                yield {
                    "title": title[no],
                    "image": f"https:{image[no]}",
                    "price": price[no],
                    "discount_price": discount_price[no],
                }
