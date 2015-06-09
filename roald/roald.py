# encoding=utf-8
import codecs
import json

from .models import Roald2
from .models import Marc21
from .models import Skos
from .models import Concepts


class Roald(object):
    """
    Roald

    Example:

    >>> roald = roald.Roald()
    >>> roald.importRoald2()
    >>> roald.save('realfagstermer.json')
    >>> roald.exportMarc21('realfagstermer.marc21.xml')
    """

    def __init__(self):
        super(Roald, self).__init__()
        self.concepts = Concepts()

    def load(self, filename):
        self.concepts.fromfile(filename)

    def save(self, filename):
        self.concepts.tofile(filename)

    def importRoald2(self, path='./'):
        self.concepts.load(Roald2().read(path))

    def exportMarc21(self, filename):
        m21 = Marc21()
        with open(filename, 'w') as f:
            f.write(m21.convert(self.concepts))

    def exportRdfSkos(self, filename):
        skos = Skos()
        with open(filename, 'w') as f:
            f.write(skos.convert(self.concepts))

    def authorize(self, value):
        # <value> can take a compound heading value like "$a Component1 $x Component2 $x Component3"
        return self.concepts.by_term(value)
        # parts = [[x.strip()[0], x.strip()[1:].strip()] for x in value.split('$') if len(x.strip()) > 0]
        # for part in parts:
