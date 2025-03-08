# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import logging
import random

import requests
from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware


class StoneSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class StoneDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


import requests
import logging


class ProxyMiddleware:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing ProxyMiddleware")

        # Fetch proxy list
        url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                self.proxies = response.text.strip().split("\n")
                # Remove empty strings that might be in the list
                self.proxies = [p for p in self.proxies if p.strip()]
                self.logger.info(f"Loaded {len(self.proxies)} proxies")
            else:
                self.logger.error(f"Failed to fetch proxies: {response.status_code}")
                self.proxies = []
        except Exception as e:
            self.logger.error(f"Error fetching proxies: {e}")
            self.proxies = []

        self.current_proxy = 0
        self.bad_proxies = set()
        self.current_working_proxy = None

    def get_next_proxy(self):
        """Get the next proxy that hasn't been marked as bad"""
        if not self.proxies:
            return None

        attempts = 0
        max_attempts = len(self.proxies)

        while attempts < max_attempts:
            proxy = self.proxies[self.current_proxy]
            self.current_proxy = (self.current_proxy + 1) % len(self.proxies)

            # Skip known bad proxies
            if proxy in self.bad_proxies:
                attempts += 1
                continue

            # Ensure proxy has proper format (but don't modify the URL)
            if not proxy.startswith(("http://", "https://")):
                proxy = "http://" + proxy

            return proxy

        return None  # No good proxies left

    def process_request(self, request, spider):
        # IMPORTANT: Don't modify the original URL
        original_url = request.url

        # If we have a working proxy, continue using it
        if (
            self.current_working_proxy
            and self.current_working_proxy not in self.bad_proxies
        ):
            request.meta["proxy"] = self.current_working_proxy
            # Make sure the URL is unchanged
            request._set_url(original_url)
            return

        # Otherwise, get a new proxy
        proxy = self.get_next_proxy()
        if proxy:
            request.meta["proxy"] = proxy
            # Make sure the URL is unchanged
            request._set_url(original_url)
            self.logger.debug(f"Trying new proxy: {proxy} for {original_url}")

    def process_response(self, request, response, spider):
        """Track successful proxy uses"""
        if response.status < 400:  # 2xx and 3xx are generally successful
            # Remember this proxy as working
            proxy = request.meta.get("proxy")
            if proxy:
                self.current_working_proxy = proxy

        elif response.status >= 400:
            # If we get an error response, mark the proxy as bad
            proxy = request.meta.get("proxy")
            if proxy:
                self.logger.warning(f"Proxy error: {proxy} - HTTP {response.status}")
                self.bad_proxies.add(proxy)
                self.current_working_proxy = None

                # Retry with a new proxy, but keep the original URL
                retryreq = request.copy()
                retryreq.dont_filter = True
                return retryreq

        return response

    def process_exception(self, request, exception, spider):
        """Handle connection errors with proxies"""
        # Mark proxy as bad if it fails
        proxy = request.meta.get("proxy")
        if proxy:
            self.logger.warning(f"Proxy error: {proxy} - {exception}")
            self.bad_proxies.add(proxy)
            self.current_working_proxy = None

            # Retry with a new proxy, but keep the original URL
            retryreq = request.copy()
            retryreq.dont_filter = True
            return retryreq

        return None


class RandomUserAgentMiddleware(UserAgentMiddleware):
    def __init__(self, user_agent_list):
        self.user_agent_list = user_agent_list
        super().__init__()

    @classmethod
    def from_crawler(cls, crawler):
        # Load list of user agents from settings
        user_agent_list = crawler.settings.get("USER_AGENT_LIST", [])
        middleware = cls(user_agent_list)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware

    def spider_opened(self, spider):
        self.user_agent = getattr(
            spider, "user_agent", random.choice(self.user_agent_list)
        )

    def process_request(self, request, spider):
        request.headers["User-Agent"] = random.choice(self.user_agent_list)
