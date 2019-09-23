# encoding=utf-8
import isodate
import xmlwitch
import iso639
import copy
import json
import logging
from six import text_type
from rdflib import URIRef
from rdflib.graph import Graph, Literal
from rdflib.namespace import SKOS
import re

from .adapter import Adapter

logger = logging.getLogger(__name__)


class Marc21(Adapter):
    """
    MARC21 exporter

    URIs are included if `uri_format` is set on the Vocabulary.
    """

    vocabulary = None
    created_by = None  # Cataloguing agency 040 $a
    transcribed_by = None  # Transcribing agency 040 $c
    modified_by = None  # Modifying agency 040 $d
    vocabulary_code = None  # Vocabulary code, 040 $f
    language = None  # Default language code for 040 $b
    include_extras = False  # Whether to include $9 language and $9 rank codes

    def __init__(self, vocabulary, created_by=None, vocabulary_code=None, language=None, include_extras=False, include_memberships=False):
        super(Marc21, self).__init__()
        self.vocabulary = vocabulary
        self.created_by = created_by
        self.vocabulary_code = vocabulary_code
        self.language = language or self.vocabulary.default_language
        self.include_extras = include_extras
        self.include_memberships = include_memberships

    def serialize(self):

        if self.language is None:
            raise RuntimeError('MARC21 serialization needs language.')

        if type(self.language) != iso639.iso639._Language:
            raise RuntimeError('MARC21 language must be an instance of iso639.iso639._Language.')

        # Make a dictionary of 'narrower' (reverse 'broader') for fast lookup
        self.narrower = {}
        for c in self.vocabulary.resources:
            for x in c.get('broader', []):
                self.narrower[x] = self.narrower.get(x, []) + [c['id']]
            if self.include_memberships and not c.get('deprecated'):
                for x in c.get('memberOf', []):
                    self.narrower[x] = self.narrower.get(x, []) + [c['id']]

        # Make a dictionary of 'replaces' (inverse 'replacedBy') for fast lookup
        self.replaces = {}
        for c in self.vocabulary.resources:
            for x in c.get('replacedBy', []):
                self.replaces[x] = self.replaces.get(x, []) + [c['id']]

        builder = xmlwitch.Builder(version='1.0', encoding='utf-8')

        self.nmappings = 0
        with builder.collection(xmlns='info:lc/xmlns/marcxchange-v1'):
            for resource in self.vocabulary.resources:
                self.convert_resource(builder, resource, self.vocabulary.resources)

        logger.info(' - Included %d DDC mappings', self.nmappings)

        s = text_type(builder)
        return s.encode('utf-8')

    def global_cn(self, value, include_prefix=True):
        if value.startswith('http://data.ub.uio.no/entity/'):
            return 'REAL%s' % value[30:]
        if include_prefix is False or self.created_by is None:
            return value
        else:
            return '({}){}'.format(self.created_by, value)

    def add_acronyms(self, builder, term, resourceType):

        if term.hasAcronym:
            tag = {
                'Temporal': '448',
                'Topic': '450',
                'Geographic': '451',
                'GenreForm': '455',
            }[resourceType]
            with builder.datafield(tag=tag, ind1=' ', ind2=' '):
                builder.subfield(term.hasAcronym, code='a')

                # Heading in the tracing field is an acronym for the heading in the 1XX field.
                # Ref: http://www.loc.gov/marc/authority/adtracing.html
                builder.subfield('d', code='g')

        if term.acronymFor:
            tag = {
                'Temporal': '448',
                'Topic': '450',
                'Geographic': '451',
                'GenreForm': '455',
            }[resourceType]
            with builder.datafield(tag=tag, ind1=' ', ind2=' '):
                builder.subfield(term.acronymFor, code='a')

                # No special indication possible?
                # https://github.com/realfagstermer/roald/issues/8

    def tag_from_type(self, base, res_type):
        vals = {
            'Temporal': 48,
            'Topic': 50,
            'Geographic': 51,
            'GenreForm': 55,
            'LinkingTerm': 50,  # Knutetermer
            'SplitNonPreferredTerm': 50,  # Generell se-henvisning
            'Collection': 50, # Fasettindikatorer
            'Category': 50,   # i realfagstermer
        }
        return '{:d}'.format(base + vals[res_type])

    def convert_resource(self, builder, resource, resources):

        created = None
        modified = None

        if resource.get('created'):
            created = isodate.parse_datetime(resource.get('created'))

        if resource.get('deprecated'):
            modified = isodate.parse_datetime(resource.get('deprecated'))
        elif resource.get('modified'):
            modified = isodate.parse_datetime(resource.get('modified'))

        if created is None and modified is None:
            # Mrtermer har ingen datoer(!)
            created = isodate.isodatetime.datetime(2010, 1, 1)
            modified = isodate.isodatetime.datetime(2010, 1, 1)
            # or… isodate.isodatetime.datetime.now()
        elif created is None:
            created = modified

        elif modified is None:
            modified = created


        if self.vocabulary.uri_format is not None:
            uri = self.vocabulary.uri(resource.get('id'))
        else:
            uri = None
        ddc_matcher = re.compile(r'http://dewey.info/class/(([1-9])--)?([0-9.]+)')
        vocab_matcher = re.compile(r'http://data.ub.uio.no/([a-z]+)/c([0-9]+)')
        mappingRelationsRepr = {
            'exactMatch': '=EQ',
            'closeMatch': '~EQ',
            'relatedMatch': 'RM',
            'broadMatch': 'BM',
            'narrowMatch': 'NM'
        }

        # Loop over resource types
        for resourceType in resource.get('type'):

            if resourceType == 'VirtualCompoundHeading':
                continue

            if resourceType == 'Category' and not self.include_memberships:
                continue

            with builder.record(xmlns='http://www.loc.gov/MARC21/slim', type='Authority'):

                # Fixed leader for all records
                # Ref: <http://www.loc.gov/marc/uma/pt8-11.html#pt8>
                record_status = 'n'

                x = resource.get('replacedBy', [])
                if len(x) > 1:
                    record_status = 's'  # replaced by more than one concept
                elif len(x) == 1:
                    record_status = 'x'  # replaced by one concept
                elif resource.get('deprecated') is not None:
                    record_status = 'd'  # deleted

                leader = '00000{}z  a2200000n  4500'.format(record_status)
                builder.leader(leader)

                # 001 Control number
                builder.controlfield(self.global_cn(resource.get('id'), False), tag='001')

                # 003 MARC code for the agency whose system control number is contained in field 001 (Control Number).
                if self.created_by is not None:
                    builder.controlfield(self.created_by, tag='003')

                # 005 Date of creation
                builder.controlfield(modified.strftime('%Y%m%d%H%M%S.0'), tag='005')

                # 008 General Information / Informasjonskoder
                f09 = 'a'  # Kind of record: Established heading
                f14 = 'b'  # Heading use-main or added entry (1XX or 7XX fields): Not appropriate
                f15 = 'a'  # Heading use-subject added entry (6XX fields): Appropriate

                if resourceType == 'LinkingTerm':
                    f15 = 'b'  # Not appropriate

                if resourceType == 'SplitNonPreferredTerm':
                    f15 = 'b'  # Not appropriate

                # Fasetter
                if resourceType == 'Collection':
                    f09 = 'e'  # Node label
                    f15 = 'b'  # Not appropriate

                field008 = '{created}|||{f09}nz|n{f14}{f15}bn          |a|ana|||| d'.format(
                    created=created.strftime('%y%m%d'),
                    f09=f09,
                    f14=f14,
                    f15=f15
                )

                builder.controlfield(field008, tag='008')

                # 024 Other Standard Identifier
                if uri is not None:
                    with builder.datafield(tag='024', ind1='7', ind2=' '):
                        builder.subfield(uri, code='a')
                        builder.subfield('uri', code='2')

                # 035 System control number ?
                # Her kan vi legge inn ID-er fra andre systemer, f.eks. BARE?
                # For eksempel, se XML-dataene fra WebDewey

                # 040 Cataloging source
                with builder.datafield(tag='040', ind1=' ', ind2=' '):
                    if self.created_by is not None:
                        builder.subfield(self.created_by, code='a')     # Original cataloging agency
                    if self.language is not None:
                        builder.subfield(self.language.bibliographic, code='b')      # Language of cataloging
                    if self.transcribed_by is not None:
                        builder.subfield(self.transcribed_by, code='c')     # Transcribing agency
                    if self.modified_by is not None:
                        builder.subfield(self.modified_by, code='d')     # Modifying agency
                    if self.vocabulary_code is not None:
                        builder.subfield(self.vocabulary_code, code='f')  # Subject heading/thesaurus

                # 065 Other Classification Number
                for value in resource.get('msc', []):
                    with builder.datafield(tag='065', ind1=' ', ind2=' '):
                        builder.subfield(value, code='a')
                        builder.subfield('msc', code='2')

                # 083 DDC number
                #
                # We exclude these from the MARC21 export at the moment since
                # we don't want thse numbers to end up in WebDewey until they have
                # been reviewed by the mapping project team
                #
                # for value in resource.get('ddc', []):
                #     with builder.datafield(tag='083', ind1='0', ind2=' '):
                #         builder.subfield(value, code='a')

                # 083 DDC number
                for value in resource.get('notation', []):
                    with builder.datafield(tag='083', ind1='0', ind2=' '):
                        builder.subfield(value, code='a')

                cmappings = []
                omappings = []
                umappings = []
                for mapping_type, target_uris in resource.get('mappings', {}).items():
                    for target_uri in target_uris:
                        m = ddc_matcher.match(target_uri)
                        m2 = vocab_matcher.match(target_uri)
                        if m:
                            ma = {'number': m.group(3), 'relation': mappingRelationsRepr.get(mapping_type)}
                            if ma['relation'] is not None:
                                self.nmappings += 1
                                if m.group(2) is not None:
                                    ma['table'] = m.group(2)
                                else:
                                    ma['table'] = ''
                                cmappings.append(ma)
                        elif m2:
                            vocab = {'humord': 'humord', 'realfagstermer': 'noubomn', 'tekord': 'tekord'}.get(m2.group(1))
                            if vocab and mappingRelationsRepr.get(mapping_type):
                                cid = {'humord': '(No-TrBIB)HUME', 'tekord': '(No-TrBIB)NTUB', 'realfagstermer': '(NoOU)REAL'}.get(m2.group(1)) + m2.group(2)
                                omappings.append({'vocab': vocab, 'id': cid, 'relation': mappingRelationsRepr[mapping_type]})
                        else:
                            umappings.append({'uri': text_type(target_uri), 'relation': mappingRelationsRepr[mapping_type]})

                for ma in sorted(cmappings, key=lambda k: '{},{},{}'.format(k['relation'], k['table'], k['number'])):
                    with builder.datafield(tag='083', ind1='0', ind2=' '):
                        if ma['table'] != '':
                            builder.subfield(ma['table'], code='z')
                        builder.subfield(ma['number'], code='a')
                        builder.subfield(ma['relation'], code='c')
                        builder.subfield('23', code='2')

                out_terms = []
                def add_term(out_term):
                    tag=out_term.pop(0)  # ignore tag when comparing as we can have the same term in 1xx and 4xx
                    out_term_s = json.dumps(out_term)
                    if out_term_s in out_terms:
                        return
                    out_terms.append(out_term_s)
                    with builder.datafield(tag=tag, ind1=' ', ind2=' '):
                        for sf in out_term:
                            builder.subfield(sf[1], code=sf[0])

                # 148/150/151/155 Authorized heading
                if resourceType == 'CompoundHeading':

                    # Get first component to get a list of languages
                    first_component = resources.get(id=resource.get('component')[0])

                    for lang, term in first_component.prefLabel.items():

                        # Determine tag number based on the first component:
                        if lang == self.language.alpha2:
                            tag = self.tag_from_type(100, first_component.type[0])
                        else:
                            tag = self.tag_from_type(400, first_component.type[0])

                        # Ignore this language if not *all* components have labels in it
                        vals = [resources.get(id=value).prefLabel.get(lang) is None for value in resource.get('component')]
                        if True in vals:
                            continue

                        sf_a = first_component.prefLabel[lang]

                        out_term = [
                            tag,
                            ['a', sf_a.value],
                        ]

                        for value in resource.get('component')[1:]:
                            component = resources.get(id=value)

                            # Determine subfield code from type:
                            sf = {
                                'Topic': 'x',
                                'Temporal': 'y',
                                'Geographic': 'z',
                                'GenreForm': 'v',
                            }[component['type'][0]]

                            # OBS! 150 har også $b.. Men når brukes egentlig den??
                            sf_term = component.prefLabel[lang]
                            out_term.append([sf, sf_term.value])

                            if self.include_extras:
                                out_term.append(['9', 'rank=preferred'])
                                out_term.append(['9', 'language=' + lang])

                        add_term(out_term)


                else:  # Not a compound heading
                    for lang, term in resource.prefLabel.items():

                        if lang == self.language.alpha2:
                            tag = self.tag_from_type(100, resourceType)
                        else:
                            tag = self.tag_from_type(400, resourceType)

                        out_term = [
                            tag,
                            ['a', term.value],
                        ]
                        if self.include_extras:
                            out_term.append(['9', 'rank=preferred'])
                            out_term.append(['9', 'language=' + lang])
                        add_term(out_term)

                        # Atm. acronyms only for primary language
                        # if lang == self.language.alpha2:
                        #     self.add_acronyms(builder, term, resourceType)

                    # Add 448/450/451/455 See from tracings
                    for lang, terms in resource.get('altLabel', {}).items():
                        tag = self.tag_from_type(400, resourceType)
                        for term in terms:
                            out_term = [
                                tag,
                                # Always use subfield $a. Correct???
                                ['a', term.value],
                            ]
                            term_value = term.value

                            if self.include_extras:
                                out_term.append(['9', 'rank=alternative'])
                                out_term.append(['9', 'language=' + lang])
                            add_term(out_term)

                            # Atm. acronyms only for primary language
                            # if lang == self.language.alpha2:
                            #    self.add_acronyms(builder, term, resourceType)

                # 548/550/551/555 See also
                tags = {
                    'Temporal': '548',
                    'Topic': '550',
                    'Geographic': '551',
                    'GenreForm': '555',
                    'LinkingTerm': '550',  # @TODO: ???
                    'SplitNonPreferredTerm': '550',  # @TODO: ???
                    'Category': '550',
                }
                if not resource.get('deprecated'):
                    # Only include relations for non-deprecated concepts

                    broader = copy.copy(resource.get('broader', []))
                    if self.include_memberships:
                        broader += resource.get('memberOf', [])

                    for value in broader:
                        rel = resources.get(id=value)
                        rel_type = rel['type'][0]
                        if rel_type in tags:
                            with builder.datafield(tag=tags[rel_type], ind1=' ', ind2=' '):
                                builder.subfield(rel.prefLabel[self.language.alpha2].value, code='a')
                                builder.subfield('g', code='w')  # Ref: http://www.loc.gov/marc/authority/adtracing.html
                                builder.subfield(self.global_cn(value), code='0')
                        else:
                            logger.warn('Cannot serialize "%s" <broader> "%s", because the latter has a unknown type.', value, rel['id'])

                    for value in self.narrower.get(resource['id'], []):
                        rel = resources.get(id=value)
                        rel_type = rel['type'][0]
                        with builder.datafield(tag=tags[rel_type], ind1=' ', ind2=' '):
                            builder.subfield(rel.prefLabel[self.language.alpha2].value, code='a')
                            builder.subfield('h', code='w')  # Ref: http://www.loc.gov/marc/authority/adtracing.html
                            builder.subfield(self.global_cn(value), code='0')

                    for value in resource.get('related', []):
                        rel = resources.get(id=value)
                        tag = self.tag_from_type(500, rel['type'][0])
                        # Note: rel['type'][0] can be 'KnuteTerm'! How to handle?
                        with builder.datafield(tag=tag, ind1=' ', ind2=' '):
                            builder.subfield(rel.prefLabel[self.language.alpha2].value, code='a')
                            builder.subfield(self.global_cn(value), code='0')

                # 680 Notes
                for value in resource.get('editorialNote', []):
                    with builder.datafield(tag='680', ind1=' ', ind2=' '):
                        builder.subfield(value, code='i')

                # 680 Notes (Definition)
                for lang, value in resource.get('definition', {}).items():
                    with builder.datafield(tag='680', ind1=' ', ind2=' '):
                        builder.subfield(value, code='i')

                # 7XX Heading Linking Entries-General Information
                for ma in sorted(omappings, key=lambda k: '{},{}'.format(k['vocab'], k['id'])):
                    # @TODO: Does choice of 748/750/751/755 depend on source or target concept?
                    with builder.datafield(tag='750', ind1=' ', ind2='7'):
                        # builder.subfield('???', code='a')
                        builder.subfield(ma['id'], code='0')
                        builder.subfield(ma['vocab'], code='2')
                        builder.subfield(ma['relation'], code='4')
                for ma in sorted(umappings, key=lambda k: k['uri']):
                    with builder.datafield(tag='750', ind1=' ', ind2='4'):
                        builder.subfield(ma['uri'], code='0')
                        builder.subfield(ma['relation'], code='4')
