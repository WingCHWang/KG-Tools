#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from kgtools.cleaner import BaseCleaner
from kgtools.tokenizer import Tokenizer
from kgtools.w2v import Word2Vec
from kgtools.func import parallel
from kgtools.type import Vocab
from kgtools.saver import Saver

from kgtools.wrapper import TimeLog


class Pipeline:
    def __init__(self, vocab=Vocab(), conf=None):
        self.vocab = vocab
        conf = {} if conf is None else conf
        self.cleaner = BaseCleaner(**(conf.get("cleaner", {})))
        self.tokenizer = Tokenizer(**(conf.get("tokenizer", {})))
        self.w2v = Word2Vec(**(conf.get("word2vec", {})))

    def process(self, data):
        @TimeLog
        def clean():
            return parallel(self.cleaner.clean, list(data.items()))
        rawdocs = clean()

        @TimeLog
        def tokenize():
            return self.tokenizer.tokenize(rawdocs)
        docs, sentences = tokenize()

        @TimeLog
        def word2vec():
            self.w2v.train(sentences)
        word2vec()

        return docs, sentences


if __name__ == "__main__":
    conf = {
        "cleaner": {
            "rules": [{"type": "root_node", "attr": "class", "value": "devsite-article-body"}]
        }
    }
    vocab = Vocab()
    pipeline = Pipeline(conf=conf)
    data = Saver.load("testdata/guide.bin")
    docs, sentences = pipeline.process(data)

    Saver.dump(docs, "testdata/docs.bin")
    Saver.dump(sentences, "testdata/sentences.bin")

    with Path("testdata/sentences.txt").open("w", encoding="utf-8") as f:
        f.write("\n".join([str(sent) for sent in sentences]))
    with Path("testdata/tokens.txt").open("w", encoding="utf-8") as f:
        f.write("\n".join([str(sent) + "\n" + sent.tokenized_text + "\n" + sent.lemma_text + "\n" for sent in sentences]))
    with Path("testdata/vocab.txt").open("w", encoding="utf-8") as f:
        f.write("\n".join(sorted(vocab.words, key=lambda x: x)))
    print(vocab.get_emb("-PRON-"))
