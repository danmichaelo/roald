


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

    def get(self, key, default=None):
        return self.data.get(key, default)
