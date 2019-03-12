#!/usr/bin/env python
# -*- coding: utf-8 -*-

from kgtools.wrapper import Singleton, Lazy


@Singleton
class Vocab:
    def __init__(self, stopwords=None):
        self.words = set()
        self.embs = {}
        self.stopwords = stopwords

    def get_emb(self, word):
        return self.embs[word]

    def __len__(self):
        return len(self.words)


class Token:
    def __init__(self, vocab, text, lemma, pos, dep):
        pass


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


if __name__ == "__main__":
    d1 = {Sentence("hello"): 1, Sentence("world"): 2, Sentence("!"): 3}
    print(d1[Sentence("hello")])
    
