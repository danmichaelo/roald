Roald III backend - en begynnelse
---------------------------------

Python-pakke som foreløpig tar seg av konvertering av data.
Pakken importerer data (fra Roald 2) og eksporterer (som MARC21XML og RDF/SKOS)

For å importere Roald 2-data, lagre Roald 3-data (JSON) og
eksportere som MARC21XML og RDF/SKOS:

```python
from roald import Roald
roald = Roald()
roald.importRoald2('./riidata/')
roald.save('realfagstermer.json')
roald.exportMarc21('realfagstermer.marc21.xml')
roald.exportRdfSkos('realfagstermer.ttl')
```

For å kjøre tester:

```bash
pip install -e .
py.test
```

