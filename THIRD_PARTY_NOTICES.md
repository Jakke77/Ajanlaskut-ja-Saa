# Kolmansien osapuolten aineistot

## Oikeiden kalenterien muunnokset

`vendor/convertdate` on muuttamaton convertdate 2.4.0: MIT; Phil Schwartz,
John Walker, fitnr ja muut projektin tekijät. Säilytetty tekijänoikeusteksti ja
lisenssi: `vendor/convertdate-2.4.0.dist-info/LICENSE`.
Lähde: https://github.com/fitnr/convertdate
Dokumentaatio: https://convertdate.readthedocs.io/en/latest/

`vendor/pymeeus` on muuttamaton PyMeeus 0.5.12: LGPLv3; Dagoberto Salazar
ja muut projektin tekijät. Sen täydet Python-lähdekoodit toimitetaan mukana,
ei binääriä. Lisenssit ovat
`vendor/pymeeus-0.5.12.dist-info/licenses/LICENSE.txt` (GPLv3) ja
`vendor/pymeeus-0.5.12.dist-info/licenses/COPYING.LESSER` (LGPLv3-lisäehdot).
Lähde: https://github.com/architest/pymeeus

Kirjastot asennettiin PyPI:n versionoiduista julkaisuista paikalliseen kansioon,
eivätkä ne muuta järjestelmän Python-asennusta. Käyttäjä voi korvata tai muokata
näitä lähdekirjastoja ja käyttää järjestelmän asennettua kirjastoa. Sovelluksen
oman koodin MIT-lisenssi ei muuta kirjastojen lisenssejä. Kalenterien nimet ja
laskentatulokset eivät ole tämän sovelluksen keksimiä uusia ajanlaskusääntöjä.

## Alkuperäiset sovellukset

Ajanlaskut ja Sää hyödyntää Jakke77:n omien projektien kalenterimuunnoksia,
sääkerrosta ja muistutuksen ääntä. Käyttöliittymä, yhteinen ohjain ja tietomalli
on toteutettu tähän sovellukseen. Alkuperäiset MIT-tekijänoikeusmerkinnät säilyvät
projektin LICENSE-tiedostossa: Copyright (c) 2026 Jakke77.

- Tähtiaika: https://github.com/Jakke77/tahtiaika
- Varjoaika/Goottikalenteri: https://github.com/Jakke77/goottikalenteri
- Pöllönkankaan sää: https://github.com/Jakke77/Ubuntu_ChatGPT_Widgget
- Varjosään käyttämä päiväennuste: https://github.com/Jakke77/varjosaa

## Yr / MET Norway

Yr-vaihtoehdon ennuste on MET Norwayn Locationforecast 2.0 -rajapinnasta.
Säätietojen lisenssi: Creative Commons Attribution 4.0 International.

- Tekijä: MET Norway, https://www.met.no/
- Palvelu: https://api.met.no/weatherapi/locationforecast/2.0/documentation
- Lisenssi: https://creativecommons.org/licenses/by/4.0/
- Muutokset: 12/24 tunnin rajaus, valittu paikallisaika, pyöristetyt lukuarvot ja käyrät.

Yr-linkki vie alkuperäisen sijainnin ennustesivulle. Yr:n logoa tai sääsymbolien
kuvatiedostoja ei käytetä. Widgetin symbolit piirretään sovelluksen omalla koodilla.

## PyQt6 ja Qt

PyQt6: Riverbank Computing, GPL v3 tai kaupallinen lisenssi.
https://www.riverbankcomputing.com/software/pyqt/
https://www.riverbankcomputing.com/static/Docs/PyQt6/introduction.html#license

Qt: The Qt Company ja muut tekijät, moduulikohtaiset lisenssit.
https://www.qt.io/licensing/

Oman koodin MIT-lisenssi ei muuta riippuvuuksien lisenssejä. Tässä toimitetaan
lähdekoodi, ei PyQt6-/Qt-binaaripakettia. Jos julkaiset myöhemmin asennuspaketin
tai AppImagen, sisällytä myös riippuvuuksien vaaditut lisenssit ja lähdekooditiedot.

## wttr.in

Kolmen päivän Varjosää-ennuste: https://wttr.in/
Palvelun avoin lähdekoodi ja tietolähteet: https://github.com/chubin/wttr.in
Päiväennuste esitetään tekstinä, mutta data ei ole tämän sovelluksen oman koodin
MIT-lisenssin alainen aineisto. Kalenterimerkintöjä ei välitetä sääpalvelulle.


## Ilmatieteen laitos

Toimitettu Skandinavian piste-ennuste avoimesta WFS-palvelusta.
Lähde: Ilmatieteen laitos, https://www.ilmatieteenlaitos.fi/
Palvelu: https://opendata.fmi.fi/wfs
Lisenssi ja käyttöehdot: https://www.ilmatieteenlaitos.fi/avoin-data-lisenssi
CC BY 4.0. Aineisto rajataan tuntiennusteeksi ja esitetään omilla kuvakkeilla/käyrillä.

Sadekartta avautuu muuttamattomana palvelun omana sivuna:
https://www.ilmatieteenlaitos.fi/sadekartta
Verkkosivun aineisto ja avoimen WFS-rajapinnan aineisto ovat eri käyttötapauksia.
Kartasta ei eroteta tai kopioida kuvia eikä poisteta palvelun merkintöjä.
Widgettiin sovittaminen käyttää kartan omaa suurennustoimintoa. Sen kartta,
aikajana ja selitteet pysyvät samassa palvelun omassa näkymässä.
Sivuston käyttöehdot: https://www.ilmatieteenlaitos.fi/tietoa-sivustosta

