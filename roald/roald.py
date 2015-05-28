# encoding=utf-8
import codecs
import json

from .models import Roald2
from .models import Marc21
from .models import Skos


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
        self.concepts = []

    def load(self, filename):
        rt = json.load(codecs.open(filename, 'r', 'utf-8'))
        self.concepts = rt['concepts']

    def save(self, filename):
        json.dump({'concepts': self.concepts},
                  codecs.open(filename, 'w', 'utf-8'),
                  indent=2)

    def importRoald2(self, path='./'):
        rii = Roald2()
        self.concepts = rii.read(path)

    def exportMarc21(self, filename):
        m21 = Marc21()
        with open(filename, 'w') as f:
            f.write(m21.convert(self.concepts))

    def exportRdfSkos(self, filename):
        skos = Skos()
        with open(filename, 'w') as f:
            f.write(skos.convert(self.concepts))
