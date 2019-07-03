#!/usr/bin/env python
# -*- coding: utf-8 -*-

from kgtools.annotation import Lazy

from kgtools.type.vocab import Vocab


class Token:
    def __init__(self, text, lemma, vocab=Vocab(), pos=None, dep=None, ner=None):
        self.text = text
        self.lemma = lemma
        self.vocab = vocab
        self.lemma_first = vocab.lemma_first
        self.vocab.add(lemma if self.lemma_first else text)
        self.pos = pos
        self.dep = dep
        self.ner = ner

    def __str__(self):
        return self.lemma if self.lemma_first else self.text

    def __hash__(self):
        return hash(str(self))

    @Lazy
    def emb(self):
        return self.vocab.get_emb(str(self))
