# encoding=utf-8
import isodate
import xmlwitch
import iso639
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
    Class for exporting data as MARC21
    """

    vocabulary = None
    created_by = None  # Cataloguing agency 040 $a
    transcribed_by = None  # Transcribing agency 040 $c
    modified_by = None  # Modifying agency 040 $d
    vocabulary_code = None  # Vocabulary code, 040 $f
    language = None  # Default language code for 040 $b

    def __init__(self, vocabulary, created_by=None, vocabulary_code=None, language=None, mappings_from=None):
        super(Marc21, self).__init__()
        self.vocabulary = vocabulary
        self.created_by = created_by
        self.vocabulary_code = vocabulary_code
        self.language = language or self.vocabulary.default_language
        if mappings_from is None:
            self.mappings_from = []
        else:
            self.mappings_from = mappings_from

    def serialize(self):

        if self.language is None:
            raise RuntimeError('MARC21 serialization needs language.')

        if type(self.language) != iso639.iso639._Language:
            raise RuntimeError('MARC21 language must be an instance of iso639.iso639._Language.')

        # Load mappings
        mappings = Graph()
        for inc in self.mappings_from:
            self.load_mappings(inc, mappings)
            #logger.info(' - Loaded {} (two-way) mappings from {}'.format(len(mappings), inc))

        # Make a dictionary of 'narrower' (reverse 'broader') for fast lookup
        self.narrower = {}
        for c in self.vocabulary.resources:
            for x in c.get('broader', []):
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
                self.convert_resource(builder, resource, self.vocabulary.resources, mappings)

        logger.info(' - Included %d DDC mappings', self.nmappings)

        s = text_type(builder)
        return s.encode('utf-8')

    def global_cn(self, value):
        if self.created_by is None:
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
            'KnuteTerm': 50  # ... or..?
        }
        return '{:d}'.format(base + vals[res_type])

    def convert_resource(self, builder, resource, resources, mappings):

        created = None
        modified = None

        if resource.get('created'):
            created = isodate.parse_datetime(resource.get('created'))

        if resource.get('modified'):
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

        uri = self.vocabulary.uri(resource.get('id'))
        ddc_matcher = re.compile(r'http://data.ub.uio.no/ddc/(T([1-9])--)?([0-9.]+)')
        mappingRelationsRepr = {
            SKOS.exactMatch: '=EQ',
            SKOS.closeMatch: '~EQ',
            SKOS.relatedMatch: 'RM',
            SKOS.broadMatch: 'BM',
            SKOS.narrowMatch: 'NM'
        }

        # Loop over resource types
        for resourceType in resource.get('type'):

            if resourceType == 'VirtualCompoundHeading':
                continue

            # if resourceType == 'KnuteTerm':
            #     # @TODO: Not sure how to handle these
            #     continue

            if resourceType == 'Collection':
                # @TODO: Not sure how to handle these
                continue

            with builder.record(xmlns='http://www.loc.gov/MARC21/slim', type='Authority'):

                # Fixed leader for all records
                # Ref: <http://www.loc.gov/marc/uma/pt8-11.html#pt8>
                record_status = 'n'

                x = resource.get('replacedBy', [])
                if len(x) > 1:
                    record_status = 's'
                elif len(x) == 1:
                    record_status = 'x'
                elif resource.get('deprecated') is not None:
                    record_status = 'd'

                leader = '00000{}z  a2200000n  4500'.format(record_status)
                builder.leader(leader)

                # 001 Control number
                builder.controlfield(resource.get('id'), tag='001')

                # 003 MARC code for the agency whose system control number is contained in field 001 (Control Number).
                if self.created_by is not None:
                    builder.controlfield(self.created_by, tag='003')

                # 005 Date of creation
                builder.controlfield(modified.strftime('%Y%m%d%H%M%S.0'), tag='005')

                # 008 General Information / Informasjonskoder
                field008 = '{created}|||anz|naabn          |a|ana|||| d'.format(created=created.strftime('%y%m%d'))
                builder.controlfield(field008, tag='008')

                # 024 Other Standard Identifier
                if self.vocabulary.uri_format is not None:
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
                for tr in mappings.triples((URIRef(uri), None, None)):
                    m = ddc_matcher.match(tr[2])
                    if m:
                        self.nmappings += 1
                        ma = {'number': m.group(3), 'relation': mappingRelationsRepr[tr[1]]}
                        if m.group(2) is not None:
                            ma['table'] = m.group(2)
                        else:
                            ma['table'] = ''
                        cmappings.append(ma)

                for ma in sorted(cmappings, key=lambda k: '{},{},{}'.format(k['relation'], k['table'], k['number'])):
                    with builder.datafield(tag='083', ind1='0', ind2=' '):
                        if ma['table'] != '':
                            builder.subfield(ma['table'], code='z')
                        builder.subfield(ma['number'], code='a')
                        builder.subfield(ma['relation'], code='c')
                        builder.subfield('23', code='2')

                # 148/150/151/155 Authorized heading
                if resourceType == 'CompoundHeading':

                    # Determine tag number based on the first component:
                    rel = resources.get(id=resource.get('component')[0])
                    tag = {
                        'Temporal': '148',
                        'Topic': '150',
                        'Geographic': '151',
                        'GenreForm': '155',
                    }[rel['type'][0]]

                    with builder.datafield(tag=tag, ind1=' ', ind2=' '):

                        # Add the first component. Always use subfield $a. Correct???
                        term = rel.prefLabel[self.language.alpha2]
                        builder.subfield(term.value, code='a')

                        # Add remaining components
                        for value in resource.get('component')[1:]:
                            rel = resources.get(id=value)

                            # Determine subfield code from type:
                            sf = {
                                'Topic': 'x',
                                'Temporal': 'y',
                                'Geographic': 'z',
                                'GenreForm': 'v',
                            }[rel['type'][0]]

                            # OBS! 150 har også $b.. Men når brukes egentlig den??
                            term = rel.prefLabel[self.language.alpha2]
                            builder.subfield(term.value, code=sf)

                else:  # Not a compound heading
                    for lang, term in resource.prefLabel.items():

                        if lang == self.language.alpha2:
                            tag = self.tag_from_type(100, resourceType)
                        else:
                            tag = self.tag_from_type(400, resourceType)

                        # Always use subfield $a. Correct???
                        with builder.datafield(tag=tag, ind1=' ', ind2=' '):
                            builder.subfield(term.value, code='a')

                        # Atm. acronyms only for primary language
                        if lang == self.language.alpha2:
                            self.add_acronyms(builder, term, resourceType)

                    # Add 448/450/451/455 See from tracings
                    for lang, terms in resource.get('altLabel', {}).items():

                        tag = self.tag_from_type(400, resourceType)
                        # if lang == self.language.alpha2:
                        for term in terms:
                            with builder.datafield(tag=tag, ind1=' ', ind2=' '):
                                # Always use subfield $a. Correct???
                                builder.subfield(term.value, code='a')

                            # Atm. acronyms only for primary language
                            if lang == self.language.alpha2:
                                self.add_acronyms(builder, term, resourceType)

                # 548/550/551/555 See also
                tags = {
                    'Temporal': '548',
                    'Topic': '550',
                    'Geographic': '551',
                    'GenreForm': '555',
                    'KnuteTerm': '550'  # @TODO: ???
                }
                for value in resource.get('broader', []):
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

                for value in self.replaces.get(resource['id'], []):
                    rel = resources.get(id=value)
                    with builder.datafield(tag=self.tag_from_type(400, rel['type'][0]), ind1=' ', ind2=' '):
                        builder.subfield(rel.prefLabel[self.language.alpha2].value, code='a')
                        builder.subfield(self.global_cn(value), code='0')

                for value in resource.get('related', []):
                    rel = resources.get(id=value)
                    tag = self.tag_from_type(500, rel['type'][0])
                    # Note: rel['type'][0] can be 'KnuteTerm'! How to handle?
                    with builder.datafield(tag=tag, ind1=' ', ind2=' '):
                        builder.subfield(rel.prefLabel[self.language.alpha2].value, code='a')
                        builder.subfield(self.global_cn(value), code='0')

                # 680 Notes
                for value in resource.get('note', []):
                    with builder.datafield(tag='680', ind1=' ', ind2=' '):
                        builder.subfield(value, code='i')

                # 680 Notes (Definition)
                for value in resource.get('definition', []):
                    with builder.datafield(tag='680', ind1=' ', ind2=' '):
                        builder.subfield(value, code='i')
