from iso639 import languages
import json
import re
from .resources import Resources
# from .collections import Collections


class Vocabulary(object):

    def __init__(self):
        super(Vocabulary, self).__init__()
        self._uri_format = None
        self._default_language = None
        self.resources = Resources()
        # self.collections = Collections()

    @property
    def uri_format(self):
        return self._uri_format

    @uri_format.setter
    def uri_format(self, value):
        # @TODO: Check type
        self._uri_format = value

    @property
    def default_language(self):
        return self._default_language

    @default_language.setter
    def default_language(self, value):
        # @TODO: Check type
        self._default_language = value

    def uri(self, id):  # TODO: Move into Concept/Collection class
        if self._uri_format is None:
            raise Exception('URI format has not been set.')
        return self._uri_format.format(id=re.sub('[^0-9]', '', id))
        # Removes the REAL, HUME, SMR prefixes. @TODO: Should probably rather remove these during import.