## Foreca

Foreca.fi:n julkisen tuntiennusteen epävirallinen lukija.
https://www.foreca.fi/
Forecan aineisto ei ole tämän repon MIT-lisenssin alaista avointa dataa.
Forecan kuvatiedostoja, logoa ja kuvakkeita ei kopioida; kuvakkeet piirretään itse.
Sääkoodeja tulkitaan dokumentaation mukaan:
https://developer.foreca.com/resources
Virallinen API ja sen käyttöehdot: https://developer.foreca.com/

Oma sadetutka avautuu Forecan nykyisessä tutkanäkymässä:
https://www.foreca.fi/tutka
Palvelun oma JavaScript tukee paikan `lt`-/`ln`-koordinaatteja, `z`-zoomia ja
`l=tutkaennuste`-kerrosta. Kartta sovitetaan widgettiin sen omalla
suurennustoiminnolla; verkkosivun HTML:ää tai karttatiiliä ei kopioida.
Karttatiiliä, logoa, hallintapainikkeita tai kartta-aineistoa ei kopioida.
Verkkosivun käyttöehdot: https://www.foreca.fi/kayttoehdot

## Windy

Virallinen upotettu kartta: https://embed.windy.com/config/map
Virallinen kartaton tuntiennuste: https://embed.windy.com/config/forecast
Kartta, ennustetaulukko, kuvakkeet, merkinnät ja aineisto latautuvat Windyn palvelusta.
Kartasta ei poisteta lähdemerkintöjä eikä tehdä omaa karttatiilikopiota.
Käyttöehdot ja tietosuoja ovat Windyn upotuspalvelun sivulla.
Point Forecast API ei kuulu tähän toteutukseen. Sen testiavaimen muuttamaa
aineistoa ei käytetä oikeana sääennusteena eikä muiden palvelujen tietoja
esitetä Windyn ennusteena.
Qt WebEngine on riippuvuus; Qt/PyQt-binaareja ei sisällytetä sovelluksen .deb-pakettiin.

## RainViewer

Vaihtoehtoisen sadekartan linkki avaa palvelun oman sivun selaimessa:
https://www.rainviewer.com/weather-radar-map-live.html
RainViewerin karttatiiliä tai API-aineistoa ei kopioida tai noudeta sovelluksen
omaksi kartaksi. Verkkosivun lähdemerkinnät ja käyttöehdot säilyvät.

## Paikkahaku

Open-Meteon Geocoding API: https://open-meteo.com/en/docs/geocoding-api
Paikkanimitiedot: GeoNames, https://www.geonames.org/
Open-Meteon ilmaispalvelu on tarkoitettu ei-kaupalliseen käyttöön.

## Kupari-teema

Oma koodilla piirretty Ubuntu 26.04 -henkinen ulkoasu, jonka värit ja orbitit
pohjautuvat käyttäjän antamaan esimerkkikuvaan. Käyttäjän taustakuvaa ei toimiteta
paketissa. Teema ei ole Canonicalin virallinen teema. Ubuntu-tavaramerkki kuuluu
Canonicalille; ohjelma on Jakke77:n itsenäinen projekti.

Version 1.1.0 mukana toimitetaan erikseen luotu Kuparinen tähtikello -fanitaustakuva
ja sen luontikuvaus. Kuva ei ole alkuperäisen työpöytäkuvan kopio. Se on luotu
sisäänrakennetulla kuvanluonnilla. Ubuntu-logo ei tarkoita Canonicalin hyväksyntää.
Kuville ei ole määritetty tämän sovelluskoodin MIT-lisenssistä erillistä avointa
jakelulisenssiä; yksityisen teema-repon mahdollinen julkinen julkaisu päätetään
erikseen. Taustakuvien luontikuvaukset ovat `assets/wallpapers`-kansiossa.

GNOME-taustakuvasovitin käyttää valinnaista PyGObject/Gio-riippuvuutta ja koneella
valmiiksi käytössä olevaa Dia Wall 77 -lisäosaa. Lisäosan koodia ei kopioida
sovellukseen eikä lukituksen turvallisuusasetuksia muuteta.

## Ubuntu 26.10 Dark

Version 1.8.0 itsenäinen faniteema käyttää
[Ubuntun virallista brändipalettia](https://design.ubuntu.com/brand/colour-palette):
musta `#000000`, tumma munakoiso `#2C001E`, keskimmäinen munakoiso `#5E2750`,
oranssi `#E95420`, valkoinen `#FFFFFF` ja lämmin harmaa `#AEA79F`.
SVG-kuvakkeet ovat tämän projektin alkuperäisiä piirroksia. Sovellusten nimet
ja tunnukset kuuluvat niiden omistajille; teemassa ei toimiteta muiden
kuvaketeemojen kopioita. Tähtikehä-taustakuva on luotu sisäänrakennetulla
kuvanluonnilla. Sen luontikuvaus on `assets/wallpapers/ubuntu-2610-dark`-kansiossa.
Teema ei ole Canonicalin virallinen Ubuntu 26.10 -kuvakepaketti tai julkaisu­tausta.
