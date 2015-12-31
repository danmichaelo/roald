# encoding=utf-8
import isodate
import json
import codecs


class Resource(object):

    def __init__(self):
        super(Resource, self).__init__()
        self.data = {
            'prefLabel': {}
        }
        self.blank = True

    def add(self, key, value):
        self.blank = False
        key = key.split('.')
        data = self.data
        while len(key) != 0:
            k = key.pop(0)
            if k not in data:
                data[k] = [] if len(key) == 0 else {}
            if len(key) == 0:
                data[k].append(value)
            data = data[k]

    def set(self, key, value):
        self.blank = False
        if key == 'type':
            self.set_type(value)
            return
        origkey = key
        key = key.split('.')
        data = self.data
        while len(key) != 0:
            k = key.pop(0)
            if k not in data:
                data[k] = {}
            if len(key) == 0:
                if data[k] != {}:
                    raise StandardError('Uh oh, {} defined two times for the same resource! Dump: {}'.format(origkey, json.dumps(self.__dict__)))
                data[k] = value
            data = data[k]

    def get(self, key, default=None):
        return self.data.get(key, default)

    def __getitem__(self, key):
        return self.data[key]


class Group(Resource):

    def __init__(self):
        super(Group, self).__init__()
        self.data['type'] = 'Group'


class Collection(Resource):

    def __init__(self):
        super(Collection, self).__init__()
        self.data['type'] = ['Collection']


class Concept(Resource):
    """docstring for Concept"""

    def __init__(self, conceptType):
        super(Concept, self).__init__()
        self.set_type(conceptType)
        self.blank = True

    def set_type(self, conceptType):

        if conceptType not in ['Topic', 'Geographic', 'Temporal', 'GenreForm', 'CompoundHeading', 'VirtualCompoundHeading', 'KnuteTerm']:
            raise ValueError('Invalid concept type')

        conceptTypes = [conceptType]

        # Genre/form can also be used as topic:
        # if conceptType == 'GenreForm':
        #    conceptTypes.append('Topic')

        self.data['type'] = conceptTypes


class Resources(object):
    """
    Resources class
    """

    string_separator = ' : '

    def __init__(self, data={}, uri_format=None):
        """
            - data: dict
            - uri_format : the URI format string, example: 'http://data.me/{id}'
        """
        super(Resources, self).__init__()
        self._ids = {}
        self._terms = {}
        self._uri_format = uri_format
        self.load(data)

    @property
    def uri_format(self):
        return self._uri_format

    @uri_format.setter
    def uri_format(self, value):
        self._uri_format = value

    def get(self, id=None, term=None):
        if id is not None:
            return self._data[id]
        if term is not None:
            return self._data[self._ids[term]]
        return self._data

    def load(self, data):
        """
            data: dict
        """

        self._data = data

        default_language = 'nb'  # @TODO

        # Build lookup hashes:
        for k, v in data.items():
            if 'prefLabel' in v and default_language in v['prefLabel']:
                self._ids[v['prefLabel'][default_language]['value']] = k
                self._terms[k] = v['prefLabel'][default_language]['value']
            elif 'component' in v:
                term = self.string_separator.join(map(lambda x: data[x]['prefLabel'][default_language]['value'], v['component']))
                self._ids[term] = k
                self._terms[k] = term

    def uri(self, id):  # TODO: Move into Resource class
        if self._uri_format is None:
            raise Exception('URI format has not been set.')
        return self._uri_format.format(id=id[4:])

    def __iter__(self):
        for c in self._data.values():
            yield c

    def __len__(self):
        return len(self._data)


class Concepts(Resources):
    """
    Concepts class
    """

    def __init__(self, data={}):
        """
            - data: dict
        """
        super(Concepts, self).__init__()

    def split_compound_heading(self, term):
        parts = [[x.strip()[0], x.strip()[1:].strip()] for x in value.split('$') if len(x.strip()) > 0]
