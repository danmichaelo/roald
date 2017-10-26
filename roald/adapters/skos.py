# encoding=utf-8
import isodate

from rdflib.graph import Graph, Literal
from rdflib.namespace import Namespace, URIRef, OWL, RDF, DC, DCTERMS, FOAF, XSD, SKOS, RDFS
from rdflib.collection import Collection
from otsrdflib import OrderedTurtleSerializer
from six import binary_type
from datetime import datetime
import logging

from .adapter import Adapter
from ..models.resources import Concept
from ..models.resources import Label

try:
    from skosify import Skosify
except:
    raise RuntimeError('Please install skosify first')

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
UOC = Namespace('http://trans.biblionaut.net/class#')


class Skos(Adapter):
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

    def __init__(self, vocabulary, include=None, mappings_from=None, add_same_as=None):
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
        if add_same_as is None:
            self.add_same_as = []
        else:
            self.add_same_as = add_same_as

    def load(self, filename):
        """
        Note: This loader only loads categories and mappings
        """
        graph = Graph()
        graph.load(filename, format=self.extFromFilename(filename))
        skosify = Skosify()
        skosify.enrich_relations(graph,
                                 enrich_mappings=True,
                                 use_narrower=False,
                                 use_transitive=False)

        # Load mappings
        for tr in graph.triples_choices((None, [SKOS.exactMatch, SKOS.closeMatch, SKOS.broadMatch, SKOS.narrowMatch, SKOS.relatedMatch], None)):
            source_concept = tr[0]
            res_id = self.vocabulary.id_from_uri(source_concept)
            if res_id is not None:
                shortName = str(tr[1]).split('#')[1]
                try:
                    self.vocabulary.resources[res_id].add('mappings.%s' % shortName, str(tr[2]))
                except KeyError:
                    logger.warning('Concept not found: %s', res_id)

        # Load categories
        for tr in graph.triples((None, RDF.type, UOC.Category)):
            cat_lab = graph.preferredLabel(tr[0], lang='nb')[0][1].value
            cat_id = self.vocabulary.id_prefix + tr[0].split('/')[-1]

            cat = Concept().set_type('Category')
            cat.set('id', cat_id)
            cat.set('prefLabel.nb', Label(cat_lab))
            self.vocabulary.resources.load([cat])


            for tr2 in graph.triples((tr[0], SKOS.member, None)):
                uri = str(tr2[2])
                res_id = self.vocabulary.id_from_uri(uri)
                if res_id is not None:
                    try:
                        self.vocabulary.resources[res_id].add('memberOf', cat_id)
                    except KeyError:
                        logger.warning('Concept not found: %s', res_id)

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
            self.convert_resource(graph, resource, self.vocabulary.resources, scheme_uri, self.vocabulary.default_language.alpha2, self.add_same_as)
        logger.info(' - Added {} triples'.format(len(graph) - lg0))

        all_concepts = set([tr[0] for tr in graph.triples((None, RDF.type, SKOS.Concept))])
        skosify = Skosify()
        for inc in self.mappings_from:
            lg0 = len(graph)
            mappings = self.load_mappings(inc)
            for tr in mappings.triples((None, None, None)):
                if tr[0] in all_concepts:
                    graph.add(tr)
            logger.info(' - Added {} mappings from {}'.format(len(graph) - lg0, inc))

        logger.info('Skosify...')
        self.skosify_process(graph)

        logger.info('Serializing RDF graph')
        serializer = OrderedTurtleSerializer(graph)

        # These will appear first in the file and be ordered by URI
        serializer.topClasses = [SKOS.ConceptScheme,
                                 FOAF.Organization,
                                 SD.Service,
                                 SD.Dataset,
                                 SD.Graph,
                                 SD.NamedGraph,
                                 OWL.Ontology,
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

    def convert_resource(self, graph, resource, resources, scheme_uri, default_language, add_same_as):
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
            graph.add((uri, SKOS.prefLabel, Literal(term.value, lang=lang)))

            if term.hasAcronym:
                # @TODO Temporary while thinking...
                # graph.add((uri, LOCAL.acronym, Literal(term['hasAcronym'], lang=lang)))
                graph.add((uri, SKOS.altLabel, Literal(term.hasAcronym, lang=lang)))

        for lang, terms in resource.get('altLabel', {}).items():
            for term in terms:
                graph.add((uri, SKOS.altLabel, Literal(term.value, lang=lang)))

                if term.hasAcronym:
                    # @TODO Temporary while thinking...
                    # graph.add((uri, LOCAL.acronym, Literal(term['hasAcronym'], lang=lang)))
                    graph.add((uri, SKOS.altLabel, Literal(term.hasAcronym, lang=lang)))

        for lang, value in resource.get('definition', {}).items():
            graph.add((uri, SKOS.definition, Literal(value, lang=lang)))

        for lang, values in resource.get('scopeNote', {}).items():
            for value in values:
                graph.add((uri, SKOS.scopeNote, Literal(value, lang=lang)))

        for value in resource.get('editorialNote', []):
            graph.add((uri, SKOS.editorialNote, Literal(value, lang=default_language)))

        for value in resource.get('acronym', []):
            graph.add((uri, LOCAL.acronym, Literal(value)))

        for value in resource.get('notation', []):
            graph.add((uri, SKOS.notation, Literal(value)))

        x = resource.get('created')
        if x is not None:
            graph.add((uri, DCTERMS.created, Literal(x, datatype=XSD.dateTime)))

        x = resource.get('deprecated')
        if x is not None:
            graph.add((uri, OWL.deprecated, Literal(True)))
            graph.add((uri, SKOS.historyNote, Literal('Deprecated on {}'.format(x))))
            graph.add((uri, DCTERMS.modified, Literal(x, datatype=XSD.dateTime)))
        else:
            x = resource.get('modified', resource.get('created'))
            if x is not None:
                graph.add((uri, DCTERMS.modified, Literal(x, datatype=XSD.dateTime)))

        x = resource.get('elementSymbol')
        if x is not None:
            graph.add((uri, LOCAL.elementSymbol, Literal(x)))

        for x in resource.get('libCode', []):
            graph.add((uri, LOCAL.libCode, Literal(x)))

        x = resource.get('id')
        if x is not None:
            graph.add((uri, DCTERMS.identifier, Literal(x)))

        for x in resource.get('ddc', []):
            graph.add((uri, DCTERMS.DDC, Literal(x)))

        related = [resources.get(id=value) for value in resource.get('related', [])]
        for c in related:
            rel_uri = URIRef(self.vocabulary.uri(c['id']))

            graph.add((uri, SKOS.related, rel_uri))

        replacedBy = [resources.get(id=value) for value in resource.get('replacedBy', [])]
        for c in replacedBy:
            rel_uri = URIRef(self.vocabulary.uri(c['id']))
            graph.add((uri, DCTERMS.isReplacedBy, rel_uri))

        for res_id in resource.get('memberOf', []):
            graph.add((URIRef(self.vocabulary.uri(res_id)), SKOS.member, uri))

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

        for mapping_type, target_uris in resource.get('mappings', {}).items():
            for target_uri in target_uris:
                graph.add((uri, SKOS[mapping_type], URIRef(target_uri)))

        components = [resources.get(id=value) for value in resource.get('component', [])]
        if len(components) != 0:

            # @TODO: Generalize
            fallback_lang = 'nb'
            for lang in ['nb', 'nn', 'en']:
                labels = [component['prefLabel'].get(lang, component['prefLabel'].get(fallback_lang)) for component in components]
                labels = [component.value for component in labels if component]
                # labels = [c.prefLabel[lang].value for c in components if c['prefLabel'].get(lang, fallback_lang)]
                if len(labels) == len(components):
                    streng = resources.string_separator.join(labels)
                    graph.add((uri, SKOS.prefLabel, Literal(streng, lang=lang)))

            component_uris = [URIRef(self.vocabulary.uri(c['id'])) for c in components]

            for component_uri in component_uris:
                graph.add((uri, LOCAL.component, component_uri))
                graph.add((uri, SKOS.broader, component_uri))
                if self.options['include_narrower']:
                    graph.add((component_uri, SKOS.narrower, uri))
                    graph.add((component_uri, LOCAL.compound, uri))

        for same_as in add_same_as:
            graph.add((uri, OWL.sameAs, URIRef(same_as.format(id=resource['id']))))

    def skosify_process(self, graph):

        # logging.info("Performing inferences")

        skosify = Skosify()

        # Perform RDFS subclass inference.
        # Mark all resources with a subclass type with the upper class.
        # skosify.infer_classes(graph)
        # skosify.infer_properties(graph)

        # logging.info("Setting up namespaces")
        # skosify.setup_namespaces(graph, namespaces)

        # logging.info("Phase 4: Transforming concepts, literals and relations")

        # special transforms for labels: whitespace, prefLabel vs altLabel
        # skosify.transform_labels(graph, options.default_language)

        # special transforms for collections + aggregate and deprecated concepts
        # skosify.transform_collections(graph)

        # find concept schema and update date modified
        # cs = skosify.get_concept_scheme(graph)
        # skosify.initialize_concept_scheme(graph, cs,
        #                                   label=False,
        #                                   language='nb',
        #                                   set_modified=True)

        # skosify.transform_aggregate_concepts(graph, cs, relationmap, options.aggregates)
        # skosify.transform_deprecated_concepts(graph, cs)

        # logging.info("Phase 5: Performing SKOS enrichments")

        # Enrichments: broader <-> narrower, related <-> related
        # skosify.enrich_relations(graph,
        #                          enrich_mappings=True,
        #                          use_narrower=False,
        #                          transitive=False)

        # logging.info("Phase 6: Cleaning up")

        # Clean up unused/unnecessary class/property definitions and unreachable
        # triples
        # if options.cleanup_properties:
        #     skosify.cleanup_properties(graph)
        # if options.cleanup_classes:
        #     skosify.cleanup_classes(graph)
        # if options.cleanup_unreachable:
        #     skosify.cleanup_unreachable(graph)

        # logging.info("Phase 7: Setting up concept schemes and top concepts")

        # setup inScheme and hasTopConcept
        # skosify.setup_concept_scheme(graph, cs)
        # skosify.setup_top_concepts(graph, options.mark_top_concepts)

        # logging.info("Phase 8: Checking concept hierarchy")

        # check hierarchy for cycles
        skosify.check_hierarchy(graph, break_cycles=True, keep_related=False,
                                mark_top_concepts=False, eliminate_redundancy=True)

        # logging.info("Phase 9: Checking labels")

        # check for duplicate labels
        # skosify.check_labels(graph, options.preflabel_policy)
