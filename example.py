from roald import Roald
roald = Roald()

print 'Importing Roald 2 files'
roald.importRoald2('./riidata')

print 'Saving JSON'
roald.save('realfagstermer.json')

print 'Converting to MARC21'
roald.exportMarc21('realfagstermer.marc21.xml')

print 'Converting to RDF/SKOS'
roald.exportRdfSkos('realfagstermer.ttl')
