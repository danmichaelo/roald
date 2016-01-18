# encoding=utf-8
from __future__ import print_function
import unittest
from lxml import etree
import pytest
from copy import copy

from roald.models.resources import Concept
from roald.models.resources import Collection
from roald.models.resources import Label
from roald.models.resources import Resources
from roald.errors import InvalidDataException

class TestConcept(unittest.TestCase):

    def test_set_type(self):
        c = Concept('Topic')
        self.assertEqual(['Topic'], c.type)
        c.set_type('Geographic')
        self.assertEqual(['Geographic'], c.type)
        c.set_type('GenreForm')
        self.assertEqual(['GenreForm'], c.type)
        c.set_type('CompoundHeading')
        self.assertEqual(['CompoundHeading'], c.type)
        c.set_type('VirtualCompoundHeading')
        self.assertEqual(['VirtualCompoundHeading'], c.type)

        with pytest.raises(ValueError):
            c.set_type('SomeRandomStuff')

    def test_attr_chain(self):
        concept = Concept().set('id', 2).set('prefLabel.nb', Label('Test'))
        self.assertEqual(2, concept.id)
        assert  'Test' == concept.prefLabel['nb'].value

    def test_label_conversion(self):
        concept = Concept().set('prefLabel.nb', 'Test')
        assert isinstance(concept.prefLabel['nb'], Label)

class TestResources(unittest.TestCase):

    testdata1 = [
        {
            'id': 'REAL012789',
            'type': ['Topic'],
            'prefLabel': {'nb': {'value': 'Fornybar energi'}},
            'altLabel': {'nb': [{'value': 'Fornybare energikilder'}]},
            'hiddenLabel': {'nb': [{'value': 'Forybar energi'}]}
        },
        {
            'id': 'REAL013995',
            'type': ['Topic'],
            'prefLabel': {'nb': {'value': 'Livssyklusanalyse'}}
        },
        {
            'id': 'REAL022146',
            'type': ['VirtualCompoundConcept'],
            'component': ['REAL012789', 'REAL013995']
        },
        {
            'id': 'REAL022147',
            'type': ['Collection'],
            'member': ['REAL012789', 'REAL013995'],
            'prefLabel': {'nb': {'value': 'Energi'}}
        }
    ]

    def test_load(self):
        # Test that we can load resources
        resources = Resources().load(self.testdata1)
        assert len(resources) == 4

    def test_load_fail(self):
        # Test that load fails if given data of invalid type
        with pytest.raises(InvalidDataException):
            resources = Resources().load({'key': 'val'})
        with pytest.raises(InvalidDataException):
            resources = Resources().load('Hei')
        with pytest.raises(InvalidDataException):
            resources = Resources().load(3)

    def test_serialize(self):
        # Test load/serialize roundtrip
        resources = Resources().load(self.testdata1)
        assert resources.serialize() == self.testdata1

    def test_getitem_lookup(self):
        # Test that we can use Resources as a dict
        resources = Resources().load(self.testdata1)
        assert resources['REAL012789'].id == 'REAL012789'

    def test_instance_of_concept(self):
        resources = Resources().load(self.testdata1)
        assert isinstance(resources['REAL012789'], Concept)

    def test_instance_of_collection(self):
        resources = Resources().load(self.testdata1)
        assert isinstance(resources['REAL022147'], Collection)

    def test_instance_of_label(self):
        resources = Resources().load(self.testdata1)
        assert isinstance(resources['REAL012789'].prefLabel['nb'], Label)

    def test_term_lookup(self):
        resources = Resources().load(self.testdata1)
        assert 'REAL012789' == resources.get(term='Fornybar energi').id
        assert 'REAL012789' == resources.get(term='Fornybar energi', lang='nb').id
        with pytest.raises(KeyError):
            assert 'REAL012789' == resources.get(term='Fornybar energi', lang='en').id
        assert 'REAL013995' == resources.get(term='Livssyklusanalyse').id
        assert 'REAL022146' == resources.get(term='Fornybar energi : Livssyklusanalyse').id

    # def test_builder(self):
    #     c = Resources()
    #     # c.add('REAL012789').setPrefLabel('Fornybar energi', 'nb')

    #     # TODO ...
