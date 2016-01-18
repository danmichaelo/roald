# encoding=utf-8
from __future__ import print_function
import unittest
import pytest

from roald.util import array_set, array_get, array_add

class TestUtil(unittest.TestCase):

    def test_array_set(self):
        x = {}
        array_set(x, 'prefLabel.nb.test', 'Test')

        self.assertEqual('Test', x['prefLabel']['nb']['test'])

    def test_array_get(self):
        x = {'prefLabel': {'nb': {'test': 42}}}

        self.assertEqual(42, array_get(x, 'prefLabel.nb.test'))


    def test_array_get_default(self):
        x = {'prefLabel': {'nb': {'test': 42}}}

        self.assertEqual(53, array_get(x, 'prefLabel.nb.other', 53))

    def test_array_get_deep_default(self):
        x = {}

        self.assertEqual(61, array_get(x, 'prefLabel.en', 61))

    def test_array_add(self):
        x = {}
        array_add(x, 'note.en', 'Note 1')
        array_add(x, 'note.en', 'Note 2')

        self.assertEqual(2, len(x['note']['en']))
        self.assertEqual('Note 1', x['note']['en'][0])
        self.assertEqual('Note 2', x['note']['en'][1])
