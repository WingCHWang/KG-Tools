#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import numpy as np


class Vocab:
    _thread_lock = threading.Lock()
    # _process_lock = multiprocessing.Lock()

    def __init__(self, lemma_first=True, stopwords=None, emb_size=100):
        self.words = set()
        self.embedding = {}
        self.stopwords = stopwords
        self.emb_size = emb_size

        self.lemma_first = lemma_first

        self.ZERO = np.array([0.] * self.emb_size)

    def __new__(cls, *args, **kwargs):
        if not hasattr(Vocab, "_instance"):
            with Vocab._thread_lock:
                if not hasattr(Vocab, "_instance"):
                    Vocab._instance = object.__new__(cls)
        return Vocab._instance

    def __add__(self, other):
        vocab = Vocab(self.lemma_first, self.stopwords, self.emb_size)
        vocab.words = self.words | other.words
        return vocab

    def get_emb(self, word):
        return self.embedding.get(word, self.ZERO)

    def add(self, word):
        self.words.add(word)

    def __len__(self):
        return len(self.words)
