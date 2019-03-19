#!/usr/bin/env python
# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import re
from bs4 import BeautifulSoup
from kgtools.type import RawDoc
# from nltk.tokenize import sent_tokenize

# from kgtools.type import Sentence, Doc


class BaseCleaner:
    __name__ = "Cleaner"

    def __init__(self, rules=None):
        self.rules = rules
        self.root_nodes = {rule["attr"]: rule["value"] for rule in rules if rule["type"] == "root_node"}
        self.removes = {rule["attr"]: rule["value"] for rule in rules if rule["type"] == "remove"}

    def worker(self, html):
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

        for attr, value in self.removes.items():
            if attr == "tag":
                rms = body.findAll(value)
                [rm.extract() for rm in rms]
            elif attr == "id":
                rms = body.findAll(id=value)
                [rm.extract() for rm in rms]
            elif attr == "class":
                rms = body.findAll(class_=value)
                [rm.extract() for rm in rms]

        roots = []
        for attr, value in self.root_nodes.items():
            if attr == "tag":
                roots.extend(body.findAll(value))
            elif attr == "id":
                roots.extend(body.findAll(id=value))
            elif attr == "class":
                roots.extend(body.findAll(class_=value))
        if len(roots) == 0:
            roots = [body]

        texts = []
        for root in roots:
            for li in root.findAll("li"):
                string = li.get_text().strip()
                if len(string) > 0 and string[-1] not in set(".?!:;,"):
                    string = string + "."
                li.clear()
                li.append(string)
            for h in root.findAll(re.compile(r'h[1-6]')):
                string = h.get_text().strip()
                if len(string) > 0 and string[-1] not in set(".?!:;,"):
                    string = string + "."
                h.clear()
                h.append(string)
            for p in root.findAll("p"):
                string = p.get_text().strip()
                if len(string) > 0 and string[-1] not in set(".?!:;,"):
                    string = string + "."
                p.clear()
                p.append(string)

            for table in root.findAll("table"):
                table.clear()
                table.append("-TAB-")
            for img in root.findAll("img"):
                if not img.get("alt") or len(img["alt"]) == 0:
                    img_alt = "-IMG-"
                else:
                    img_alt = img["alt"]
                img.insert_after(img_alt)
            for code in root.findAll("code"):
                string = code.get_text().strip()
                if len(string.split()) > 5 or len(string) > 50:
                    string = "-CODE-"
                # else:
                #     string = "$CODE" + string + "CODE$"
                code.clear()
                code.append(string)

            for pre in root.findAll("pre"):
                pre.clear()
                pre.append("-CODE-.")
            for pre in root.findAll("blockquote"):
                pre.clear()
                pre.append("-QUOTE-.")
            text = root.get_text()
            text = text.strip() + " "
            text = re.sub(r'(https?://.*?)([^a-zA-Z0-9/]?\s)', r'-URL-\2', text)
            texts.append(text)
        return texts

    def clean(self, htmls):
        docs = set()
        for url, html in htmls:
            texts = self.worker(html)
            docs.add(RawDoc(url, texts))
        return docs

    def process(self, htmls):
        return self.clean(htmls)


class JavaDocCleaner(BaseCleaner):
    __name__ = "Javadoc Cleaner"

    def __init__(self, **cfg):
        super(self.__class__, self).__init__(**cfg)

    def worker(self, html):
        soup = BeautifulSoup(html, "lxml")
        strings = []
        for div in soup.select(".block"):
            string = div.get_text().strip()
            if len(string) > 0 and string[-1] not in set(".?!"):
                string = string + "."
            strings.append(string)
        return strings


if __name__ == "__main__":
    html_cleaner = BaseCleaner()