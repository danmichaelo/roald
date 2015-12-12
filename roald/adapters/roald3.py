import json
import codecs


class Roald3(object):

    def __init__(self, vocabulary):
        super(Roald3, self).__init__()
        self.vocabulary = vocabulary

    def load(self, filename):
        data = json.load(codecs.open(filename, 'r', 'utf-8'))

        if 'uri_format' in data:
            self.vocabulary.uri_format = data['uri_format']

        if 'default_language' in data:
            self.vocabulary.default_language = languages.get(alpha2=data['default_language'])

        if 'resources' in data:
            self.vocabulary.resources.load(data['resources'])

    def save(self, filename):

        if self.vocabulary.default_language is None:
            raise RuntimeError('vocabulary.save: No default language code set.')

        data = {
            'default_language': self.vocabulary.default_language.alpha2,
            'uri_format': self.vocabulary.uri_format,
            'resources': self.vocabulary.resources.get()
        }

        with codecs.open(filename, 'w', 'utf-8') as stream:
            json.dump(data, stream, indent=2)
