# encoding=utf-8
import isodate
from rdflib.graph import Graph, Literal
from rdflib.namespace import Namespace, URIRef, OWL, RDF, DC, DCTERMS, FOAF, XSD, SKOS, RDFS
from rdflib.collection import Collection
from rdflib import BNode
from otsrdflib import OrderedTurtleSerializer

from roald.models.concepts import Concepts

try:
    from io import BytesIO
    assert BytesIO
except ImportError:
    try:
        from cStringIO import StringIO as BytesIO
        assert BytesIO
    except ImportError:
        from StringIO import StringIO as BytesIO
        assert BytesIO

MADS = Namespace('http://www.loc.gov/mads/rdf/v1#')
LOCAL = Namespace('http://data.ub.uio.no/onto#')


class Skos(object):
    """
    Class for exporting data as SKOS
    """

    typemap = {
        'Topic': [SKOS.Concept, MADS.Topic],
        'Geographic': [SKOS.Concept, MADS.Geographic],
        'GenreForm': [SKOS.Concept, MADS.GenreForm],
        'Temporal': [SKOS.Concept, MADS.Temporal],
        'CompoundHeading': [SKOS.Concept, MADS.ComplexSubject],
        'VirtualCompoundHeading': [SKOS.Concept, MADS.ComplexSubject],
    }

    def __init__(self, concepts=None, scheme=None):
        """
            - concepts : Concepts object or list of concepts
            - scheme : Turtle file with initial vocabulary configuration
        """
        super(Skos, self).__init__()
        if concepts is not None:
            self.load(concepts)
        self.scheme = scheme


    # Todo: Move into superclass
    def load(self, data):
        if type(data) == dict:
            self.concepts = Concepts(data)
        elif type(data) == Concepts:
            self.concepts = data
        else:
            raise ValueError


    def serialize(self):
        graph = Graph()
        print 'Building graph'

        if self.scheme is not None:
            print '(Including {})'.format(self.scheme)
            graph.load(self.scheme, format='turtle')

        for concept in self.concepts:
            self.convert_concept(graph, concept, self.concepts)

        print 'Serializing'
        stream = BytesIO()
        serializer = OrderedTurtleSerializer(graph)
        serializer.serialize(stream)
        return stream.getvalue()

    def convert_types(self, types):
        out = []
        for x in types:
            for y in self.typemap.get(x, []):
                out.append(y)
        return out

    def convert_concept(self, graph, concept, concepts):
        uri = URIRef(concepts.uri(concept['id']))

        types = self.convert_types(concept.get('type', []))
        if len(types) == 0:
            # Unknown type, log it?
            return
        for value in types:
            graph.add((uri, RDF.type, value))

        for lang, term in concept.get('prefLabel', {}).items():
            graph.add((uri, SKOS.prefLabel, Literal(term['value'], lang=lang)))

            if term.get('hasAcronym'):
                graph.add((uri, LOCAL.acronym, Literal(term['hasAcronym'], lang=lang)))

        for lang, terms in concept.get('altLabel', {}).items():
            for term in terms:
                graph.add((uri, SKOS.altLabel, Literal(term['value'], lang=lang)))

                if term.get('hasAcronym'):
                    graph.add((uri, LOCAL.acronym, Literal(term['hasAcronym'], lang=lang)))

        for lang, value in concept.get('definition', {}).items():
            graph.add((uri, SKOS.definition, Literal(value, lang=lang)))

        for lang, value in concept.get('scopeNote', {}).items():
            graph.add((uri, SKOS.scopeNote, Literal(value, lang=lang)))

        for value in concept.get('acronym', []):
            graph.add((uri, LOCAL.acronym, Literal(value)))

        x = concept.get('created')
        if x is not None:
            graph.add((uri, DCTERMS.created, Literal(x, datatype=XSD.dateTime)))

        x = concept.get('modified', concept.get('created'))
        if x is not None:
            graph.add((uri, DCTERMS.modified, Literal(x, datatype=XSD.dateTime)))

        x = concept.get('elementSymbol')
        if x is not None:
            graph.add((uri, LOCAL.elementSymbol, Literal(x)))

        x = concept.get('id')
        if x is not None:
            graph.add((uri, DCTERMS.identifier, Literal(x)))

        related = [concepts.get(id=value) for value in concept.get('related', [])]
        for c in related:
            rel_uri = URIRef(concepts.uri(c['id']))

            graph.add((uri, SKOS.related, rel_uri))

        components = [concepts.get(id=value) for value in concept.get('component', [])]
        if len(components) != 0:

            for lang in ['nb']:
                labels = [c['prefLabel'][lang]['value'] for c in components if c['prefLabel'].get(lang)]
                if len(labels) == len(components):
                    streng = ' : '.join(labels)
                    graph.add((uri, SKOS.prefLabel, Literal(streng, lang=lang)))

            component_uris = [URIRef(concepts.uri(c['id'])) for c in components]

            component = component_uris.pop(0)
            b1 = BNode()
            graph.add((uri, MADS.componentList, b1))
            graph.add((b1, RDF.first, component))

            for component in component_uris:
                b2 = BNode()
                graph.add((b1, RDF.rest, b2))
                graph.add((b2, RDF.first, component))
                b1 = b2

            graph.add((b1, RDF.rest, RDF.nil))


