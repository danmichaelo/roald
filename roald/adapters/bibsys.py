# encoding=utf-8
import isodate
import xmlwitch
import codecs
import os
import re
from lxml import etree
from ..models.resources import Concept, Collection, Label
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

    def load(self, filename, exclude_underemne=False):
        language = self.vocabulary.default_language.alpha2
        self.exclude_underemne = exclude_underemne
        resources = []
        ids = {}  # index lookup hash
        parents = {}
        if not os.path.isfile(filename):
            return {}

        # First pass
        for _, record in etree.iterparse(filename, tag='post'):
            resource = self.process_record(record, language, parents)
            if resource is not None:
                resources.append(resource)
                ids[resource['id']] = len(resources) - 1
            record.clear()

        # Second pass
        for _, record in etree.iterparse(filename, tag='post'):
            self.process_relations(record, resources, ids, language, parents)
            record.clear()

        self.vocabulary.resources.load(resources)

    def get_label(self, record):
        label = record.find('hovedemnefrase').text
        kv = record.find('kvalifikator')
        if kv is not None:
            label = u'{} ({})'.format(label, kv.text)
        if not self.exclude_underemne:
            for uf in record.findall('underemnefrase'):
                label = u'{} - {}'.format(label, uf.text)
        for node in record.findall('kjede'):
            label = u'{} : {}'.format(label, node.text)
        return label

    def process_record(self, record, language, parents):

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

        elif record.find('type') is not None and record.find('type').text == 'K':
            obj = Concept('KnuteTerm')

        else:
            obj = Concept(conceptType)

        obj.set('id', ident)

        for node in record.findall('signatur'):
            obj.add('notation', node.text)

        for node in record.findall('klass-signatur/signatur'):
            obj.add('notation', node.text)

        for node in record.findall('toppterm-id'):
            if node.text == ident:
                obj.set('isTopConcept', True)

        if not obj.get('isTopConcept') is True:
            for node in record.findall('overordnetterm-id') + record.findall('ox-id'):
                parents[ident] = parents.get(ident, []) + [node.text]

        prefLabel = self.get_label(record)
        obj.set('prefLabel.{}'.format(language), Label(prefLabel))
        if isinstance(record, Concept) and prefLabel.endswith('(Form)'):
            logging.info('Setting GenreForm')
            obj.set_type('GenreForm')
            prefLabel = prefLabel[:-7]

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

        return obj

    def get_parents(self, parents, resources, ids, tid):
        out = []
        # if parents.get(tid) is None:
        #     logger.warn('No parents for %s', tid)
        for parent_id in parents.get(tid, []):
            if parent_id not in ids:
                logger.warn('The parent ID %s of %s is not a Concept or a Collection', parent_id, tid)
            elif isinstance(resources[ids[parent_id]], Concept):
                out.append(resources[ids[parent_id]])
            else:
                x = self.get_parents(parents, resources, ids, parent_id)
                out.extend(x)
        return out

    def process_relations(self, record, resources, ids, language, parents):

        tid = record.find('term-id').text

        if record.find('gen-se-henvisning') is not None:
            return

        if record.find('se-id') is not None:
            se_id = record.find('se-id').text
            resources[ids[se_id]].add('altLabel.{}'.format(language), Label(self.get_label(record)))
            return

        resource = resources[ids[tid]]

        for node in record.findall('se-ogsa-id'):
            try:
                related = resources[ids[node.text]]
                if isinstance(related, Collection):
                    logger.warn(u'Cannot use a collection as related(?) Ignoring {} SA {}'.format(tid, node.text))
                else:
                    resource.add('related', related['id'])
            except KeyError:
                logger.warn('Cannot add relation %s SO %s because the latter doesn\'t exist as a concept (it might be a term though)', tid, node.text)


        # Add normal hierarchical relations
        if isinstance(resource, Concept) and not resource.get('isTopConcept') is True:
            for parent in self.get_parents(parents, resources, ids, tid):
                resource.add('broader', parent['id'])

        # Add facet relations
        for node in record.findall('overordnetterm-id') + record.findall('ox-id'):
            if node.text not in ids:
                logger.warn('Parent %s not a Concpet or Collection', node.text)
            else:
                broader = resources[ids[node.text]]
                if isinstance(broader, Collection):
                    broader.add('member', resource['id'])
                if isinstance(broader, Concept) and isinstance(resource, Collection):
                    resource.add('superOrdinate', broader['id'])

        # if isinstance(resource, Concept):
        #     parents_transitive = self.get_parents_transitive(parents, tid, [])
        #     if 'HUME06256' in parents_transitive:
        #         logging.info('Setting Geographic')
        #         resource.set_type('Geographic')
            # if 'HUME10852' in parents_transitive:
            #     logging.info('Setting Time')
            #     resource.set_type('Temporal')

    def get_parents_transitive(self, parents, tid, path):
        p = []
        if tid in path:
            logger.warn(u'Uh oh, trapped in a circle: %s', u' → '.join(path + [tid]))
            return p
        for parent in parents.get(tid, []):
            p.append(parent)
            p.extend(self.get_parents_transitive(parents, parent, path + [tid]))
        return p

