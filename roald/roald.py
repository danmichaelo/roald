# encoding=utf-8
import codecs
import json
import os
from iso639 import languages
import logging

from .adapters import Bibsys
from .adapters import Roald2
from .adapters import Roald3
from .adapters import Marc21
from .adapters import Skos
from .models import Vocabulary

logger = logging.getLogger(__name__)


class Roald(object):
    """
    Roald

    Example:

    >>> roald = roald.Roald()
    >>> roald.load('./data/', format='roald2', language='nb')
    >>> roald.set_uri_format('http://data.ub.uio.no/realfagstermer/c{id}')
    >>> roald.save('realfagstermer.json')
    >>> roald.export('realfagstermer.marc21.xml', format='marc21')
    """

    def __init__(self):
        super(Roald, self).__init__()
        self.vocabulary = Vocabulary()
        self.default_language = None

    def load(self, filename, format='roald3', language=None):
        """
            - filename : the filename to a 'roald3' file or path to a 'roald2' directory.
            - format : 'roald3', 'roald2' or 'bibsys'.
            - language : language code (only for 'roald2')
        """
        filename = os.path.expanduser(filename)
        if format == 'roald3':
            if language is not None:
                logger.warn('roald.load: Setting language has no effect when loading Roald3 data')
            Roald3(self.vocabulary).load(filename)
        elif format == 'roald2':
            self.vocabulary.default_language = languages.get(alpha2=language)
            Roald2(self.vocabulary).load(filename)
        elif format == 'bibsys':
            self.vocabulary.default_language = languages.get(alpha2=language)
            Bibsys(self.vocabulary).load(filename)
        else:
            raise ValueError('Unknown format')

        logger.info('Loaded {} resources'.format(len(self.vocabulary.resources)))

    def set_uri_format(self, value):
        self.vocabulary.uri_format = value

    def save(self, filename):
        filename = os.path.expanduser(filename)

        Roald3(self.vocabulary).save(filename)

        logger.info('Saved {} resources to {}'.format(len(self.vocabulary.resources), filename))

    def export(self, filename, format, **kwargs):
        if format == 'marc21':
            logger.info('Preparing MARC21 export')
            model = Marc21(self.vocabulary, **kwargs)
        elif format == 'rdfskos':
            logger.info('Preparing RDF/SKOS export')
            model = Skos(self.vocabulary, **kwargs)
        else:
            raise Exception('Unknown format')

        filename = os.path.expanduser(filename)
        with open(filename, 'wb') as f:
            f.write(model.serialize())
        logger.info('Export to {} complete'.format(filename))


    def authorize(self, value):
        # <value> can take a compound heading value like "$a Component1 $x Component2 $x Component3"
        return self.concepts.get(term=value)
        # parts = [[x.strip()[0], x.strip()[1:].strip()] for x in value.split('$') if len(x.strip()) > 0]
        # for part in parts:
