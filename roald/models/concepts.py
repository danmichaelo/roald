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

    def fromfile(self, filename):
        rt = json.load(codecs.open(filename, 'r', 'utf-8'))
        self.load(rt['concepts'])

    def tofile(self, filename):
        json.dump({'concepts': self._data},
                  codecs.open(filename, 'w', 'utf-8'),
                  indent=2)

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

    def by_id(self, id):
        return self._data[id]

    def by_term(self, term):
        return self._data[self._ids[term]]

    def split_compound_heading(self, term):
        parts = [[x.strip()[0], x.strip()[1:].strip()] for x in value.split('$') if len(x.strip()) > 0]

    def uri(self, id):  # TODO: Move into a new Concept class
        return 'http://data.ub.uio.no/realfagstermer/c{}'.format(id[4:])

    def __iter__(self):
        for c in self._data.values():
            yield c
