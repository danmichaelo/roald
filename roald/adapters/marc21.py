# encoding=utf-8
import isodate
import xmlwitch
import iso639
import logging

logger = logging.getLogger(__name__)


class Marc21(object):
    """
    Class for exporting data as MARC21
    """

    vocabulary = None
    created_by = None  # Cataloguing agency 040 $a
    transcribed_by = None  # Transcribing agency 040 $c
    modified_by = None  # Modifying agency 040 $d
    vocabulary_code = None  # Vocabulary code, 040 $f
    language = None  # Default language code for 040 $b

    def __init__(self, vocabulary, created_by=None, vocabulary_code=None, language=None):
        super(Marc21, self).__init__()
        self.vocabulary = vocabulary
        self.created_by = created_by
        self.vocabulary_code = vocabulary_code
        self.language = language or self.vocabulary.default_language

    def serialize(self):

        if self.language is None:
            raise StandardError('MARC21 serialization needs language.')

        if type(self.language) != iso639.iso639._Language:
            raise StandardError('MARC21 language must be an instance of iso639.iso639._Language.')

        # Make a dictionary of narrower resources for fast lookup
        self.narrower = {}
        for c in self.vocabulary.resources:
            for x in c.get('broader', []):
                self.narrower[x] = self.narrower.get(x, []) + [c['id']]

        builder = xmlwitch.Builder(version='1.0', encoding='utf-8')

        with builder.collection(xmlns='info:lc/xmlns/marcxchange-v1'):
            for resource in self.vocabulary.resources:
                self.convert_resource(builder, resource, self.vocabulary.resources)
        return str(builder)

    def global_cn(self, value):
        if self.created_by is None:
            return value
        else:
            return '({}){}'.format(self.created_by, value)

    def add_acronyms(self, builder, term, resourceType):

        if term.get('hasAcronym'):
            tag = {
                'Temporal': '448',
                'Topic': '450',
                'Geographic': '451',
                'GenreForm': '455',
            }[resourceType]
            with builder.datafield(tag=tag, ind1=' ', ind2=' '):
                builder.subfield(term.get('hasAcronym'), code='a')

                # Heading in the tracing field is an acronym for the heading in the 1XX field.
                # Ref: http://www.loc.gov/marc/authority/adtracing.html
                builder.subfield('d', code='g')

        if term.get('acronymFor'):
            tag = {
                'Temporal': '448',
                'Topic': '450',
                'Geographic': '451',
                'GenreForm': '455',
            }[resourceType]
            with builder.datafield(tag=tag, ind1=' ', ind2=' '):
                builder.subfield(term.get('acronymFor'), code='a')

                # No special indication possible?
                # https://github.com/realfagstermer/roald/issues/8

    def convert_resource(self, builder, resource, resources):

        if resource.get('created'):
            created = isodate.parse_datetime(resource.get('created'))
        else:
            # Tja... Mrtermer har ingen datoer(!)
            created = isodate.isodatetime.datetime.now()  # isodate.isodatetime.datetime(2010, 1, 1)

        if resource.get('modified'):
            modified = isodate.parse_datetime(resource.get('modified'))
        else:
            modified = created

        # Loop over resource types
        for resourceType in resource.get('type'):

            if resourceType == 'VirtualCompoundHeading':
                continue

            if resourceType == 'Collection':
                # @TODO: Not sure how to handle these
                continue

            with builder.record(xmlns='http://www.loc.gov/MARC21/slim', type='Authority'):

                # Fixed leader for all records
                # Ref: <http://www.loc.gov/marc/uma/pt8-11.html#pt8>
                leader = '00000nz  a2200000n  4500'
                builder.leader(leader)

                # 001 Control number
                builder.controlfield(resource.get('id'), tag='001')

                # 003 MARC code for the agency whose system control number is contained in field 001 (Control Number).
                if self.created_by is not None:
                    builder.controlfield(self.created_by, tag='003')

                # 005 Date of creation
                builder.controlfield(modified.strftime('%Y%m%d%H%M%S.0'), tag='005')

                # 008 General Information / Informasjonskoder
                field008 = '{created}|||a|z||||||          || a||     d'.format(created=created.strftime('%y%m%d'))
                builder.controlfield(field008, tag='008')

                # 024 Other Standard Identifier
                if self.vocabulary.uri_format is not None:
                    with builder.datafield(tag='024', ind1='7', ind2=' '):
                        builder.subfield(self.vocabulary.uri(resource.get('id')), code='a')
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
                for value in resource.get('ddc', []):
                    with builder.datafield(tag='083', ind1='0', ind2='4'):
                        builder.subfield(value, code='a')

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
                        term = rel['prefLabel'][self.language.alpha2]
                        builder.subfield(term['value'], code='a')

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
                            term = rel['prefLabel'][self.language.alpha2]
                            builder.subfield(term['value'], code=sf)

                else:  # Not a compound heading
                    for lang, term in resource.get('prefLabel').items():
                        tag = {
                            'Temporal': '148',
                            'Topic': '150',
                            'Geographic': '151',
                            'GenreForm': '155',
                        }[resourceType]
                        if lang == self.language.alpha2:

                            # Always use subfield $a. Correct???
                            with builder.datafield(tag=tag, ind1=' ', ind2=' '):
                                builder.subfield(term['value'], code='a')

                            self.add_acronyms(builder, term, resourceType)


                    # Add 448/450/451/455 See from tracings
                    for lang, terms in resource.get('altLabel', {}).items():
                        tag = {
                            'Temporal': '448',
                            'Topic': '450',
                            'Geographic': '451',
                            'GenreForm': '455',
                        }[resourceType]
                        if lang == self.language.alpha2:
                            for term in terms:
                                with builder.datafield(tag=tag, ind1=' ', ind2=' '):
                                    # Always use subfield $a. Correct???
                                    builder.subfield(term['value'], code='a')

                                self.add_acronyms(builder, term, resourceType)

                # 548/550/551/555 See also
                tags = {
                    'Temporal': '548',
                    'Topic': '550',
                    'Geographic': '551',
                    'GenreForm': '555',
                }
                for value in resource.get('broader', []):
                    rel = resources.get(id=value)
                    rel_type = rel['type'][0]
                    if rel_type in tags:
                        with builder.datafield(tag=tags[rel_type], ind1=' ', ind2=' '):
                            builder.subfield(rel['prefLabel'][self.language.alpha2]['value'], code='a')
                            builder.subfield('h', code='w')  # Ref: http://www.loc.gov/marc/authority/adtracing.html
                            builder.subfield(self.global_cn(value), code='0')
                    else:
                        logger.warn('Cannot serialize "%s" <broader> "%s", because the latter has a unknown type.', value, rel['id'])

                for value in self.narrower.get(resource['id'], []):
                    rel = resources.get(id=value)
                    rel_type = rel['type'][0]
                    with builder.datafield(tag=tags[rel_type], ind1=' ', ind2=' '):
                        builder.subfield(rel['prefLabel'][self.language.alpha2]['value'], code='a')
                        builder.subfield('g', code='w')  # Ref: http://www.loc.gov/marc/authority/adtracing.html
                        builder.subfield(self.global_cn(value), code='0')

                for value in resource.get('related', []):
                    rel = resources.get(id=value)
                    tag = {
                        'Temporal': '548',
                        'Topic': '550',
                        'Geographic': '551',
                        'GenreForm': '555',
                    }[rel['type'][0]]
                    with builder.datafield(tag=tag, ind1=' ', ind2=' '):
                        builder.subfield(rel['prefLabel'][self.language.alpha2]['value'], code='a')
                        builder.subfield(self.global_cn(value), code='0')

                # 680 Notes
                for value in resource.get('note', []):
                    with builder.datafield(tag='680', ind1=' ', ind2=' '):
                        builder.subfield(value, code='i')
