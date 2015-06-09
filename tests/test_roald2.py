# encoding=utf-8
from __future__ import print_function
import unittest
from lxml import etree
from StringIO import StringIO
import pytest

from roald.models.roald2 import Roald2, Concept


class TestConverter(unittest.TestCase):

    def test_set_type(self):
        c = Concept('Topic')
        self.assertEqual(['Topic'], c.get('type'))
        c.set_type('Geographic')
        self.assertEqual(['Geographic'], c.get('type'))
        c.set_type('GenreForm')
        self.assertEqual(['GenreForm', 'Topic'], c.get('type'))
        c.set_type('CompoundHeading')
        self.assertEqual(['CompoundHeading'], c.get('type'))
        c.set_type('VirtualCompoundHeading')
        self.assertEqual(['VirtualCompoundHeading'], c.get('type'))

        with pytest.raises(ValueError):
            c.set_type('SomeRandomStuff')

    def test_read_concept(self):

        data = """
        id= REAL030070
        te= Atlas
        bf= Verdensatlas
        tio= 2015-02-20T13:08:04Z
        """

        rii = Roald2()
        concepts = [x for x in rii.read_concept(data, 'GenreForm')]

        self.assertEqual(1, len(concepts))
        self.assertEqual(set(['GenreForm', 'Topic']), set(concepts[0].get('type')))
        self.assertEqual('REAL030070', concepts[0].get('id'))
        self.assertEqual('Atlas', concepts[0].get('prefLabel').get('nb'))
        self.assertEqual('Verdensatlas', concepts[0].get('altLabel').get('nb')[0])
