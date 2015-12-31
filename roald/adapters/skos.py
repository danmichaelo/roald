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

ISOTHES = Namespace('http://purl.org/iso25964/skos-thes#')
MADS = Namespace('http://www.loc.gov/mads/rdf/v1#')
SD = Namespace('http://www.w3.org/ns/sparql-service-description#')
LOCAL = Namespace('http://data.ub.uio.no/onto#')


class Skos(object):
    """
    Class for exporting data as SKOS
    """

    typemap = {
        'Group': [SKOS.Collection, ISOTHES.ConceptGroup],
        'Collection': [SKOS.Collection, ISOTHES.ThesaurusArray],
        'Topic': [SKOS.Concept, LOCAL.Topic],
        'Geographic': [SKOS.Concept, LOCAL.Place],
        'GenreForm': [SKOS.Concept, LOCAL.GenreForm],
        'Temporal': [SKOS.Concept, LOCAL.Time],
        'CompoundHeading': [SKOS.Concept, LOCAL.CompoundConcept],
        'VirtualCompoundHeading': [SKOS.Concept, LOCAL.VirtualCompoundConcept],
        'KnuteTerm': [SKOS.Concept, LOCAL.KnuteTerm],
    }

    options = {
        'include_narrower': False
    }

    def __init__(self, vocabulary, include=None, mappings_from=None):
        """
            - vocabulary : Vocabulary object
            - include : List of files to include
            - mappings_from : List of files to only include mapping relations from
        """
        super(Skos, self).__init__()
        self.vocabulary = vocabulary
        if include is None:
            self.include = []
        else:
            self.include = include
        if mappings_from is None:
            self.mappings_from = []
        else:
            self.mappings_from = mappings_from

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

        try:
            scheme_uri = next(graph.triples((None, RDF.type, SKOS.ConceptScheme)))
        except StopIteration:
            raise Exception('Concept scheme URI could not be found in vocabulary scheme data')
        scheme_uri = scheme_uri[0]

        now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        graph.set((URIRef(scheme_uri), DCTERMS.modified, Literal(now, datatype=XSD.dateTime)))

        lg0 = len(graph)
        for resource in self.vocabulary.resources:
            self.convert_resource(graph, resource, self.vocabulary.resources, scheme_uri, self.vocabulary.default_language.alpha2)
        logger.info(' - Added {} triples'.format(len(graph) - lg0))

        all_concepts = set([tr[0] for tr in graph.triples((None, RDF.type, SKOS.Concept))])
        for inc in self.mappings_from:
            lg0 = len(graph)
            tmp = Graph()
            tmp.load(inc, format=self.extFromFilename(inc))
            for tr in tmp.triples_choices((None, [SKOS.exactMatch, SKOS.closeMatch, SKOS.broadMatch, SKOS.narrowMatch, SKOS.relatedMatch], None)):
                if tr[0] in all_concepts:
                    graph.add(tr)
            logger.info(' - Added {} mappings from {}'.format(len(graph) - lg0, inc))

        logger.info('Serializing RDF graph')
        serializer = OrderedTurtleSerializer(graph)

        # These will appear first in the file and be ordered by URI
        serializer.topClasses = [SKOS.ConceptScheme,
                                 FOAF.Organization,
                                 SD.Service,
                                 SD.Dataset,
                                 SD.Graph,
                                 SD.NamedGraph,
                                 OWL.Class,
                                 OWL.DatatypeProperty,
                                 SKOS.Collection,
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

    def convert_resource(self, graph, resource, resources, scheme_uri, default_language):
        uri = URIRef(self.vocabulary.uri(resource['id']))

        types = self.convert_types(resource.get('type', []))
        if len(types) == 0:
            # Unknown type, log it?
            return
        for value in types:
            graph.add((uri, RDF.type, value))

        if resource.get('isTopConcept'):
            graph.add((uri, SKOS.topConceptOf, scheme_uri))
        else:
            graph.add((uri, SKOS.inScheme, scheme_uri))

        for lang, term in resource.get('prefLabel', {}).items():
            graph.add((uri, SKOS.prefLabel, Literal(term['value'], lang=lang)))

            if term.get('hasAcronym'):
                # @TODO Temporary while thinking...
                # graph.add((uri, LOCAL.acronym, Literal(term['hasAcronym'], lang=lang)))
                graph.add((uri, SKOS.altLabel, Literal(term['hasAcronym'], lang=lang)))

        for lang, terms in resource.get('altLabel', {}).items():
            for term in terms:
                graph.add((uri, SKOS.altLabel, Literal(term['value'], lang=lang)))

                if term.get('hasAcronym'):
                    # @TODO Temporary while thinking...
                    # graph.add((uri, LOCAL.acronym, Literal(term['hasAcronym'], lang=lang)))
                    graph.add((uri, SKOS.altLabel, Literal(term['hasAcronym'], lang=lang)))

        for lang, value in resource.get('definition', {}).items():
            graph.add((uri, SKOS.definition, Literal(value, lang=lang)))

        for lang, values in resource.get('scopeNote', {}).items():
            for value in values:
                graph.add((uri, SKOS.scopeNote, Literal(value, lang=lang)))

        for value in resource.get('editorialNote', []):
            graph.add((uri, SKOS.editorialNote, Literal(value, lang=default_language)))

        for value in resource.get('acronym', []):
            graph.add((uri, LOCAL.acronym, Literal(value)))

        x = resource.get('created')
        if x is not None:
            graph.add((uri, DCTERMS.created, Literal(x, datatype=XSD.dateTime)))

        x = resource.get('modified', resource.get('created'))
        if x is not None:
            graph.add((uri, DCTERMS.modified, Literal(x, datatype=XSD.dateTime)))

        x = resource.get('elementSymbol')
        if x is not None:
            graph.add((uri, LOCAL.elementSymbol, Literal(x)))

        x = resource.get('id')
        if x is not None:
            graph.add((uri, DCTERMS.identifier, Literal(x)))

        for x in resource.get('ddc', []):
            graph.add((uri, DCTERMS.DDC, Literal(x)))

        related = [resources.get(id=value) for value in resource.get('related', [])]
        for c in related:
            rel_uri = URIRef(self.vocabulary.uri(c['id']))

            graph.add((uri, SKOS.related, rel_uri))

        for res_id in resource.get('member', []):
            graph.add((uri, SKOS.member, URIRef(self.vocabulary.uri(res_id))))

        for res_id in resource.get('superOrdinate', []):
            uri2 = URIRef(self.vocabulary.uri(res_id))
            graph.add((uri, ISOTHES.superOrdinate, uri2))
            graph.add((uri2, ISOTHES.subordinateArray, uri))

        broader = [resources.get(id=value) for value in resource.get('broader', [])]
        for c in broader:
            rel_uri = URIRef(self.vocabulary.uri(c['id']))

            graph.add((uri, SKOS.broader, rel_uri))
            if self.options['include_narrower']:
                graph.add((rel_uri, SKOS.narrower, uri))

        components = [resources.get(id=value) for value in resource.get('component', [])]
        if len(components) != 0:

            # @TODO: Generalize
            for lang in ['nb']:
                labels = [c['prefLabel'][lang]['value'] for c in components if c['prefLabel'].get(lang)]
                if len(labels) == len(components):
                    streng = resources.string_separator.join(labels)
                    graph.add((uri, SKOS.prefLabel, Literal(streng, lang=lang)))

            component_uris = [URIRef(self.vocabulary.uri(c['id'])) for c in components]

            component = component_uris.pop(0)
            b1 = BNode()
            graph.add((uri, MADS.componentList, b1))
            graph.add((b1, RDF.first, component))
            graph.add((uri, SKOS.broader, component))
            if self.options['include_narrower']:
                graph.add((component, SKOS.narrower, uri))

            for component in component_uris:
                b2 = BNode()
                graph.add((b1, RDF.rest, b2))
                graph.add((b2, RDF.first, component))
                b1 = b2

            graph.add((b1, RDF.rest, RDF.nil))
            # graph.add((uri, SKOS.broader, component))


