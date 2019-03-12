#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pickle
from pathlib import Path


class Saver:
    @staticmethod
    def load(bin_file):
        with Path(bin_file).open("rb") as f:
            return pickle.load(f)

    @staticmethod
    def dump(obj, bin_file):
        Path(bin_file).parent.mkdir(parents=True, exist_ok=True)
        with Path(bin_file).open("wb") as f:
            pickle.dump(obj, f)
