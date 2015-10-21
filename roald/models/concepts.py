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

    def __init__(self, data={}, indexLanguage='nb'):
        """
            - data: dict
            - indexLanguage : the primary language
        """
        super(Concepts, self).__init__()
        self.indexLanguage = indexLanguage
        self._ids = {}
        self._terms = {}
        self.load(data)

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
                self._ids[v['prefLabel']['nb']] = k
                self._terms[k] = v['prefLabel']['nb']
        for k, v in data.items():
            if 'component' in v:
                s = ' : '.join([self._terms[x] for x in v['component']])
                self._ids[s] = k
                self._terms[k] = s

    def split_compound_heading(self, term):
        parts = [[x.strip()[0], x.strip()[1:].strip()] for x in value.split('$') if len(x.strip()) > 0]

    def uri(self, id):  # TODO: Move into a new Concept class
        return 'http://data.ub.uio.no/realfagstermer/c{}'.format(id[4:])

    def __iter__(self):
        for c in self._data.values():
            yield c
