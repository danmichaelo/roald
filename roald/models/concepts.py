# encoding=utf-8
import isodate
import json
import codecs
from rdflib.graph import Graph, Literal
from rdflib.namespace import Namespace, URIRef, OWL, RDF, DC, DCTERMS, FOAF, XSD, SKOS, RDFS


class Concepts(object):
    """
    Concepts class
    """

    def __init__(self, data={}, uri_format=None):
        """
            - data: dict
            - uri_format : the URI format string, example: 'http://data.me/{id}'
        """
        super(Concepts, self).__init__()
        self._ids = {}
        self._terms = {}
        self._uri_format = uri_format
        self.load(data)

    @property
    def uri_format(self):
        return self._uri_format

    @uri_format.setter
    def uri_format(self, value):
        self._uri_format = value

    def get(self, id=None, term=None):
        if id is not None:
            return self._data[id]
        if term is not None:
            return self._data[self._ids[term]]
        return self._data

    def load(self, data):
        """
            data: dict
        """

        self._data = data

        # Build lookup hashes:
        for k, v in data.items():
            if 'prefLabel' in v and 'nb' in v['prefLabel']:
                self._ids[v['prefLabel']['nb']['value']] = k
                self._terms[k] = v['prefLabel']['nb']['value']
        for k, v in data.items():
            if 'component' in v:
                s = ' : '.join([self._terms[x] for x in v['component']])
                self._ids[s] = k
                self._terms[k] = s

    def split_compound_heading(self, term):
        parts = [[x.strip()[0], x.strip()[1:].strip()] for x in value.split('$') if len(x.strip()) > 0]

    def uri(self, id):  # TODO: Move into a new Concept class?
        if self._uri_format is None:
            raise Exception('URI format has not been set.')
        return self._uri_format.format(id=id[4:])

    def __iter__(self):
        for c in self._data.values():
            yield c

    def __len__(self):
        return len(self._data)
