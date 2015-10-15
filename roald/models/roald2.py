# encoding=utf-8
import isodate
import xmlwitch
import codecs


class Concept(object):
    """docstring for Concept"""

    def __init__(self, conceptType):
        super(Concept, self).__init__()
        self.data = {
            'prefLabel': {}
        }
        self.set_type(conceptType)
        self.blank = True

    def set_type(self, conceptType):

        if conceptType not in ['Topic', 'Geographic', 'Temporal', 'GenreForm', 'CompoundHeading', 'VirtualCompoundHeading']:
            raise ValueError('Invalid concept type')

        conceptTypes = [conceptType]

        # Genre/form can also be used as topic:
        # if conceptType == 'GenreForm':
        #    conceptTypes.append('Topic')

        self.data['type'] = conceptTypes

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
                    raise StandardError('Uh oh, {} defined two times for the same concept! Dump: {}'.format(origkey, json.dumps(self.__dict__)))
                data[k] = value
            data = data[k]

    def get(self, key):
        return self.data[key]


class Roald2(object):
    """
    Class for importing legacy data from Roald 2
    """

    def __init__(self):
        super(Roald2, self).__init__()

    def read(self, path='./'):

        files = {
            'idtermer.txt': 'Topic',
            'idformer.txt': 'GenreForm',
            'idtider.txt': 'Temporal',
            'idsteder.txt': 'Geographic',
            'idstrenger.txt': 'CompoundHeading',
        }

        concepts = []
        for f, t in files.items():
            concepts += self.read_file(path + f, t)

        return {c.get('id'): c.data for c in concepts}

    def read_file(self, filename, conceptType):
        concepts = []
        f = codecs.open(filename, 'r', 'utf-8')
        for concept in self.read_concept(f.read(), conceptType):
            if not concept.blank:
                concepts.append(concept)
        f.close()
        return concepts

    def read_concept(self, data, conceptType):
        concept = Concept(conceptType)
        for line in data.split('\n'):
            line = line.strip().split('= ')
            if len(line) == 1:
                if not concept.blank:
                    yield concept
                concept = Concept(conceptType)
            else:
                key, value = line
                if key == 'id':
                    # uri = 'http://data.ub.uio.no/realfagstermer/{}'.format(value)
                    # concept.set('uri', uri)
                    concept.set('id', value)
                elif key == 'te':
                    concept.set('prefLabel.nb', value)
                elif key == 'bf':
                    concept.add('altLabel.nb', value)
                elif key in ['en', 'nn', 'la']:
                    if key not in concept.get('prefLabel'):
                        concept.set('prefLabel.{key}'.format(key=key), value)
                    else:
                        concept.add('altLabel.{key}'.format(key=key), value)

                elif key == 'ak':
                    concept.add('acronym', value)

                elif key == 'ms':
                    concept.add('msc', value)
                elif key == 'dw':
                    concept.add('ddc', value)

                elif key == 'so':
                    # uri = 'http://data.ub.uio.no/realfagstermer/{}'.format(value)
                    concept.add('related', value)
                elif key == 'ot':
                    # uri = 'http://data.ub.uio.no/realfagstermer/{}'.format(value)
                    concept.add('broader', value)
                elif key == 'ut':
                    pass
                    # concept.add('narrower', value)
                elif key == 'de':
                    concept.add('definition', value)
                elif key == 'no':
                    concept.add('scopeNote', value)
                elif key == 'tio':
                    concept.set('created', value)
                elif key == 'tie':
                    concept.set('modified', value)
                elif key == 'ba':
                    pass  # ignore, ignore for now

                elif key == 'st':
                    pass
                    # concept.add('streng', value)
                elif key in ['da', 'db', 'dx', 'dy', 'dz']:
                    # uri = 'http://data.ub.uio.no/realfagstermer/{}'.format(value)
                    concept.add('component', value)
                    if key in ['dx', 'dy', 'dz']:
                        concept.set_type('VirtualCompoundHeading')

                else:
                    print 'Unknown key: {}'.format(key)
        if not concept.blank:
            yield concept
