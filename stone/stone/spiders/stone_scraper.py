import re
import time
from cgi import parse
from typing import Iterable, Any
from urllib.request import Request

import requests
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
        "https://royalestones.co.uk/categories/bathroom-furiture.html",
        "https://royalestones.co.uk/categories/acoustic-slat-wood-panels.html",
        "https://royalestones.co.uk/categories/paving-essentials.html",
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
        "https://www.thestonemart.co.uk/collections/limestone-paving",
        "https://www.thestonemart.co.uk/collections/granite-paving",
        "https://www.thestonemart.co.uk/collections/porcelain-paving",
        "https://www.thestonemart.co.uk/collections/slate-paving",
        "https://www.thestonemart.co.uk/collections/driveway-paving",
        "https://www.thestonemart.co.uk/collections/paving-accessories",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        total_items = response.xpath(
            "/html/body/div[1]/main/div/div[3]/div/div[1]/div/div["
            "2]/div/div/nav/div[1]/span[5]/text()"
        ).get()
        if total_items is None:
            self.parse_next(response)
        else:
            total_no = re.findall(r"\d+", total_items)[0]
            total_no = int(total_no)
            print(total_no)
            for i in range(1, (total_no // 18) + 2):
                next_page = f"{response.url}?page={i}"
                yield response.follow(next_page, callback=self.parse_next)
                print(next_page)

    def parse_next(self, response: Response) -> Any:
        products = response.css("div.collection")
        print(products)
        for items in products:
            image = items.xpath(".//li/div/div/div/div/a/img[1]/@src").getall()
            title = items.xpath(
                ".//li/div/div/div/div[1]/a/@data-product-title"
            ).getall()
            price = items.xpath(
                ".//li/div/div/div/div[1]/div/div/div/span[1]/text()"
            ).getall()
            discount_price = items.xpath(
                ".//li/div/div/div/div[1]/div/div/div/span[2]/text()"
            ).getall()
            for no, items in enumerate(title):
                yield {
                    "title": title[no],
                    "image": f"https://royalestones.co.uk/{image[no]}",
                    "price": price[no],
                    "discount_price": discount_price[no],
                }
