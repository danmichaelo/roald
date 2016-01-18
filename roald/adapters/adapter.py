from rdflib.graph import Graph, Literal
from rdflib.namespace import Namespace, URIRef, OWL, RDF, DC, DCTERMS, FOAF, XSD, SKOS, RDFS
from skosify import Skosify


class Adapter(object):

    def extFromFilename(self, fn):
        if fn.endswith('.ttl'):
            return 'turtle'
        return 'xml'

    def load_mappings(self, filename, graph=None):
        tmp = Graph()
        if graph is None:
            graph = Graph()
        tmp.load(filename, format=self.extFromFilename(filename))

        skosify = Skosify()
        skosify.enrich_relations(tmp,
                                 enrich_mappings=True,
                                 use_narrower=False,
                                 use_transitive=False)

        for tr in tmp.triples_choices((None, [SKOS.exactMatch, SKOS.closeMatch, SKOS.broadMatch, SKOS.narrowMatch, SKOS.relatedMatch], None)):
            #if tr[0] in all_concepts:
            graph.add(tr)

        return graph
