# Sadekarttojen todellinen selainkoe · 14.10.2026

Lopullinen tuotantokoodi avasi Forecan ja Ilmatieteen laitoksen oikeat
sadekartat Qt WebEngine 6.11:llä. Sovelluksen oma `WeatherWebView` ja
`RadarFocus` tekivät kartan avaamisen; testillä ei korvattu niiden toimintaa.
Molemmat Qt-ikkunat pysyivät normaalikoossa, ja kartan oma fullscreen-elementti
täytti vain selaimen sisältöalueen.

| Palvelu | Käynnistys | Kartan koko | Tulos |
| --- | --- | --- | --- |
| Foreca | Pääikkunan koko | 1200×817 | Läpäisi |
| FMI | Pääikkunan koko | 1200×817 | Läpäisi |
| Foreca | Valmiin kartan pienentäminen | 389×156 | Läpäisi |
| FMI | Valmiin kartan pienentäminen | 389×156 | Läpäisi |
| Foreca | Suoraan pieneen widgettiin | 389×156 | Läpäisi |
| FMI | Suoraan pieneen widgettiin | 389×156 | Läpäisi |

Pienen widgetin isäntäikkuna oli 432×276 ja sisältökehys 389×189. Kartan
valmistuminen vahvistettiin DOM fullscreen -tilasta; vasta sen jälkeen
tuotantokoodi merkitsi pyydetyn kartan ladatuksi. Valmis selainzoom oli 1.0.
Foreca näytti valittujen Oulun koordinaattien kartan sekä omat karttasäätimet,
ajan ja OpenMapTiles/OpenStreetMap-lähdemerkinnät. FMI näytti oman Suomen
sadekarttansa, aikajanan, toiston ja sadeselitteet.

## Evästevalinta

Tuotantokoodi jätti kartan avaamisen odottamaan alkuperäistä evästevalintaa.
Poisheittoprofiilin testaaja painoi Forecan **Estä kaikki** ja FMI:n
**Salli vain välttämättömät** -painikkeita alkuperäisessä sivuston ikkunassa.
Nämä testin erilliset käyttäjätoiminnot on kirjattu JSON-tuloksiin.
Sovellus ei valitse evästeitä käyttäjän puolesta.

FMI:n zoom oli **1.0 ennen valintaa** sekä isossa että suoraan pieneen
widgettiin käynnistetyssä näkymässä. Vain valinnan jälkeen karttapainiketta
peittävä sivuston navigaatio käynnisti tilapäisen sovituksen; valmis kartta
palautui normaaliin zoomiin. Evästeikkunan HTML:ää tai tyylejä ei muutettu.

## Lähde ja tarkistusympäristö

Kaikkien kolmen karttatoteutuksen tiedoston SHA256 täsmää julkaistuun
lähdekoodiin sekä ison/pienennetyn näkymän että suoran pienen käynnistyksen
koeajossa. Lähde oli konttiin liitettynä vain luettavaksi.

Koeajo käytti kertakäyttöistä Docker-konttia, Xvfb:tä ja Mesan ohjelmallista
OpenGL:ää. HTTPS-varmenteiden tarkistus säilyi. Ympäristön tarjoama CA oli
luotettu vain kontin omassa tilapäisessä NSS-hakemistossa; isäntäympäristön
CA-/NSS-asetuksia ei muutettu. Testikontit poistettiin. Xvfb-paketin SHA256
varmistettiin allekirjoitetun Debian-julkaisun ja pakettimetadatan kautta.
Testin selainasetuksia ja varmenteita ei lisätty sovellukseen tai pakettiin.

[Iso/pienennetty näkymä](final-adapter-results.json)
· [Suora pieni käynnistys](fresh-small-adapter-results.json)
· [Ison kokeen lähdehashit](final-adapter-code-hashes.json)
· [Pienen kokeen lähdehashit](fresh-small-adapter-code-hashes.json).
