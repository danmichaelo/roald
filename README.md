Konverteringsscript for data.ub
---

Konverterer fra Roald 2, Bibsys, MESH-XML til Marc21XML og RDF/SKOS.

For å installere pakken:

``` {.bash}
pip install -U --process-dependency-links -e .
```

For å kjøre tester:

``` {.bash}
py.test
```

Eventuelt:

``` {.bash}
pyenv local 2.6.9 2.7.11 3.3.6 3.4.3 3.5.1
pip install tox tox-pyenv
tox
```

Eksempler
---------

#### Fra Roald 2 til Roald 3, MARC21 og RDF/SKOS

(Se `dodo.py` i [realfagstermer-repoet](https://github.com/realfagstermer/realfagstermer)
for en faktisk implementasjon.)

For å importere Roald 2-data, lagre Roald 3-data (JSON) og eksportere
som MARC21XML og RDF/SKOS:

``` {.python}
from roald import Roald

roald = Roald()
roald.load('~/fuse/riidata/ureal/rii/', format='roald2', language='nb')
roald.set_uri_format('http://data.ub.uio.no/realfagstermer/c{id}')
roald.save('realfagstermer.json')

marc21options = {
  'vocabulary_code': 'noubomn',
  'created_by': 'NoOU'
}
roald.export('realfagstermer.marc21.xml', format='marc21', **marc21options)
roald.export('realfagstermer.ttl', format='rdfskos',
             include=['realfagstermer.scheme.ttl'], mappings_from=['mumapper.rdf'])

```

``` {.python}
from roald import Roald
roald = Roald()
roald.load('~/fuse/riidata/mr/', format='roald2', language='en')
roald.set_uri_format('http://data.ub.uio.no/mr/c{id}')
roald.save('menneskerettighetstermer.json')

marc21options = {
  'vocabulary_code': 'noubomr',
  'created_by': 'NoOU'
}
roald.export('menneskerettighetstermer.marc21.xml', format='marc21', **marc21options)
roald.export('menneskerettighetstermer.ttl', format='rdfskos')
```

(Her er `~/fuse/riidata` montert med sshfs til `/net/app-evs/w3-vh/no.uio.www_80/ub/emnesok/htdocs/data/`)

#### Tilfeldig uttrekk

For å hente ut en liste over 10 tilfeldige emneord:

```python
import numpy as np
from roald import Roald

roald = Roald()
roald.load('realfagstermer.json')

terms = [concept['prefLabel']['nb'] for concept in roald.concepts if 'nb' in concept['prefLabel']]
tilfeldige = [terms[x]['value'] for x in np.random.randint(0, len(termer), 10)]

```

Intern datamodell
------------------

Et vokabular (`Vocabulary`) har et sett av ressurser (`Resource`).
Hver ressurs kan være enten et *begrep* (`Concept`) eller en
*samling* (`Collection`).

Begreper er *autoriteter* som kan brukes som *emner* (for å beskrive dokumenters
innhold, geografiske eller kronologiske avgrensning). Noen kan også
brukes for å beskrive dokumenters bibliografiske form eller sjanger.

Samlinger er fasetter eller grupper som brukes for navigasjon i vokabularet.

Alle ressurser identifiseres ved en lokal numerisk identifikator,
som mappes til en global URI for datautveksling.

Hver ressurs kan ha én foretrukket/anbefalt term (`prefLabel`) per språk
og 0 eller flere ikke-foretrukne termer (`altLabel`) per språk. Et emne
kan for eksempel se slik ut:
(http://data.ub.uio.no/realfagstermer/c012680)

    {
      "id": 12680
      "prefLabel": {
        "nb": {"value": "Røye"},
        "en": {"value": "Arctic char"},
        "la": {"value": "Salvelinus alpinus"}
      },
      "altLabel": {
        "nb": [
          {"value": "Sjørøye"},
          {"value": "Arktisk røye"},
          {"value": "Røyer"},
          {"value": "Rør"},
          {"value": "Røyr"}
        ]
      },
      "type": [
        "Topic"
      ]
    }

Selv om det i modellen vår er den numeriske identifikatoren som primært
identifiserer begrepet, må vi forholde oss til klassiske
biblioteksystemer som Bibsys og Alma, der det er såkalte *indekstermer*
som primært identifiserer et begrep. Som indekstermer bruker vi de
foretrukne termene på norsk bokmål, og alle emner *må* derfor ha én
*unik* foretrukken term på norsk bokmål. For å ikke gjøre skillet mellom
ulike språk større enn nødvendig har vi foreløpig operert med at
foretrukne termer på andre språk også må være unike.

Hver ressurs har også ekstra metadata som dato for opprettelse og siste
endring.

### Klasser

#### Begrep

Egenskap        | Type        | Meta?  | Beskrivelse
----------------|-------------|--------|-----------------------------------------------------------------------------------
`id`            | string      |        | Unik lokal ID (påkrevd)
`type`          | array       |        | Liste over begrepstyper fra et fast sett (se liste under)
`prefLabel`     | object      |        | Key-value med språkkode som key, `Term` som value. (påkrevd)
`altLabel`      | object      |        | Key-value med språkkode som key, array av `Term` som value. (valgfri)
`definition`    | object      |        | Key-value med språkkode som key, streng som value. (valgfri)
`scopeNote`     | object      |        | Key-value med språkkode som key, streng som value. (valgfri)
`editorialNote` | array       |        | Lukket bemerkning. Språk er alltid vokabularets standardspråk. (valgfri)
`component`     | array       |        | (kun for strenger) : Liste av ID-er for streng-komponentene
`related`       | array       |        | Liste av ID-er for begrep
`broader`       | array       |        | Liste av ID-er for begrep
`replacedBy`    | array       |        | Liste av ID-er for begrep (må brukes sammen med `deprecated`)
`elementSymbol` | string      |        | Kjemisk symbol
`isTopTerm`     | boolean     |        | (for Humord)
`created`       | datetime    | meta   | Dato for opprettelse (påkrevd)
`createdBy`     | string      | meta   | (for fremtidig bruk)
`modified`      | datetime    | meta   | Dato for siste endring (påkrevd)
`modifiedBy`    | string      | meta   | (for fremtidig bruk)
`deprecated`    | datetime    | meta   | Dato for fjerning
`deprecatedBy`  | string      | meta   | (for fremtidig bruk)
`version`       | int         | meta   | (for fremtidig bruk)

(Egenskapene merket med "meta" er egenskaper som kanskje må skilles ut i
RDF-representasjonen hvis vi må skille mellom RWO/ikke-RWO)

#### Term

Egenskap        | Type        | Meta?  | Beskrivelse
----------------|-------------|--------|-----------------------------------------------------------------------------------
`value`         | string      |        | Termens verdi
`acronymFor`    | string      |        | Term som `value` er akronym for
`hasAcronym`    | string      |        | Akronym for `value`

### Begrepstyper

Vi opererer foreløpig med følgende typer:

Type                      | Navn                 | Beskrivelse                                                                                                                | MARC21-felt som brukes ved indeksering
--------------------------|----------------------|----------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------
`Topic`                   | Emne                 | I praksis Hjortsæters ‘innholdsbeskrivende emneord’?                                                                       | 650 Topical Term (en) / Sachsclagwort (de) / Term (sv).
`Place`                   | Sted                 | Geografisk punkt eller område (på jorden eller andre steder). Inkluderer også fiktive steder. Gir geografisk avgrensning.  | 651 Geographic name (en) / Geografikum (de) / Geografiskt namn (sv)
`Event`                   | Hendelse             | Hendelse, historisk periode, etc. Punkt eller utstrekning på tidslinja.                                                    | 648 Chronological Term (en) / Zeitschlagwort (de) Kronologisk term (sv)
`GenreForm`               | Form/sjanger         | Bibliografisk form eller sjanger.                                                                                          | 655 Genre/Form (en) / Genre/formschlagwort (de) / Genre eller form (sv)
`CompoundHeading`         | Emnestreng           | Sammensatt emne i streng                                                                                                   | (diverse)
`VirtualCompoundHeading`  | Virtuell emnestreng  | Sammensatt emneord i streng som påføres katalogposter komponentvis, ikke som streng.                                       | (diverse)

Hvert begrep har én eller flere typer (klasser). De fleste har kun én –
unntaket foreløpig er form/sjanger-begreper, som både kan brukes som
form/sjanger og som emneord. Det samme begrepet `30105 Science fiction`
kan brukes i 655 for å uttrykke at dokumentet *er Science fiction*
(eksempel, eller i 650 for å uttrykke at dokumentet *handler om Science
fiction* (eksempel). Dette i motsetning til f.eks. LCSH og Humord (Eks:
“Lærebøker” og “Lærebøker (Form)”).

### Strenger og virtuelle strenger.

- Strenger er sammensatte begreper der komponentene er egne begreper.
- Virtuelle strenger er alle strenger som inneholder minst én \$x, \$y
eller \$z-komponent, mens ekte strenger kun inneholder \$a og \$b.
Virtuelle strenger registreres ikke som en streng på katalogposter, men
i egne felt.

Eksempelvis er

    <REAL014357> Sauer : Himalaya

en virtuell streng (vi har 14913 slike per juni 2015). Den fungerer som
søkehjelp i emnesøket, men registreres som

    650 $a Sauer
    651 $a Himalaya

Derimot er

    <REAL022146> Fornybar energi : Livssyklusanalyse

er en ekte streng (vi har 888 slike per juni 2015). Den registreres som

    650 $a Fornybar energi $b Livssyklusanalyse

Vi har også et lite antall (~160) strenger med flere enn to ledd. Noen av
disse er en blanding av virtuelle og ekte strenger – for eksempel

    Tatoveringer : Realfag : Populærvitenskap

som skal registreres som

    650 $a Tatoveringer $b Realfag
    655 $a Populærvitenskap

Det er ikke helt klarlagt hvordan disse skal behandles enda.

### Akronymer

Kodes med `acronymFor` og `hasAcronym`.
Se [#5](https://github.com/realfagstermer/roald/issues/5). Hvis akronymet er den foretrukne varianten:

```json
{
  "prefLabel": {
    "nb": {
      "value": "LVSEM",
      "acronymFor": "Low-Voltage Scanning Electron Microscopy"
    },
    "en": {
      "value": "LVSEM",
      "acronymFor": "Low-Voltage Scanning Electron Microscopy"
    }
  }
}
```

Dette kan presenteres som `LVSEM (Low-Voltage Scanning Electron Microscopy)`.

Hvis akronymet ikke er den foretrukne varianten:

```json
{
  "prefLabel": {
    "nb": {
      "hasAcronym": "ISM",
      "value": "Interstellar materie"
    }
  }
}
```

Dette kan presenteres som `Interstellar materie (ISM)`.


RDF-serialisering
-----------------

Baserer seg i hovedsak på [SKOS](http://www.w3.org/TR/skos-reference). I tillegg bruker vi
* `owl:deprecated` for å markere at begreper har blitt tatt ut av bruk.
* `dcterms:isReplacedBy` for å markere at et begrep har blitt erstattet av et annet.
* `dcterms:identifier` for lokal identifikator (ikke URI).
* `isothes:subordinateArray` og `isothes:superOrdinate` fra [iso25964](http://pub.tenforce.com/schemas/iso25964/skos-thes)-utvidelsen.
* [et par lokale tillegg](https://github.com/realfagstermer/realfagstermer/blob/master/src/ub-onto.ttl)

MARC21-serialisering
--------------------

### Overordnede valg og åpne spørsmål

* Autoritetsposter av typen `VirtualCompoundHeading` ignoreres fordi disse påføres
  katalogpostene komponentvis, ikke som strenger. De skal/kan derfor ikke valideres i Alma.
  Poster av typen `CompoundHeading` (“Topic : Topic”-strenger) eksporteres,
  *uklart??*

* Se-henvisninger føres ikke som egne autoritetsposter, men legges inn som
  sporingsinnførsler (*tracings*), se http://www.loc.gov/marc/authority/adtracing.html . Akronymer markeres med
  `$g d`.

* Alle autoritetsposter av typen `GenreForm` i Realfagstermer kan egentlig
  brukes både som emne (Topic) og form/sjanger (GenreForm), men har bare én ID. Hvordan uttrykker vi disse i MARC21?
  Se [Issue #1](https://github.com/realfagstermer/roald/issues/1).

### Informasjon om felt som benyttes

* **Leader**:
  * Posisjon 6 har en av følgende verdier:
    * `n`: vanlig post
    * `x`: erstattet av en annen post
    * `s`: erstattet av mer enn én post
    * `d`: slettet

* **001 og 003** Control number and agency

  * Kontrollnummeret i 001 er en lokal identifikator på formen `REAL[0-9]{6}`, eks.: `REAL009035`.
  * Organisasjonskoden i 003 settes alltid til `No-TrBIB`
    (se "[MARC Code List for Organizations](http://www.loc.gov/marc/organizations/org-search.php)").
    Opprinnelig brukte vi `NoOU`, som vi egentlig mener er mer riktig, men dette førte til krøll i Alma.
  * Kontrollnummeret og organisasjonskoden utgjør til sammen en globalt unik
    identifikator som brukes for å henvise til autoritetsposten.
    Eks.: `(No-TrBIB)REAL009035`.

* **005** Date and Time of Latest Transaction
  * Tidspunkt for siste endring.

* **008** Fixed-Length Data Elements
  * De første 6 posisjonene brukes til opprettelsesdato for posten.
  * Posisjon 9 er "a" for vanlige begreper eller "e" for fasetter (*node labels*).
  * Posisjon 14 er alltid "b" (autoritetsposten *kan ikke* brukes i 1XX eller 7XX-felt)
  * Posisjon 15 er "a" (autoritetsposten *kan* brukes i 6XX-felt) for vanlige begreper
    og "b" (kan *ikke* brukes) for knutetermer og fasetter.

* **024** Other Standard Identifier
  * Postens URI (eks.: `http://data.ub.uio.no/realfagstermer/c010856`) med `$2 uri`

* **035** System Control Number
  * Kan brukes til å legge inn ID til posten i andre systemer, f.eks. BARE.
  * *Brukes foreløpig ikke*.

* **040** Cataloging Source
  * `$a No-TrBIB`
  * `$b nob`: Språkkode for posten. MARC-poster er dessverre énspråklige. For Realfagstermer, som er flerspråklig, oppgir vi "nob" siden det er bokmålstermen vi setter på katalogpostene.
    Vi kan evt. opprette én henvisningspost per språk, men da må vi også generere ID-er for disse.
  * `$f {vokabularkode}`: Verdien fra LCs [Subject Heading and Term Source Codes](https://www.loc.gov/standards/sourcelist/subject.html), f.eks. "humord" for Humord, "noubomn" for Realfagstermer.
  * Eksempel: `040 ## $a NO-TrBIB $b nob $f noubomn`

* **065** Other Classification Number
  * Fylles ut med MSC-nummer der det finnes. Med `$2 msc` fra [Classification Scheme Source Codes](http://www.loc.gov/standards/sourcelist/classification.html). Merk: MARC gir ingen måte å skille mellom ulike utgaver på – dette er en svakhet i 065!
  * Eksempel: `065 ## $a 81 $2 msc`

* **083** Dewey Decimal Classification Number
  * `$a`: Tilmappet Dewey-nummer
  * `$c`: Relasjonstype for mappingen (`=EQ`, `~EQ`, `BM`, `NM` eller `RM`)
  * `$2`: Utgave (23/nor)
  * Eksempel: `083 0# $a 541.37 $c BM $2 23/nor`

* **148/150/151/155** Authorized Heading
  * Foretrukket term på indeksspråket (norsk bokmål for de fleste av vokabularene).
  * Delfelt `$x` benyttes for strenger.
  * Eksempel: `150 ## $a Krepsdyrskall $9 rank=preferred $9 language=nb` (foretrukket term bokmål, `$9 er egentlig unødvendig her, men tas med for kompletthets skyld, se under.)

* **448/450/451/455** See From Tracings
  * Her legges ikke-foretrukne termer, samt foretrukne termer på andre språk. For å skille mellom disse bruker vi `$9 rank=preferred` og `$9 rank=alternative`, samt `$9 language={språkkode}`. Ikke helt ideelt.
  * Eksempel: `450 ## $a Krepsdyrskal $9 rank=preferred $9 language=nn` (foretrukket term på nynorsk)

* **548/550/551/555** See Also From Tracings
  * Hierarkiske relasjoner har `$w g` (overordnet) eller `$w h` (underordnet). Se [LC-dokumentasjon](http://www.loc.gov/marc/authority/adtracing.html). Se også-hevnisninger har ingen `$w`.
  * Merk: Begrepene i Realfagstermer er knyttet til ett eller flere fagområder. I MARC-serialiseringen
    er dette kodet med `55X` med `$w g`, som ikke er helt ideelt. I SKOS er det kodet som `SKOS.member`.
  * Eksempel: `550 ## $a Digital humaniora $w h $0 (No-TrBIB)HUME27908`

* **680** Public General Note
  * Noter og definisjoner.
  * Eksempel: `680 ## $i Programmeringsspråk` 

* **748/750/751/755** Heading Linking Entries
  * Mappinger til andre vokabularer (bortsett fra Dewey, som havner i 083)
  * Eksempel: `750 #4 $0 http://www.wikidata.org/entity/Q220457 $4 ~EQ`
