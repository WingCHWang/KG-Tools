#!/usr/bin/env python
# -*- coding: utf-8 -*-
import dill
import json
from pathlib import Path
from enum import Enum, unique


@unique
class FileFormat(Enum):
    JSON = "json"
    BINARY = "binary"


class Saver:
    @staticmethod
    def load(file_name, file_format=FileFormat.BINARY):
        if file_format == FileFormat.BINARY:
            with Path(file_name).open("rb") as f:
                return dill.load(f)
        elif file_format == FileFormat.JSON:
            with Path(file_name).open("r", encoding="utf-8") as f:
                return json.load(f)
        else:
            raise NotImplementedError

    @staticmethod
    def dump(obj, file_name, file_format=FileFormat.BINARY):
        Path(file_name).parent.mkdir(parents=True, exist_ok=True)
        if file_format == FileFormat.BINARY:
            with Path(file_name).open("wb") as f:
                dill.dump(obj, f)
        elif file_format == FileFormat.JSON:
            with Path(file_name).open("w", encoding="utf-8") as f:
                json.dump(obj, f, indent=4)
        else:
            raise NotImplementedError

    @staticmethod
    def transform(file, src_fmt, tgt_fmt):
        Saver.dump(Saver.load(file, src_fmt), tgt_fmt)
