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
      packages=['roald', 'roald.models', 'roald.adapters'],
      install_requires=['xmlwitch>=1.0.0', 'isodate', 'lxml', 'rdflib', 'iso-639', 'otsrdflib', 'six', 'skosify'],
      dependency_links=[
        'https://github.com/danmichaelo/xmlwitch/tarball/master#egg=xmlwitch-1.0.2.dev1',
        'https://github.com/NatLibFi/Skosify/tarball/master#egg=skosify-1.0.2.dev1'
      ],
      classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: MIT License',
      ]
      )
