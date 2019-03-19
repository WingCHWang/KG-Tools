#!/usr/bin/env python
# -*- coding: utf-8 -*-

from kgtools.wrapper import Singleton, Lazy
import numpy as np
import threading


class Vocab:
    _instance_lock = threading.Lock()

    def __init__(self, stopwords=None, emb_size=100):
        self.words = set()
        self.embedding = {}
        self.stopwords = stopwords
        self.emb_size = emb_size

        self.ZERO = np.array([0.] * self.emb_size)

    def __new__(cls, *args, **kwargs):
        if not hasattr(Vocab, "_instance"):
            with Vocab._instance_lock:
                if not hasattr(Vocab, "_instance"):
                    Vocab._instance = object.__new__(cls)
        return Vocab._instance

    def get_emb(self, word):

        return self.embedding.get(word, self.ZERO)

    def add(self, word):
        self.words.add(word)

    def __len__(self):
        return len(self.words)


class Token:
    def __init__(self, text, lemma, vocab=Vocab(), pos=None, dep=None, lemma_first=True):

        self.text = text
        self.lemma = lemma
        self.vocab = vocab
        self.vocab.add(lemma if lemma_first else text)
        self.pos = pos
        self.dep = dep

        self.lemma_first = lemma_first

    def __str__(self):
        return self.lemma if self.lemma_first else self.text

    def __hash__(self):
        return hash(str(self))

    @Lazy
    def emb(self):
        return self.vocab.get_emb(str(self))


class Span:
    def __init__(self, text, tokens):
        self.text = text
        self.tokens = tokens

    def __add__(self, other):
        return Span(self.text + " " + other.text, self.tokens + other.tokens)


class Sentence:
    def __init__(self, text, docs=None, tokens=None):
        self.text = text
        self.docs = docs
        self.tokens = tokens

    def __str__(self):
        return self.text

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __iter__(self):
        return iter(self.tokens)

    def __add__(self, other):
        if self == other:
            sent = Sentence(self.text, self.docs | other.docs, self.tokens)
            for doc in sent.docs:
                doc.sents[doc.sent2index[sent]] = sent
            return sent

        else:
            print("The two sentences must have the same 'text'")
            return self

    @Lazy
    def tokenized_text(self):
        return " ".join([str(token) for token in self.tokens])

    @Lazy
    def lemma_text(self):
        return " ".join([token.lemma for token in self.tokens])

    @Lazy
    def emb(self):
        pass


class Doc:
    def __init__(self, url, sents):
        self.url = url
        self.sents = sents
        for sent in sents:
            sent.docs = {self}
        self.sent2index = {sent: i for i, sent in enumerate(self.sents)}

    def __str__(self):
        return self.url

    def __iter__(self):
        return iter(self.sents)


class RawDoc:
    def __init__(self, url, texts):
        self.url = url
        self.texts = texts

    def __iter__(self):
        return iter(self.texts)


if __name__ == "__main__":
    d1 = {Sentence("hello"): 1, Sentence("world"): 2, Sentence("!"): 3}
    print(d1[Sentence("hello")])
