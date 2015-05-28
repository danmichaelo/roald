# encoding=utf-8
import isodate
from rdflib.graph import Graph, Literal
from rdflib.namespace import Namespace, URIRef, OWL, RDF, DC, DCTERMS, FOAF, XSD, SKOS, RDFS


class Skos(object):
    """
    Class for exporting data as SKOS
    """

    def __init__(self):
        super(Skos, self).__init__()

    def convert(self, concepts):
        pass
        # TODO
