#!/usr/bin/env python
# -*- coding: utf-8 -*-

from kgtools.annotation import Lazy
from kgtools.type.span import Span


class Sentence:
    def __init__(self, text, docs=None, tokens=None, nps=None):
        self.text = text
        self.docs = docs
        self.tokens = tokens
        self.nps = set() if nps is None else nps

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

    def __iadd__(self, other):
        if self == other:
            self.docs |= other.docs
            return self
        else:
            print("The two sentences must have the same 'text'")
            return self

    def add_nps(self, *pairs):
        self.nps.update({Span(self, *pair) for pair in pairs})

    def find_spans(self, *spans, is_lemma=True):
        words = [token.lemma if is_lemma else token.text for token in self.tokens]
        group_dict = {}
        for span in spans:
            length = len(span.split())
            if length in group_dict:
                group_dict[length].add(span)
            else:
                group_dict[length] = {span}
        group_dict = dict(sorted(group_dict.items(), key=lambda x: x[0], reverse=True))
        index = 0
        result_dict = {}
        while index < len(self):
            for length, group in group_dict.items():
                span = " ".join(words[index:index + length])
                if span in group:
                    result_dict[span] = index
                    index += length
                    break
            else:
                index += 1
        result = [(span, result_dict.get(span, -1)) for span in spans]
        return result

    @Lazy
    def tokenized_text(self):
        return " ".join([token.text for token in self.tokens])

    @Lazy
    def lemma_text(self):
        return " ".join([token.lemma for token in self.tokens])

    @Lazy
    def emb(self):
        return sum([token.emb for token in self.tokens]) / len(self)
