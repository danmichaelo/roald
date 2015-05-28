# encoding=utf-8
import isodate
import xmlwitch


class Marc21(object):
    """
    Class for exporting data as MARC21
    """

    def __init__(self):
        super(Marc21, self).__init__()

    def convert(self, concepts):

        # Make a dictionary of narrower concepts for fast lookup
        self.narrower = {}
        for c in concepts.values():
            for x in c.get('broader', []):
                self.narrower[x] = self.narrower.get(x, []) + [c['id']]

        self.xml = xmlwitch.Builder(version='1.0', encoding='utf-8')

        with self.xml.collection(xmlns='info:lc/xmlns/marcxchange-v1'):
            for concept in concepts.values():
                self.convertConcept(concept, concepts)
        return str(self.xml)

    def convertConcept(self, concept, concepts):

        xml = self.xml

        conceptType = concept.get('type')

        if concept.get('created'):
            created = isodate.parse_datetime(concept.get('created'))
        else:
            created = isodate.isodatetime.datetime.now()
        if concept.get('created') is None:
            modified = created
        else:
            modified = isodate.parse_datetime(concept.get('created'))

        with xml.record(xmlns='http://www.loc.gov/MARC21/slim'):

            # Fixed leader for all records
            # Ref: <http://www.loc.gov/marc/uma/pt8-11.html#pt8>
            leader = '00000nz  a2200000n  4500'
            xml.leader(leader)

            # 001 Control number
            xml.controlfield(concept.get('id'), tag='001')

            # 003 MARC code for the agency whose system control number is contained in field 001 (Control Number).
            xml.controlfield('NoOU', tag='003')

            # 005 Date of creation
            xml.controlfield(modified.strftime('%Y%m%d%H%%M%S.0'), tag='005')

            # 008 Blablabla
            field008 = '{created}|||a|z||||||          || a||     d'.format(created=created.strftime('%y%m%d'))
            xml.controlfield(field008, tag='008')

            # 035 System control number ?
            # Her kan vi legge inn ID-er fra andre systemer, f.eks. BARE?
            # For eksempel, se XML-dataene fra WebDewey

            # 040 Cataloging source
            with xml.datafield(tag='040', ind1=' ', ind2=' '):
                xml.subfield('NoOU', code='a')     # Original cataloging agency
                xml.subfield('nor', code='b')      # Language of cataloging
                xml.subfield('NoOU', code='c')     # Transcribing agency
                xml.subfield('noubomn', code='f')  # Subject heading/thesaurus

            # 083 DDC number
            for value in concept.get('ddc', []):
                with xml.datafield(tag='083', ind1=' ', ind2=' '):
                    xml.subfield(value, code='a')

            # 148/150/151/155 Authorized heading
            if conceptType == 'CompoundHeading':

                # Determine tag number based on the first component:
                rel = concepts[concept.get('component')[0]]
                tag = {
                    'Temporal': '148',
                    'Topic': '150',
                    'Geographic': '151',
                    'GenreForm': '155',
                }[rel['type']]

                with xml.datafield(tag=tag, ind1=' ', ind2=' '):

                    # Add the first component. Always use subfield $a. Correct???
                    xml.subfield(rel['prefLabel']['nb'], code='a')

                    # Add remaining components
                    for value in concept.get('component')[1:]:
                        rel = concepts[value]

                        # Determine subfield code from type:
                        sf = {
                            'Topic': 'x',
                            'Temporal': 'y',
                            'Geographic': 'z',
                            'GenreForm': 'v',
                        }[rel['type']]

                        # OBS! 150 har også $b.. Men når brukes egentlig den??
                        xml.subfield(rel['prefLabel']['nb'], code=sf)

            else:  # Not a compound heading
                for lang, value in concept.get('prefLabel').items():
                    tag = {
                        'Temporal': '148',
                        'Topic': '150',
                        'Geographic': '151',
                        'GenreForm': '155',
                    }[conceptType]
                    if lang == 'nb':

                        # Always use subfield $a. Correct???
                        with xml.datafield(tag=tag, ind1=' ', ind2=' '):
                            xml.subfield(value, code='a')

                # Add 448/450/451/455 See from tracings
                for lang, values in concept.get('altLabel', {}).items():
                    tag = {
                        'Temporal': '448',
                        'Topic': '450',
                        'Geographic': '451',
                        'GenreForm': '455',
                    }[conceptType]
                    if lang == 'nb':
                        for value in values:
                            with xml.datafield(tag=tag, ind1=' ', ind2=' '):
                                # Always use subfield $a. Correct???
                                xml.subfield(value, code='a')
                for value in concept.get('acronym', {}):
                    tag = {
                        'Temporal': '448',
                        'Topic': '450',
                        'Geographic': '451',
                        'GenreForm': '455',
                    }[conceptType]
                    with xml.datafield(tag=tag, ind1=' ', ind2=' '):
                        xml.subfield(value, code='a')

                        # Heading in the tracing field is an acronym for the heading in the 1XX field.
                        # Ref: http://www.loc.gov/marc/authority/adtracing.html
                        xml.subfield('d', code='g')

            # 548/550/551/555 See also
            for value in concept.get('broader', []):
                rel = concepts[value]
                tag = {
                    'Temporal': '548',
                    'Topic': '550',
                    'Geographic': '551',
                    'GenreForm': '555',
                }[rel['type']]
                with xml.datafield(tag=tag, ind1=' ', ind2=' '):
                    xml.subfield(rel['prefLabel']['nb'], code='a')
                    xml.subfield('g', code='w')  # Ref: http://www.loc.gov/marc/authority/adtracing.html

            for value in self.narrower.get(concept['id'], []):
                rel = concepts[value]
                with xml.datafield(tag=tag, ind1=' ', ind2=' '):
                    xml.subfield(rel['prefLabel']['nb'], code='a')
                    xml.subfield('h', code='w')  # Ref: http://www.loc.gov/marc/authority/adtracing.html

            for value in concept.get('related', []):
                rel = concepts[value]
                tag = {
                    'Temporal': '548',
                    'Topic': '550',
                    'Geographic': '551',
                    'GenreForm': '555',
                }[rel['type']]
                with xml.datafield(tag=tag, ind1=' ', ind2=' '):
                    xml.subfield(rel['prefLabel']['nb'], code='a')

            # 680 Notes
            for value in concept.get('note', []):
                with xml.datafield(tag='680', ind1=' ', ind2=' '):
                    xml.subfield(value, code='i')
