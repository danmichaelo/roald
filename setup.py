#!/usr/bin/env python
# encoding=utf-8

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='roald',
      version='0.1.dev0',
      description='Roald III indexing tool',
      author='Dan Michael Heggø',
      author_email='danmichaelo@gmail.com',
      url='https://github.com/scriptotek/roald',
      license='MIT',
      packages=['roald', 'roald.models'],
      install_requires=['xmlwitch', 'isodate', 'lxml', 'rdflib', 'iso-639', 'otsrdflib']
      )
