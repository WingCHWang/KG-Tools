#!/usr/bin/env python
# -*- coding: utf-8 -*-

from kgtools.annotation import Lazy


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

    def __len__(self):
        return len(self.tokens)

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
        return " ".join([token.text for token in self.tokens])

    @Lazy
    def lemma_text(self):
        return " ".join([token.lemma for token in self.tokens])

    @Lazy
    def emb(self):
        return sum([token.emb for token in self.tokens]) / len(self)
