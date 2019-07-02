#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nltk.tokenize import sent_tokenize as st, word_tokenize as wt
import re
import spacy
from type import Vocab, Doc, Sentence, Token


class Tokenizer:

    __name__ = "Tokenizer"

    PUNC_TABLE = {ord(zh): ord(en) for zh, en in zip('‘’“”…，。！？【】（）％＃＠＆：',
                                                     '\'\'"".,.!?[]()%#@&:')}

    # MARK_TABLE = {
    #     "__CODE__": ""
    # }

    def __init__(self, vocab=Vocab(), code_patterns=None):
        self.vocab = vocab
        self.patterns = [
            re.compile(r'([a-zA-Z_][a-zA-Z\d_]*)(\.\1)+'),
            re.compile(r'[a-zA-Z_]([a-z][A-Z])'),
            re.compile(r'[a-zA-Z_][a-zA-Z\d_]*\([a-zA-Z\d_]*\)(\.[a-zA-Z_][a-zA-Z\d_]*\([a-zA-Z\d_]*\))'),
            re.compile(r'')
        ]
        code_patterns = code_patterns if code_patterns is not None else []
        self.patterns.extend(code_patterns)
        self.nlp = spacy.load('en')

        hyphen_re = re.compile(r"[A-Za-z\d]+-[A-Za-z\d]+|'[a-z]+|''")
        prefix_re = spacy.util.compile_prefix_regex(self.nlp.Defaults.prefixes)
        infix_re = spacy.util.compile_infix_regex(self.nlp.Defaults.infixes)
        suffix_re = spacy.util.compile_suffix_regex(self.nlp.Defaults.suffixes)
        self.nlp.tokenizer = spacy.tokenizer.Tokenizer(self.nlp.vocab, prefix_search=prefix_re.search, infix_finditer=infix_re.finditer,
                               suffix_search=suffix_re.search, token_match=hyphen_re.match)

    def sent_tokenize(self, text):
        text = text.translate(Tokenizer.PUNC_TABLE)
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'({[^{}]*?)(\?)([^{}]*?})', r'\1__?__\3', text)
        text = re.sub(r'(\[[^\[\]]*?)(\?)([^\[\]]*?\])', r'\1__?__\3', text)
        text = re.sub(r'(\([^()]*?)(\?)([^()]*?\))', r'\1__?__\3', text)
        text = re.sub(r'(\<[^<>]*?)(\?)([^<>]*?\>)', r'\1__?__\3', text)
        text = re.sub(r'("[^"]*?)(\?)([^"]*?")', r'\1__?__\3', text)

        text = re.sub(r'({[^{}]*?)(!)([^{}]*?})', r'\1__!__\3', text)
        text = re.sub(r'(\[[^\[\]]*?)(!)([^\[\]]*?\])', r'\1__!__\3', text)
        text = re.sub(r'(\([^()]*?)(!)([^()]*?\))', r'\1__!__\3', text)
        text = re.sub(r'(\<[^<>]*?)(!)([^<>]*?\>)', r'\1__!__\3', text)
        text = re.sub(r'("[^"]*?)(!)([^"]*?")', r'\1__!__\3', text)

        text = re.sub(r'({[^{}]*?)(\.)([^{}]*?})', r'\1__.__\3', text)
        text = re.sub(r'(\[[^\[\]]*?)(\.)([^\[\]]*?\])', r'\1__.__\3', text)
        text = re.sub(r'(\([^()]*?)(\.)([^()]*?\))', r'\1__.__\3', text)
        text = re.sub(r'(\<[^<>]*?)(\.)([^<>]*?\>)', r'\1__.__\3', text)
        text = re.sub(r'("[^"]*?)(\.)([^"]*?")', r'\1__.__\3', text)

        text = text.replace("e.g.", "__eg__")
        text = text.replace("E.g.", "__eg__")
        text = text.replace("E.G.", "__eg__")
        text = text.replace("i.e.", "__ie__")
        text = text.replace("I.e.", "__ie__")
        text = text.replace("I.E.", "__ie__")
        sentences = []
        for sent in st(text):
            if self.__pre_check(sent):
                sent_text = sent.replace("__eg__", "e.g.").replace("__ie__", "i.e.").replace("__?__", "?").replace("__!__", "!").replace("__.__", ".")
                sent_text = re.sub(r'^(-CODE- |-TAB- |-IMG- |-URL- )(.*)', r'\2', sent_text)
                sent_text = re.sub(r'^(\()(.*)(\))$', r'\2', sent_text)
                sent_text = re.sub(r'^(\[)(.*)(\])$', r'\2', sent_text)
                sent_text = re.sub(r'^({)(.*)(})$', r'\2', sent_text)
                words = sent_text.split()
                if re.search(r'^[^A-Z]', words[0]) is not None and words[1] in {"A", "An", "The", "This", "That", "You", "We"} and re.search(r'^[^A-Z]', words[2]) is None:
                    sent_text = " ".join(words[1:])
                sent_text = sent_text.strip()
                if self.__post_check(sent_text):
                    sentences.append(Sentence(sent_text))
        # text = re.sub(r'\n(.+?[^.?!])\n([A-Z])', r'\n\n\2', text)
        # text = re.sub(r'\s+', " ", text.strip())
        # text = re.sub(r'([?!.]+) ', r'\1\n', text)
        # sentences = set(text.split("\n"))
        return sentences

    def __pre_check(self, sentence):
        if len(sentence) == 0 or not (5 <= len(sentence.split()) <= 200):
            return False
        # check chinese
        if any(["\u4e00" <= ch <= "\u9fff" for ch in sentence]):
            return False
        return True

    def __post_check(self, sentence):
        if re.search(r'^[0-9a-zA-Z"\'<(]', sentence) is None:
            return False
        if sentence.count('[') != sentence.count(']'):
            return False
        if sentence.count('(') != sentence.count(')'):
            return False
        if sentence.count('{') != sentence.count('}'):
            return False
        if sentence.count('"') != sentence.count('"'):
            return False
        if sentence.count(':') > 3 or sentence.count('=') > 3 or sentence.count('[') > 3 or sentence.count('{') > 3:
            return False
        return True

    def word_tokenize_nltk(self, sentence):
        sentence = sentence.replace("e.g.", "__eg__").replace("E.g.", "__eg__").replace("E.G.", "__eg__").replace("i.e.", "__ie__").replace("I.e.", "__ie__").replace("I.E.", "__ie__")
        sentence = re.sub(r'([a-zA-Z ])\.([a-zA-Z ])', r'\1 . \2', sentence)
        sentence = re.sub(r'\s+', ' ', sentence)

        tokens = wt(sentence)
        tokens = [t.replace("__eg__", "e.g.").replace("__ie__", "i.e.") for t in tokens]
        return tokens

    def word_tokenize_spacy(self, sentence):
        # sentence = sentence.replace("__CODE__", "CODE$").replace("__IMG__", "IMG$").replace("__TAB__", "TAB$").replace("__URL__", "URL$").replace("__QUOTE__", "QUOTE$")
        tokens = [Token(t.text, t.lemma_, vocab=self.vocab, pos=t.pos_, dep=t.dep_) for t in self.nlp(sentence)]
        # for token in tokens:
        #     token.text = token.text.replace("CODE$", "__CODE__").replace("IMG$", "__IMG__").replace("TAB$", "__TAB__").replace("URL$", "__URL__").replace("QUOTE$", "__QUOTE__")
        #     token.lemma = token.lemma.replace("code$", "__code__").replace("img$", "__img__").replace("tab$", "__tab__").replace("url$", "__url__").replace("quote$", "__quote__")
        return tokens

    def tokenize(self, rawdocs):
        docs = set()
        sent2sent = {}
        for rawdoc in rawdocs:
            sents = []
            for text in rawdoc:
                sents.extend(self.sent_tokenize(text))
            if len(sents) > 0:
                docs.add(Doc(rawdoc.url, sents))
                for sent in sents:
                    if sent in sent2sent:
                        new_sent = sent + sent2sent.pop(sent)
                        sent2sent[new_sent] = new_sent
                    else:
                        sent2sent[sent] = sent
        sentences = set(sent2sent.values())
        for sent in sentences:
            tokens = self.word_tokenize_nltk(sent.text)
            sent.tokens = self.word_tokenize_spacy(" ".join(tokens))
            sent.docs = {doc.url for doc in sent.docs}
        return docs, sentences, self.vocab

    # def __handle_sent(self, rawdocs):
    #     docs = set()
    #     sent2sent = {}
    #     for rawdoc in rawdocs:
    #         sents = []
    #         for text in rawdoc:
    #             sents.extend(self.sent_tokenize(text))
    #         if len(sents) > 0:
    #             docs.add(Doc(rawdoc.url, sents))
    #             for sent in sents:
    #                 if sent in sent2sent:
    #                     new_sent = sent + sent2sent.pop(sent)
    #                     sent2sent[new_sent] = new_sent
    #                 else:
    #                     sent2sent[sent] = sent
    #     return docs, [sent2sent]

    # def __handle_word(self, sents):
    #     sentence_texts = []
    #     for sent in sents:
    #         tokens = self.word_tokenize_nltk(sent.text)
    #         sentence_texts.append((sent, " ".join(tokens)))
    #     return sentence_texts

    # def tokenize_parallel(self, rawdocs):

    #     docs, sent2sent_list = parallel(self.__handle_sent, list(rawdocs))
    #     sent2sent = sent2sent_list.pop(0)
    #     for _ in range(len(sent2sent_list)):
    #         cur = sent2sent_list.pop(0)
    #         for sent in cur.keys():
    #             if sent in sent2sent:
    #                 new_sent = sent + sent2sent.pop(sent)
    #                 sent2sent[new_sent] = new_sent
    #             else:
    #                 sent2sent[sent] = sent

    #     sentences = set(sent2sent.values())

    #     pairs = parallel(self.__handle_word, list(sentences))
    #     for sent, sent_text in pairs:
    #         sent.tokens = self.word_tokenize_spacy(sent_text)
    #         sent.docs = {doc.url for doc in sent.docs}
    #     return docs, sentences

    def find_code(self, sentence):
        '''find code elements

        [description]

        Arguments:
            sentence {[type]} -- [description]
        '''
        for pattern in self.patterns:
            pass


if __name__ == "__main__":
    t = Tokenizer()
    tokens = t.word_tokenize("Those are the language-specific tokenizer(exceptions), for example:__CODE__")
    for token in tokens:
        print(token.text, token.lemma, token.pos, token.dep)
