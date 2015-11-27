# encoding=utf-8
import codecs
import json
import os
from iso639 import languages

from .models import Roald2
from .models import Marc21
from .models import Skos
from .models import Concepts


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
        self.concepts = Concepts()
        self.default_language = None

    def load(self, filename, format='roald3', language=None):
        """
            - filename : the filename to a 'roald3' file or path to a 'roald2' directory.
            - format : 'roald3' or 'roald2'.
            - language : language code (only for 'roald2')
        """
        filename = os.path.expanduser(filename)
        if format == 'roald3':
            if language is not None:
                logger.warn('roald.load: Setting language has no effect when loading Roald3 data')
            data = json.load(codecs.open(filename, 'r', 'utf-8'))
            self.default_language = languages.get(alpha2=data['default_language'])
            self.concepts.load(data['concepts'])
            self.concepts.uri_format = data['uri_format']
        elif format == 'roald2':
            self.default_language = languages.get(alpha2=language)
            self.concepts.load(Roald2().read(filename, language=self.default_language.alpha2))
        else:
            raise ValueError('Unknown format')

    def set_uri_format(self, value):
        self.concepts.uri_format = value

    def save(self, filename):
        filename = os.path.expanduser(filename)
        if self.default_language is None:
            raise RuntimeError('roald.save: No default language code set.')
        data = {
            'default_language': self.default_language.alpha2,
            'uri_format': self.concepts.uri_format,
            'concepts': self.concepts.get()
        }
        json.dump(data, codecs.open(filename, 'w', 'utf-8'), indent=2)

    def export(self, filename, format, **kwargs):
        if format == 'marc21':
            model = Marc21(self.concepts, language=self.default_language, **kwargs)
        elif format == 'rdfskos':
            model = Skos(self.concepts, **kwargs)
        else:
            raise Exception('Unknown format')

        filename = os.path.expanduser(filename)
        with open(filename, 'w') as f:
            f.write(model.serialize())

    def authorize(self, value):
        # <value> can take a compound heading value like "$a Component1 $x Component2 $x Component3"
        return self.concepts.get(term=value)
        # parts = [[x.strip()[0], x.strip()[1:].strip()] for x in value.split('$') if len(x.strip()) > 0]
        # for part in parts:
