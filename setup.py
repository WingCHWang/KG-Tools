#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

__version__ = '0.1.11'

setup(
    name='kgtools',
    version=__version__,
    description='The tools for KG Team of Fudan SE LAB',
    url='https://github.com/FudanSELab/KG-Tools',
    author='Chong Wang',
    author_email='18212010030@fudan.edu.cn',
    license='MIT',
    packages=find_packages(exclude=("docs", "test")),
    zip_safe=False,
    python_requires='>=3',
    install_requires=[
        'bs4',
        'lxml',
        'spacy',
        'nltk',
        'gensim',
        'numpy',
        'pathos',
        'dill',
        'aiohttp'
    ],
)
