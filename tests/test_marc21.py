# encoding=utf-8
from __future__ import print_function
import unittest
from lxml import etree
from StringIO import StringIO

from roald.models.marc21 import Marc21


class TestConverter(unittest.TestCase):

    def test_acronym(self):
        # Expects acronym to be converted to 450 $a, having $g d
        concepts = {
            '1': {
                'id': '1',
                'prefLabel': {'nb': 'Forente nasjoner'},
                'acronym': ['FN'],
                'type': ['Topic']
            }
        }
        m21 = Marc21()
        f = StringIO(m21.convert(concepts))
        tree = etree.parse(f)

        f150 = tree.xpath('//m:record/m:datafield[@tag="150"]' +
                          '[./m:subfield[@code="a"]/text() = "Forente nasjoner"]',
                          namespaces={'m': 'http://www.loc.gov/MARC21/slim'})

        f450 = tree.xpath('//m:record/m:datafield[@tag="450"]' +
                          '[./m:subfield[@code="a"]/text() = "FN"]' +
                          '[./m:subfield[@code="g"]/text() = "d"]',
                          namespaces={'m': 'http://www.loc.gov/MARC21/slim'})

        self.assertEqual(1, len(f150))
        self.assertEqual(1, len(f450))
