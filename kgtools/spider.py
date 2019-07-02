#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import async_timeout
import re
from bs4 import BeautifulSoup

from kgtools.func import reduce_seqs
from kgtools.saver import Saver, FileFormat
from kgtools.annotation import TimeLog


class Spider:

    def __init__(self, root, upper=None, lower=None, proxy_server=None, pool_size=63, retry=3):
        self.root = root
        simple_root = re.sub(r'(http://|https://)?(.*)', r'\2', root)
        self.domain = re.sub(r'(http://|https://)?(.*)', r'\1', root) + simple_root.split("/")[0]
        self.upper = upper if upper is not None else self.domain
        self.lower = lower if lower is not None else "<NO-LOWER>"

        self.storage = {}
        self.waiting_urls = set() if root is None else {root}
        self.fialed_urls = set()
        self.retry = retry

        self.proxy_server = proxy_server
        self.semaphore = asyncio.Semaphore(pool_size)

    def __is_in_scope(self, url):
        if url.startswith(self.upper) and not url.startswith(self.lower):
            return True
        else:
            return False

    def __normalize_url(self, cur_url, href):
        # cur_url = re.sub(r'(http://|https://)?(.*)', r'\2', cur_url)
        if len(href) == 0 or href.startswith("#") or href.startswith("?"):
            return cur_url
        if href.startswith("http://") or href.startswith("https://"):
            url = href
        elif href.startswith("/") and len(href) > 1:
            url = self.domain.rstrip("/") + "/" + href.lstrip("/")
        else:
            url = "/".join(cur_url.split("/")[:-1]).rstrip("/") + "/" + href.lstrip("/")
        url = re.sub(r'([^#\?]*)(#.*|\?.*)', r'\1', url)
        parts = []
        eles = url.split("/")
        for ele in eles:
            if ele == ".":
                continue
            if ele == "..":
                parts.pop()
                continue
            parts.append(ele)
        url = "/".join(parts)
        return url

    async def __request(self, url):
        try:
            async with self.semaphore:
                async with aiohttp.ClientSession() as session:
                    with async_timeout.timeout(10):
                        async with session.get(url, proxy=self.proxy_server) as response:
                            return await response.text()
        except Exception:
            print(f"[Failed] {url}")
            self.fialed_urls.add(url)
            return None

    async def fetch(self, url, recursive=True):
        links = set()
        if url in self.storage:
            return links
        html = await self.__request(url)
        if html is None:
            return links
        body = BeautifulSoup(html, "lxml").body
        if body is None:
            return links
        self.storage[url] = str(body)
        if recursive:
            for a in body.findAll("a"):
                link = a.get("href", "")
                if len(link) > 0:
                    link = self.__normalize_url(url, link)
                    if self.__is_in_scope(link):
                        links.add(link)
        print(f"[Done] {url}")
        return links

    @TimeLog
    def start_crawl(self, recursive_depth=None):
        current_depth = 1
        while (recursive_depth is None or current_depth <= recursive_depth) or len(self.waiting_urls) > 0:
            loop = asyncio.get_event_loop()
            tasks = [self.fetch(url, recursive=(current_depth != recursive_depth)) for url in self.waiting_urls]
            resutls = loop.run_until_complete(asyncio.gather(*tasks))
            self.waiting_urls = {url for url in reduce_seqs(resutls) if url not in self.storage and url not in self.fialed_urls}
            current_depth += 1
        for _ in range(self.retry):
            if len(self.fialed_urls) == 0:
                break
            loop = asyncio.get_event_loop()
            tasks = [self.fetch(url, recursive=False) for url in self.fialed_urls]
            self.fialed_urls = set()
            loop.run_until_complete(asyncio.gather(*tasks))

        if len(self.fialed_urls) > 0:
            print("#### Failed Urls ####")
            for url in self.fialed_urls:
                print(url)

    def load_storage(self, file_name, file_format=FileFormat.JSON):
        self.storage = Saver.load(file_name, file_format)

    def dump_storage(self, file_name, file_format=FileFormat.JSON):
        Saver.dump(self.storage, file_name, file_format)


if __name__ == '__main__':
    spider = Spider("https://docs.oracle.com/javase/8/docs/api/allclasses-noframe.html")
    spider.start_crawl()
    spider.dump_storage("data/jdk8/all-class.html.json")
