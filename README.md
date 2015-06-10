Roald III backend - en begynnelse
---------------------------------

Python-pakke som foreløpig tar seg av konvertering av data. Pakken
importerer data (fra Roald 2) og eksporterer (som MARC21XML og RDF/SKOS)

For å importere Roald 2-data, lagre Roald 3-data (JSON) og eksportere
som MARC21XML og RDF/SKOS:

``` {.python}
from roald import Roald
roald = Roald()
roald.load('./riidata/', format='roald2')
roald.save('realfagstermer.json')
roald.export('realfagstermer.marc21.xml', format='marc21')
roald.export('realfagstermer.ttl', format='rdfskos')
```

For å kjøre tester:

``` {.bash}
pip install -e .
py.test
```

Datamodell: (KLADD)
-------------------

Realfagstermer er et kontrollert sett av *begreper* eller
*autoriteter*?? som kan brukes som *emner* (for å beskrive dokumenters
innhold, geografiske eller kronologiske avgrensning). Noen kan også
brukes for å beskrive dokumenters bibliografiske form eller sjanger.
Omfangsmessig kan vi si at Realfagstermer tilsvarer LCSH + LCGF (men
ikke f.eks. LC/NAF).

Et begrep (`Concept`) identifiseres ved en lokal numerisk identifikator,
som kan mappes til en global URI for datautveksling.

Hvert begrep kan ha én foretrukket/anbefalt term (`prefLabel`) per språk
og 0 eller flere ikke-foretrukne termer (`altLabel`) per språk. Et emne
kan for eksempel se slik ut:
(http://data.ub.uio.no/realfagstermer/c012680)

    {
      "id": 12680
      "prefLabel": {
        "nb": "Røye",
        "en": "Arctic char",
        "la": "Salvelinus alpinus"
      },
      "altLabel": {
        "nb": [
          "Sjørøye",
          "Arktisk røye",
          "Røyer",
          "Rør",
          "Røyr"
        ]
      },
      "type": [
        "Topic"
      ]
    }

Selv om det i modellen vår er den numeriske identifikatoren som primært
identifiserer begrepet. Samtidig må vi forholde oss til klassiske
biblioteksystemer som Bibsys og Alma, der det er såkalte indekstermer
som primært identifiserer et begrep. Som indekstermer bruker vi de
foretrukne termene på norsk bokmål, og alle emner *må* derfor ha én
*unik* foretrukken term på norsk bokmål. For å ikke gjøre skillet mellom
ulike språk større enn nødvendig har vi foreløpig operert med at
foretrukne termer på andre språk også må være unike.

Hvert begrep har også ekstra metadata som dato for opprettelse og siste
endring.

Egenskap        | Type        | Meta?  | Beskrivelse
----------------|-------------|--------|-----------------------------------------------------------------------------------
`id`            | string      |        | Unik lokal ID (påkrevd)
`type`          | array       |        | Liste over begrepstyper fra et fast sett (se liste under)
`prefLabel`     | object      |        | Key-value med språkkode som key, streng som value. (påkrevd)
`altLabel`      | object      |        | Key-value med språkkode som key, array av streng. (valgfri)
`component`     | array       |        | (kun for strenger) : Liste av ID-er for streng-komponentene
`created`       | datetime    | meta   | Dato for opprettelse (påkrevd)
`createdBy`     | string      | meta   | (for fremtidig bruk)
`modified`      | datetime    | meta   | Dato for siste endring (påkrevd)
`modifiedBy`    | string      | meta   | (for fremtidig bruk)
`version`       | int         | meta   | (for fremtidig bruk)

(Egenskapene merket med "meta" er egenskaper som kanskje må skilles ut i
RDF-representasjonen hvis vi må skille mellom RWO/ikke-RWO)

### Begrepstyper

Vi opererer foreløpig med følgende typer:

Type                      | Navn                 | Beskrivelse                                                                                                                | MARC21-felt som brukes ved indeksering
--------------------------|----------------------|----------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------
`Topic`                   | Emne                 | I praksis Hjortsæters ‘innholdsbeskrivende emneord’?                                                                       | 650 Topical Term (en) / Sachsclagwort (de) / Term (sv).
`Place`                   | Sted                 | Geografisk punkt eller område (på jorden eller andre steder). Inkluderer også fiktive steder. Gir geografisk avgrensning.  | 651 Geographic name (en) / Geografikum (de) / Geografiskt namn (sv)
`Event`                   | Hendelse             | Hendelse, historisk periode, etc. Punkt eller utstrekning på tidslinja.                                                    | 648 Chronological Term (en) / Zeitschlagwort (de) Kronologisk term (sv)
`FormGenre`               | Form/sjanger         | Bibliografisk form eller sjanger.                                                                                          | 655 Genre/Form (en) / Genre/formschlagwort (de) / Genre eller form (sv)
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

RDF-serialisering
-----------------

TODO

MARC21-serialisering
--------------------

TODO

Ordliste
--------

-   **Begrep** (Concept / Begriff): “kunnskapsenhet som
    er dannet gjennom en unik kombinasjon av kjennetegn” (TTN/I-term).
    Begrep representeres gjennom betegnelser (designations): enten
    termer (for allmennbegreper), egennavn (individualbegrep) eller
    symboler. Ref:
    http://www.sprakradet.no/globalassets/sprakarbeid/terminologi/nordterm—terminologiens-terminologi—no-en—2011-01-27.pdf

-   **Emne** (Subject): hva eller hvem et dokument handler om

-   **Deskriptor** eller **indeksterm**: Term som påføres katalogpost ved indeksering
   (i tradisjonelle biblioteksystemer der det ikke er mulig å påføre andre identifikatorer)
