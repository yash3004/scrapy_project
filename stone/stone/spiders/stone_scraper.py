import re
import time
from typing import Any
from typing import List

import scrapy
from scrapy.http import Response


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


class StoneScrapper3(scrapy.Spider):
    name = "nustone"

    start_urls = ["https://nustone.co.uk/product-category/paving-slabs/"]

    def parse(self, response: Response, **kwargs: Any):
        products = response.css("li.product")
        for product in products:
            next_link = product.xpath("div[2]/a/@href").get()
            next_link = f"{next_link}/?attribute_pa_format=slab"
            try:
                yield response.follow(next_link, callback=self.parse_single_page)
            except ValueError as val_err:
                print(f"error occurred trying new layout {val_err}")
                yield response.follow(next_link, callback=self.parse_single_page2)

        next_page_link = response.css("a.next::attr(href)").get()
        if next_page_link is not None:
            yield response.follow(next_page_link, callback=self.parse)

    def parse_single_page(self, response: Response, **kwargs: Any):
        try:
            title = response.css("h1.product_title::text").get()
            price_per_meter = response.css("p.price-per-meter").get()
            variant = response.css("#pa_format option::text").getall()
            price = response.css("div.product_price bdi::text").get()
            image = response.css("div.images img::attr(src)").get()
            material_type = response.css("nav.woocommerce-breadcrumb a::text").getall()[
                1
            ]

            if not all([title, price, image, material_type]):
                raise ValueError("Missing the required fields")

        except Exception as err:
            self.logger.warning(
                f"First layout failed trying new layout " f"Error : {err}"
            )
            yield response.follow(response.url, callback=self.parse_single_page2)

        yield {
            "title": title,
            "image": image,
            "variant": variant,
            "price/m^2": price_per_meter,
            "price_per_slab": price,
            "material_type": material_type,
        }

    def parse_single_page2(self, response: Response, **kwargs: Any):

        pass


class StoneScrapper4(scrapy.Spider):
    name = "londenstone"

    start_urls = [
        "https://www.londonstone.co.uk/porcelain-paving/",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        products = response.css("div.product-listing-container")
        for product in products:
            single_page_link = product.css("div.ls-product-name a::attr(href)").get()

            yield response.follow(single_page_link, callback=self.parse_single_page)

    def parse_single_page(self, response: Response, **kwargs: Any):
        title = response.css("h1#productName::text").get()
        image = response.css("li.swiper-slide picture img::attr(src)").get()
        price = response.css("p#productFromPrice span::text").getall()
        actual_price, vat_inclusive_price = price[0], price[-1]
        type = response.css("div.ls-product-nameblock div::text").get()
        stock = response.css(
            "table.table-group-price tr.odd td " "span::text"
        ).getall()[0]

        yield {
            "title": title,
            "image": image,
            "actual_price": actual_price,
            "vat_inclusive_price": vat_inclusive_price,
            "type": type,
            "stock": stock,
        }

        pass


class StoneScrapper5(scrapy.Spider):
    name = "meltonstone"
    start_urls = ["https://meltonstone.co.uk/porcelain-paving.html"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        products = response.css("div.prod-page-trustbox")

        for product in products:
            single_page_link = product.css(
                "div.product-item-info a::attr(" "href)"
            ).get()
            yield response.follow(single_page_link, callback=self.parse_single_page)

    def parse_single_page(self, response: Response, **kwargs: Any):
        title = r
