# encoding=utf-8
from __future__ import print_function
import unittest
from lxml import etree
from StringIO import StringIO
import pytest
from iso639 import languages

from roald.adapters.marc21 import Marc21, Concepts


class TestConverter(unittest.TestCase):

    def test_no_language(self):
        # Expects error if no language set
        m21 = Marc21({})
        with pytest.raises(StandardError):
            m21.serialize()

    def test_no_language(self):
        # Expects error if language of wrong datatype (string, not object)
        m21 = Marc21({}, 'nb')
        with pytest.raises(StandardError):
            m21.serialize()

    def test_acronym(self):
        # Expects acronym to be converted to 450 $a, having $g d
        m21 = Marc21({
            '1': {
                'id': '1',
                'prefLabel': {'nb': {
                    'value': 'Forente nasjoner',
                    'hasAcronym': 'FN'
                }},
                'type': ['Topic']
            }
        }, language=languages.get(alpha2='nb'))
        tree = etree.parse(StringIO(m21.serialize()))

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

        c = {
            '1': {
                'id': '1',
                'prefLabel': {'nb': {
                    'value': 'Forente nasjoner'
                }},
                'type': ['Topic']
            }
        }

        # Should accept a dict
        m21 = Marc21(c, language=languages.get(alpha2='nb'))
        self.assertEqual(Concepts, type(m21.concepts))

        # Should accept a Concepts object
        m21 = Marc21(Concepts(c))
        self.assertEqual(Concepts, type(m21.concepts))

        # Should not accept random stuff
        with pytest.raises(ValueError):
            m21 = Marc21('random stuff')

    def test_multiple_types(self):
        # A concept with two types should generate two records
        m21 = Marc21({
            '1': {
                'id': '1',
                'prefLabel': {'nb': {'value': 'Science fiction'}},
                'type': ['GenreForm', 'Topic']
            }
        }, language=languages.get(alpha2='nb'))
        tree = etree.parse(StringIO(m21.serialize()))
        c = tree.xpath('count(//m:record)',
                       namespaces={'m': 'http://www.loc.gov/MARC21/slim'})
        self.assertEqual(2, c)
