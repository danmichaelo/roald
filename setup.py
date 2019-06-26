#!/usr/bin/env python
# encoding=utf-8

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='roald',
      version='0.1.dev1',
      description='Roald III indexing tool',
      author='Dan Michael Heggø',
      author_email='danmichaelo@gmail.com',
      url='https://github.com/scriptotek/roald',
      license='MIT',
      packages=['roald', 'roald.models', 'roald.adapters'],
      install_requires=['xmlwitch==0.3.0',  # Note: we need to use the danmichaelo fork, since I haven't been able to get it merged (or get any response from the original author at all).
                        'isodate',
                        'lxml',
                        'rdflib',
                        'iso-639',
                        'otsrdflib>=0.5.0',
                        'six',
                        'skosify',
                        'xmlwitch @ git+https://github.com/danmichaelo/xmlwitch.git@0.3.0#egg=xmlwitch-0.3.0',
                        ],
      classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: MIT License',
      ]
      )
