# encoding=utf-8
import isodate
from rdflib.graph import Graph, Literal
from rdflib.namespace import Namespace, URIRef, OWL, RDF, DC, DCTERMS, FOAF, XSD, SKOS, RDFS
from rdflib.collection import Collection
from rdflib import BNode
from otsrdflib import OrderedTurtleSerializer
from six import binary_type
from datetime import datetime
import logging

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

logger = logging.getLogger(__name__)

MADS = Namespace('http://www.loc.gov/mads/rdf/v1#')
SD = Namespace('http://www.w3.org/ns/sparql-service-description#')
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

    def __init__(self, concepts=None, include=None, mappings_from=None):
        """
            - concepts : Concepts object or list of concepts
            - include : List of files to include
            - mappings_from : List of files to only include mapping relations from
        """
        super(Skos, self).__init__()
        if concepts is not None:
            self.load(concepts)
        if include is None:
            self.include = []
        else:
            self.include = include
        if mappings_from is None:
            self.mappings_from = []
        else:
            self.mappings_from = mappings_from


    # Todo: Move into superclass
    def load(self, data):
        if type(data) == dict:
            self.concepts = Concepts(data)
        elif type(data) == Concepts:
            self.concepts = data
        else:
            raise ValueError

    def extFromFilename(self, fn):
        if fn.endswith('.ttl'):
            return 'turtle'
        return 'xml'

    def serialize(self):

        logger.info('Building RDF graph')

        graph = Graph()

        for inc in self.include:
            lg0 = len(graph)
            graph.load(inc, format=self.extFromFilename(inc))
            logger.info(' - Included {} triples from {}'.format(len(graph) - lg0, inc))

        for inc in self.mappings_from:
            lg0 = len(graph)
            tmp = Graph()
            tmp.load(inc, format=self.extFromFilename(inc))
            for tr in tmp.triples_choices((None, [SKOS.exactMatch, SKOS.closeMatch, SKOS.broadMatch, SKOS.narrowMatch, SKOS.relatedMatch], None)):
                graph.add(tr)
            logger.info(' - Included {} mappings from {}'.format(len(graph) - lg0, inc))

        try:
            scheme_uri = next(graph.triples((None, RDF.type, SKOS.ConceptScheme)))
        except StopIteration:
            raise Exception('Concept scheme URI could not be found in vocabulary scheme data')
        scheme_uri = scheme_uri[0]

        now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        graph.set((URIRef(scheme_uri), DCTERMS.modified, Literal(now, datatype=XSD.dateTime)))

        lg0 = len(graph)
        for concept in self.concepts:
            self.convert_concept(graph, concept, self.concepts, scheme_uri)
        logger.info(' - Added {} triples'.format(len(graph) - lg0))

        logger.info('Serializing RDF graph')
        serializer = OrderedTurtleSerializer(graph)

        # These will appear first in the file and be ordered by URI
        serializer.topClasses = [SKOS.ConceptScheme,
                                 FOAF.Organization,
                                 SD.Service,
                                 SD.Dataset,
                                 SD.Graph,
                                 SD.NamedGraph,
                                 SKOS.Concept]

        stream = BytesIO()
        serializer.serialize(stream)
        return stream.getvalue()

    def convert_types(self, types):
        out = []
        for x in types:
            for y in self.typemap.get(x, []):
                out.append(y)
        return out

    def convert_concept(self, graph, concept, concepts, scheme_uri):
        uri = URIRef(concepts.uri(concept['id']))

        types = self.convert_types(concept.get('type', []))
        if len(types) == 0:
            # Unknown type, log it?
            return
        for value in types:
            graph.add((uri, RDF.type, value))

        graph.add((uri, SKOS.inScheme, scheme_uri))

        for lang, term in concept.get('prefLabel', {}).items():
            graph.add((uri, SKOS.prefLabel, Literal(term['value'], lang=lang)))

            if term.get('hasAcronym'):
                # @TODO Temporary while thinking...
                # graph.add((uri, LOCAL.acronym, Literal(term['hasAcronym'], lang=lang)))
                graph.add((uri, SKOS.altLabel, Literal(term['hasAcronym'], lang=lang)))

        for lang, terms in concept.get('altLabel', {}).items():
            for term in terms:
                graph.add((uri, SKOS.altLabel, Literal(term['value'], lang=lang)))

                if term.get('hasAcronym'):
                    # @TODO Temporary while thinking...
                    # graph.add((uri, LOCAL.acronym, Literal(term['hasAcronym'], lang=lang)))
                    graph.add((uri, SKOS.altLabel, Literal(term['hasAcronym'], lang=lang)))

        for lang, value in concept.get('definition', {}).items():
            graph.add((uri, SKOS.definition, Literal(value, lang=lang)))

        for lang, value in concept.get('scopeNote', {}).items():
            # @TODO For backwards compability
            graph.add((uri, SKOS.editorialNote, Literal(value, lang=lang)))

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

        for x in concept.get('ddc', []):
            graph.add((uri, DCTERMS.DDC, Literal(x)))

        related = [concepts.get(id=value) for value in concept.get('related', [])]
        for c in related:
            rel_uri = URIRef(concepts.uri(c['id']))

            graph.add((uri, SKOS.related, rel_uri))

        broader = [concepts.get(id=value) for value in concept.get('broader', [])]
        for c in broader:
            rel_uri = URIRef(concepts.uri(c['id']))

            graph.add((uri, SKOS.broader, rel_uri))
            graph.add((rel_uri, SKOS.narrower, uri))

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
            graph.add((uri, SKOS.broader, component))
            graph.add((component, SKOS.narrower, uri))

            for component in component_uris:
                b2 = BNode()
                graph.add((b1, RDF.rest, b2))
                graph.add((b2, RDF.first, component))
                b1 = b2

            graph.add((b1, RDF.rest, RDF.nil))
            # graph.add((uri, SKOS.broader, component))


