# encoding=utf-8
from __future__ import print_function
import unittest
from lxml import etree
import pytest
from iso639 import languages
try:
    from BytesIO import BytesIO  # Python 2
except ImportError:
    from io import BytesIO  # Python 3

from roald.adapters.marc21 import Marc21
from roald.models.resources import Resources
from roald.models.vocabulary import Vocabulary


class TestConverter(unittest.TestCase):

    def test_no_language(self):
        # Expects error if no language set
        m21 = Marc21(Vocabulary())
        with pytest.raises(RuntimeError):
            m21.serialize()

    def test_no_language(self):
        # Expects error if language of wrong datatype (string, not object)
        m21 = Marc21(Vocabulary())
        with pytest.raises(RuntimeError):
            m21.serialize()

    def test_acronym(self):
        # Expects acronym to be converted to 450 $a, having $g d
        voc = Vocabulary()
        voc.resources.load([
            {
                'id': '1',
                'prefLabel': {'nb': {
                    'value': 'Forente nasjoner',
                    'hasAcronym': 'FN'
                }},
                'type': ['Topic']
            }
        ])
        voc.default_language = languages.get(alpha2='nb')
        m21 = Marc21(voc)
        tree = etree.parse(BytesIO(m21.serialize()))

        f150 = tree.xpath('//m:record/m:datafield[@tag="150"]' +
                          '[./m:subfield[@code="a"]/text() = "Forente nasjoner"]',
                          namespaces={'m': 'http://www.loc.gov/MARC21/slim'})

        f450 = tree.xpath('//m:record/m:datafield[@tag="450"]' +
                          '[./m:subfield[@code="a"]/text() = "FN"]' +
                          '[./m:subfield[@code="g"]/text() = "d"]',
                          namespaces={'m': 'http://www.loc.gov/MARC21/slim'})

        self.assertEqual(1, len(f150))
        self.assertEqual(1, len(f450))

    def test_load(self):
        # Should accept a Vocabulary object

        c = [
                {
                    'id': '1',
                    'prefLabel': {'nb': {
                        'value': 'Forente nasjoner'
                    }},
                    'type': ['Topic']
                }
            ]
        voc = Vocabulary()
        voc.resources.load(c)
        voc.default_language = languages.get(alpha2='nb')

        m21 = Marc21(voc)
        self.assertEqual(Resources, type(m21.vocabulary.resources))


    def test_multiple_types(self):
        # A concept with two types should generate two records
        voc = Vocabulary()
        voc.default_language = languages.get(alpha2='nb')
        voc.resources.load([{
            'id': '1',
            'prefLabel': {'nb': {'value': 'Science fiction'}},
            'type': ['GenreForm', 'Topic']
        }])
        m21 = Marc21(voc)
        tree = etree.parse(BytesIO(m21.serialize()))
        c = tree.xpath('count(//m:record)',
                       namespaces={'m': 'http://www.loc.gov/MARC21/slim'})
        self.assertEqual(2, c)
