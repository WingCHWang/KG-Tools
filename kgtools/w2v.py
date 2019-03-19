#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gensim.models import Word2Vec as w2v
from kgtools.type import Vocab


class Word2Vec:
    def __init__(self, vocab=Vocab(), min_count=1):
        self.vocab = vocab
        self.size = vocab.emb_size
        self.min_count = min_count

    def train(self, sentences):
        corpus = [[str(token) for token in sent] for sent in sentences]
        model = w2v(corpus, size=self.size, min_count=self.min_count)
        for word in model.wv.vocab.keys():
            self.vocab.embedding[word] = model.wv[word]
        # self.vocab.add("-UNKNOWN-")
        # self.vocab.embedding["-UNKNOWN-"] = np.arrar([0.] * self.size)
