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

    def __init__(self, indexLanguage='nb'):
        super(Concepts, self).__init__()
        self.concepts = {}
        self.indexLanguage = indexLanguage
        self._ids = {}
        self._terms = {}

    def fromfile(self, filename):
        rt = json.load(codecs.open(filename, 'r', 'utf-8'))
        self.load(rt['concepts'])

    def tofile(self, filename):
        json.dump({'concepts': self.concepts},
                  codecs.open(filename, 'w', 'utf-8'),
                  indent=2)

    def load(self, concepts):
        self.concepts = concepts

        # Build lookup hashes:
        for k, v in concepts.items():
            if 'prefLabel' in v and 'nb' in v['prefLabel']:
                self._ids[v['prefLabel']['nb']] = k
                self._terms[k] = v['prefLabel']['nb']
        for k, v in concepts.items():
            if 'component' in v:
                s = ' : '.join([self._terms[x] for x in v['component']])
                self._ids[s] = k
                self._terms[k] = s

    def by_id(self, id):
        return self.concepts[id]

    def by_term(self, term):
        return self.concepts[self._ids[term]]

    def split_compound_heading(self, term):
        parts = [[x.strip()[0], x.strip()[1:].strip()] for x in value.split('$') if len(x.strip()) > 0]
