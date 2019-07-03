#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(name='kgtools',
      version='0.1.6',
      description='The tools for KG Team of Fudan SE LAB',
      url='https://github.com/FudanSELab/KG-Tools',
      author='Chong Wang',
      author_email='18212010030@fudan.edu.cn',
      license='MIT',
      packages=['kgtools'],
      zip_safe=False,
      install_requires=['bs4', 'lxml', 'spacy', 'nltk', 'gensim', 'numpy', 'pathos', 'dill', 'aiohttp'],
      python_requires='>=3'
      )

