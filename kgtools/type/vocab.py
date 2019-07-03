#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import numpy as np


class Vocab:
    __thread_lock = threading.Lock()
    # _process_lock = multiprocessing.Lock()

    def __new__(cls, *args, **kwargs):
        if not hasattr(Vocab, "_instance"):
            with Vocab.__thread_lock:
                if not hasattr(Vocab, "_instance"):
                    Vocab._instance = object.__new__(cls)
        return Vocab._instance

    def __init__(self, lemma_first=True, stopwords=None, emb_size=100):
        self.words = set()
        self.embedding = {}
        self.stopwords = stopwords
        self.emb_size = emb_size

        self.lemma_first = lemma_first

        self.ZERO = np.array([0.] * self.emb_size)

    @classmethod
    def new_instance(cls, *args, **kwargs):
        instance = object.__new__(cls)
        instance.__init__(*args, **kwargs)
        return instance

    def get_emb(self, word):
        return self.embedding.get(word, self.ZERO)

    def add(self, word):
        self.words.add(word)

    def __len__(self):
        return len(self.words)

    def __getitem__(self, key):
        return self.get_emb(key)

    def __add__(self, other):
        vocab = Vocab(self.lemma_first, self.stopwords, self.emb_size)
        vocab.words = self.words | other.words
        vocab.embedding = dict(set(self.embedding.items()) | (other.embedding.items()))
        vocab.stopwords = self.stopwords
        if self.stopwords is not None:
            if other.stopwords is not None:
                self.stopwords.update(other.stopwords)
        else:
            self.stopwords = other.stopwords
        return vocab

    def __iadd__(self, other):
        self.words |= other.words
        self.embedding.update(other.embedding)
        if self.stopwords is not None:
            if other.stopwords is not None:
                self.stopwords.update(other.stopwords)
        else:
            self.stopwords = other.stopwords
        return self
