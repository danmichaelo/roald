from roald import Roald
roald = Roald()

print 'Importing Roald 2 files'
roald.load('./riidata/', format='roald2')

print 'Saving JSON'
roald.save('realfagstermer.json')

print 'Converting to MARC21'
roald.export('realfagstermer.marc21.xml', format='marc21')

print 'Converting to RDF/SKOS'
roald.export('realfagstermer.ttl', format='rdfskos')
