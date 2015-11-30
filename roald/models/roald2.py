# encoding=utf-8
import isodate
import xmlwitch
import codecs
import os
import re


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


class Roald2(object):
    """
    Class for importing legacy data from Roald 2
    """

    elementSymbols = ['Ag', 'Al', 'Am', 'Ar', 'As', 'At', 'Au', 'B', 'Ba', 'Be', 'Bh', 'Bi', 'Bk', 'Br', 'C', 'Ca', 'Cd', 'Ce', 'Cf', 'Cl', 'Cm', 'Cn', 'Co', 'Cr', 'Cs', 'Cu', 'Db', 'Ds', 'Dy', 'Er', 'Es', 'Eu', 'F', 'Fe', 'Fl', 'Fm', 'Fr', 'Ga', 'Gd', 'Ge', 'H', 'He', 'Hf', 'Hg', 'Ho', 'Hs', 'I', 'In', 'Ir', 'K', 'Kr', 'La', 'Li', 'Lr', 'Lu', 'Lv', 'Md', 'Mg', 'Mn', 'Mo', 'Mt', 'N', 'Na', 'Nb', 'Nd', 'Ne', 'Ni', 'No', 'Np', 'O', 'Os', 'P', 'Pa', 'Pb', 'Pd', 'Pm', 'Po', 'Pr', 'Pt', 'Pu', 'Ra', 'Rb', 'Re', 'Rf', 'Rg', 'Rh', 'Rn', 'Ru', 'S', 'Sb', 'Sc', 'Se', 'Sg', 'Si', 'Sm', 'Sn', 'Sr', 'Ta', 'Tb', 'Tc', 'Te', 'Th', 'Ti', 'Tl', 'Tm', 'U', 'Uuo', 'Uup', 'Uus', 'Uut', 'V', 'W', 'Xe', 'Y', 'Yb', 'Zn', 'Zr']

    def __init__(self):
        super(Roald2, self).__init__()

    def read(self, path='./', language='en'):

        files = {
            'idtermer.txt': 'Topic',
            'idformer.txt': 'GenreForm',
            'idtider.txt': 'Temporal',
            'idsteder.txt': 'Geographic',
            'idstrenger.txt': 'CompoundHeading',
        }

        concepts = []
        for f, t in files.items():
            concepts += self.read_file(path + f, t, language)

        if len(concepts) == 0:
            raise RuntimeError('Found no concepts in {}'.format(path))

        return {c.get('id'): c.data for c in concepts}

    def read_file(self, filename, conceptType, language):
        concepts = []
        if not os.path.isfile(filename):
            return []
        f = codecs.open(filename, 'r', 'utf-8')
        for concept in self.read_concept(f.read(), conceptType, language):
            if not concept.blank:
                concepts.append(concept)
        f.close()
        return concepts


    def add_acronyms(self, concept, acronyms, language):
        for value in acronyms:
            pvalue = re.sub('-', '', value)
            if value in self.elementSymbols:
                concept.set('elementSymbol', value)
            else:
                print 'Check:', value
                acronym_for = []
                for lang, term in concept.get('prefLabel').items():
                    words = re.split('[ -]+', term['value'])
                    x = 0
                    for n in range(len(words)):
                        # print n, words[n], value[x]
                        if words[n][0].lower() == pvalue[x].lower():
                            # print ' <> Found'
                            x += 1
                            if x >= len(pvalue):
                                print ' : matched prefLabel', term['value']
                                acronym_for.append(term)
                                break
                for lang, terms in concept.get('altLabel', {}).items():
                    for term in terms:
                        words = re.split('[ -]+', term['value'])
                        x = 0
                        for n in range(len(words)):
                            # print n, words[n], value[x]
                            if words[n][0].lower() == pvalue[x].lower():
                                # print ' <> Found'
                                x += 1
                                if x >= len(pvalue):
                                    print ' : matched altLabel', term['value']
                                    acronym_for.append(term)
                                    break
                if len(acronym_for) == 0:
                    prefLabels = [term for lang, term in concept.get('prefLabel').items()]
                    if len(prefLabels) == 1:
                        acronym_for.append(prefLabels[0])
                for term in acronym_for:
                    term['hasAcronym'] = value
                if len(acronym_for) == 0:
                    concept.add('altLabel.{key}'.format(key=language), {'value': value, 'acronymFor': '?'})
        return concept


    def read_concept(self, data, conceptType, language):
        concept = Concept(conceptType)
        acronyms = []
        lines = data.split('\n')

        # First pass
        for line in lines:
            line = line.strip().split('= ')
            if len(line) == 1:
                if not concept.blank:
                    yield self.add_acronyms(concept, acronyms, language)
                acronyms = []
                concept = Concept(conceptType)
            else:
                key, value = line
                if key == 'id':
                    # uri = 'http://data.ub.uio.no/realfagstermer/{}'.format(value)
                    # concept.set('uri', uri)
                    concept.set('id', value)
                elif key == 'te':
                    concept.set('prefLabel.{}'.format(language), {'value': value})
                elif key == 'bf':
                    concept.add('altLabel.{}'.format(language), {'value': value})
                elif key in ['en', 'nb', 'nn', 'la']:
                    if key not in concept.get('prefLabel'):
                        concept.set('prefLabel.{key}'.format(key=key), {'value': value})
                    else:
                        concept.add('altLabel.{key}'.format(key=key), {'value': value})

                elif key == 'ak':
                    acronyms.append(value)

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
                    concept.set('definition.{}'.format(language), value)
                elif key == 'no':
                    concept.set('scopeNote.{}'.format(language), value)
                elif key == 'tio':
                    concept.set('created', value)
                elif key == 'tie':
                    concept.set('modified', value)
                elif key == 'ba':
                    pass  # ignore, ignore for now

                elif key == 'st':
                    pass
                    # concept.add('streng', value)
                elif key in ['da', 'db', 'dz', 'dy', 'dx']:
                    # uri = 'http://data.ub.uio.no/realfagstermer/{}'.format(value)
                    concept.add('component', value)
                    if key in ['dx', 'dy', 'dz']:
                        concept.set_type('VirtualCompoundHeading')

                else:
                    print 'Unknown key: {}'.format(key)

        if not concept.blank:
            yield self.add_acronyms(concept, acronyms, language)
