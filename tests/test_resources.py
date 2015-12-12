# encoding=utf-8
from __future__ import print_function
import unittest
from lxml import etree
from StringIO import StringIO
import pytest

from roald.models.resources import Concept
from roald.models.resources import Resources


class TestResources(unittest.TestCase):

    def test_set_type(self):
        c = Concept('Topic')
        self.assertEqual(['Topic'], c.get('type'))
        c.set_type('Geographic')
        self.assertEqual(['Geographic'], c.get('type'))
        c.set_type('GenreForm')
        self.assertEqual(['GenreForm'], c.get('type'))
        c.set_type('CompoundHeading')
        self.assertEqual(['CompoundHeading'], c.get('type'))
        c.set_type('VirtualCompoundHeading')
        self.assertEqual(['VirtualCompoundHeading'], c.get('type'))

        with pytest.raises(ValueError):
            c.set_type('SomeRandomStuff')

    def test_term_lookup(self):
        resources = Resources()
        resources.load({
            'REAL012789': {
                'id': 'REAL012789',
                'prefLabel': {'nb': {'value': 'Fornybar energi'}}
            },
            'REAL013995': {
                'id': 'REAL013995',
                'prefLabel': {'nb': {'value': 'Livssyklusanalyse'}}
            },
            'REAL022146': {
                'id': 'REAL022146',
                'component': ['REAL012789', 'REAL013995']
            }
        })
        self.assertEqual('REAL012789', resources.get(term='Fornybar energi')['id'])
        self.assertEqual('REAL013995', resources.get(term='Livssyklusanalyse')['id'])
        self.assertEqual('REAL022146', resources.get(term='Fornybar energi : Livssyklusanalyse')['id'])

    def test_builder(self):
        c = Resources()
        # c.add('REAL012789').setPrefLabel('Fornybar energi', 'nb')

        # TODO ...
