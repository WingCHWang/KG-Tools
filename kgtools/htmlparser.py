#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from typing import List
import re
from bs4 import BeautifulSoup

from kgtools.annotation import Parallel, TimeLog
from kgtools.symbol import HTML


class HTMLParser:
    __name__ = "HTMLParser"

    class Node:
        def __init__(self, key, value):
            assert key in {"name", "class_", "id"}, "The parameter 'key' must be in {'name', 'class_', 'id'}"
            self.key = key
            self.value = value

    def __init__(self, entry_nodes: List[Node]=None, filter_nodes: List[Node]=None):
        self.entry_nodes = entry_nodes if entry_nodes is not None else []
        self.filter_nodes = filter_nodes if filter_nodes is not None else []

    def parse(self, html):
        body = BeautifulSoup(html, "lxml").body

        # remove useless elements
        scripts = body.findAll("script")
        [script.extract() for script in scripts]
        noscripts = body.findAll("noscript")
        [noscript.extract() for noscript in noscripts]
        navs = body.findAll(class_=re.compile(r'.*(nav|Nav|footer|Footer).*'))
        [nav.extract() for nav in navs]
        footers = body.findAll("footer")
        [footer.extract() for footer in footers]

        for node in self.filter_nodes:
            filtered = body.findAll(**{node.key: node.value})
            [n.extract() for n in filtered]

        entries = []
        for node in self.entry_nodes:
            entries.extend(body.findAll(**{node.key: node.value}))
        if len(entries) == 0:
            entries = [body]

        texts = set()
        for entry in entries:
            for li in entry.findAll("li"):
                string = li.get_text().strip()
                if len(string) > 0 and string[-1] not in set(".?!:;,"):
                    string = string + "."
                li.clear()
                li.append(string)
            for h in entry.findAll(re.compile(r'h[1-6]')):
                string = h.get_text().strip()
                if len(string) > 0 and string[-1] not in set(".?!:;,"):
                    string = string + "."
                h.clear()
                h.append(string)
            for p in entry.findAll("p"):
                string = p.get_text().strip()
                if len(string) > 0 and string[-1] not in set(".?!:;,"):
                    string = string + "."
                p.clear()
                p.append(string)

            for table in entry.findAll("table"):
                table.clear()
                table.append(f"{HTML.TAB}")
            for img in entry.findAll("img"):
                if not img.get("alt") or len(img["alt"]) == 0:
                    img_alt = f"{HTML.IMG}"
                else:
                    img_alt = img["alt"]
                img.insert_after(img_alt)
            for code in entry.findAll("code"):
                string = code.get_text().strip()
                if len(string.split()) > 5 or len(string) > 50:
                    string = f"{HTML.CODE}"
                code.clear()
                code.append(string)

            for pre in entry.findAll("pre"):
                pre.clear()
                pre.append(f"{HTML.PRE}.")
            for pre in entry.findAll("blockquote"):
                pre.clear()
                pre.append(f"{HTML.QUOTE}.")
            text = entry.get_text()
            text = text.strip() + " "
            text = re.sub(r'(https?://.*?)([^a-zA-Z0-9/]?\s)', r"%s\2" % HTML.TAB, text)
            text = re.sub(r'\s+', ' ', text).strip()
            if len(text) > 0:
                if text[-1] not in set(".?!:;,"):
                    text = text + "."
                texts.add(text)
        return texts

    @TimeLog
    @Parallel()
    def process(self, html_list):
        docs = set()
        for html in html_list:
            texts = self.parse(html)
            docs.update(texts)
        return docs


class JavadocParser(HTMLParser):
    __name__ = "JavadocParser"

    def __init__(self, **cfg):
        super(self.__class__, self).__init__(**cfg)

    def parse(self, html):
        body = BeautifulSoup(html, "lxml").body
        strings = []
        for div in body.select(".block"):
            string = div.get_text().strip()
            string = re.sub(r'\s+', ' ', string)
            if len(string) > 0 and string[-1] not in set(".?!"):
                string = string + "."
            strings.append(string)
        return strings


if __name__ == "__main__":
    html_parser = HTMLParser()
