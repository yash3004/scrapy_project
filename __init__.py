import scrapy


class StoneSpider(scrapy.Spider):
    name = "stone"
    start_urls = [
       "https://royalestones.co.uk/categories/garden-paving.html",
    ]

    def parse(self, response):
        for item in response.css("div#product"):
            yield {
                "image": item.xpath(".//figure/a/img/@data-src").get(),
            }

        next_page = response.css('li.page-item a::attr("href")').get()
        if next_page is not None:
            yield response.follow(next_page, self.parse)