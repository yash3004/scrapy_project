import time
from typing import Iterable, Any

import scrapy
from scrapy.http import Response
from typing import List


class StoneSpider(scrapy.Spider):
    name = "stone"
    start_urls = [
        "https://royalestones.co.uk/categories/garden-paving.html",
        "https://royalestones.co.uk/categories/floor-tiles.html",
        "https://royalestones.co.uk/categories/wall-tiles.html",
        "https://royalestones.co.uk/categories/bathroom-tiles-1.html",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for no, items in enumerate(response.css("div#products")):

            title = items.xpath(".//div/p[1]/text()").getall()
            image = items.xpath(".//figure/a/img/@data-src").getall()
            on_mouse_image: List[str] = items.xpath(".//figure/a/img/@onmouseover")
            price = items.xpath(".//div/p[2]/span[1]/text()").getall()
            discount_price = items.xpath(".//div/p[2]/span/text()").getall()

            for no, items in enumerate(image):
                yield {
                    "title": title[no].strip("-")[0],
                    "size": title[no].strip("-")[1],
                    "image": f"https://royalestones.co.uk/{image[no]}",
                    "price": price[no],
                    "discount_price": discount_price[no],
                }
        next_page = response.css("li.page-item a::attr(href)").getall()
        print(next_page[-1])
        if next_page is not None:
            time.sleep(2)
            yield response.follow(next_page[-1], callback=self.parse)
