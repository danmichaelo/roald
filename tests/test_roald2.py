# encoding=utf-8
from __future__ import print_function
import unittest
from lxml import etree
from StringIO import StringIO
import pytest

from roald.adapters.roald2 import Roald2
from roald.models.vocabulary import Vocabulary


class TestConverter(unittest.TestCase):

    def test_read_concept(self):

        data = """
        id= REAL030070
        te= Atlas
        bf= Verdensatlas
        tio= 2015-02-20T13:08:04Z
        """

        voc = Vocabulary()
        voc.default_language = 'sv'

        rii = Roald2(voc)
        concepts = [x for x in rii.read_concept(data, 'GenreForm', 'sv')]

        self.assertEqual(1, len(concepts))
        self.assertEqual(set(['GenreForm']), set(concepts[0].get('type')))
        self.assertEqual('REAL030070', concepts[0].get('id'))
        self.assertEqual('Atlas', concepts[0]['prefLabel']['sv']['value'])
        self.assertEqual('Verdensatlas', concepts[0]['altLabel']['sv'][0]['value'])
