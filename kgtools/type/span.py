#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Span:
    def __init__(self, text, tokens):
        self.text = text
        self.tokens = tokens

    def __str__(self):
        return text

    def __add__(self, other):
        return Span(self.text + " " + other.text, self.tokens + other.tokens)