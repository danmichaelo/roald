# encoding=utf-8
import isodate
import xmlwitch
import codecs
import os
import re
from lxml import etree
from ..models.resources import Concept, Collection
import logging

logger = logging.getLogger(__name__)


class Bibsys(object):
    """
    Class for importing legacy data from Bibsys
    """

    encoding = 'latin1'
    vocabulary = None

    def __init__(self, vocabulary):
        super(Bibsys, self).__init__()
        self.vocabulary = vocabulary

    def load(self, filename):
        language = self.vocabulary.default_language.alpha2
        resources = {}
        parents = {}
        if not os.path.isfile(filename):
            return {}

        # First pass
        for _, record in etree.iterparse(filename, tag='post'):
            self.process_record(record, resources, language, parents)
            record.clear()

        # Second pass
        for _, record in etree.iterparse(filename, tag='post'):
            self.process_relations(record, resources, language, parents)
            record.clear()

        resources = {k: v.data for k, v in resources.items()}
        self.vocabulary.resources.load(resources)

    def get_label(self, record):
        label = record.find('hovedemnefrase').text
        kv = record.find('kvalifikator')
        if kv is not None:
            label = u'{} ({})'.format(label, kv.text)
        return label

    def process_record(self, record, resources, language, parents):

        conceptType = 'Topic'   # TODO: Perhaps 'GenreForm' if string contains ' (Form)' qualifier?

        if record.find('se-id') is not None:  # We'll handle those in the second pass
            return

        if record.find('gen-se-henvisning') is not None:
            # @TODO: Need to figure out how to handle.
            logger.warn(u'Ignoring gen-se-henvisning')
            return

        ident = record.find('term-id').text

        if record.find('type') is not None and record.find('type').text == 'F':
            obj = Collection()
            resources[ident] = obj

        elif record.find('type') is not None and record.find('type').text == 'K':
            obj = Concept('KnuteTerm')
            resources[ident] = obj

        else:
            obj = Concept(conceptType)
            resources[ident] = obj

        obj.set('id', ident)

        for node in record.findall('toppterm-id'):
            if node.text == ident:
                obj.set('isTopConcept', True)

        if not obj.get('isTopConcept') is True:
            for node in record.findall('overordnetterm-id') + record.findall('ox-id'):
                parents[ident] = parents.get(ident, []) + [node.text]

        obj.set('prefLabel.{}.value'.format(language), self.get_label(record))

        dato = record.find('dato').text
        obj.set('modified', '{}T00:00:00Z'.format(dato))

        for node in record.findall('definisjon'):
            obj.set('definition.{}'.format(language), node.text)

        for node in record.findall('gen-se-ogsa-henvisning'):
            obj.add('scopeNote.{}'.format(language), u'Se også: {}'.format(node.text))

        for node in record.findall('noter'):
            # Ihvertfall i Humord virker disse temmelig interne... Mulig noen kan flyttes til scopeNote
            obj.add('editorialNote', node.text)

        for node in record.findall('lukket-bemerkning'):
            obj.add('editorialNote', u'Lukket bemerkning: {}'.format(node.text))

    def get_parents(self, parents, resources, tid):
        out = []
        if parents.get(tid) is None:
            logger.warn('No parents for %s', tid)
        for parent_id in parents.get(tid, []):
            if isinstance(resources[parent_id], Concept):
                out.append(resources[parent_id])
            else:
                x = self.get_parents(parents, resources, parent_id)
                out.extend(x)
        return out

    def process_relations(self, record, resources, language, parents):

        tid = record.find('term-id').text

        if record.find('gen-se-henvisning') is not None:
            return

        if record.find('se-id') is not None:
            se_id = record.find('se-id').text
            resources[se_id].add('altLabel.{}'.format(language), {'value': self.get_label(record)})
            return

        resource = resources[tid]

        for node in record.findall('se-ogsa-id'):
            related = resources[node.text]
            if isinstance(related, Collection):
                logger.warn(u'Cannot use a collection as related(?) Ignoring {} SA {}'.format(tid, node.text))
            else:
                resource.add('related', related['id'])

        # Add normal hierarchical relations
        if isinstance(resource, Concept) and not resource.get('isTopConcept') is True:
            for parent in self.get_parents(parents, resources, tid):
                resource.add('broader', parent['id'])

        # Add facet relations
        for node in record.findall('overordnetterm-id') + record.findall('ox-id'):
            broader = resources[node.text]
            if isinstance(broader, Collection):
                broader.add('member', resource['id'])
            if isinstance(broader, Concept) and isinstance(resource, Collection):
                resource.add('superOrdinate', broader['id'])
