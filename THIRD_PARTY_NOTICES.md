# Aineistot ja riippuvuudet

## Yr / MET Norway

Locationforecast 2.0 -rajapinnan tuntiennuste:
https://api.met.no/weatherapi/locationforecast/2.0/documentation
Lähde MET Norway, https://www.met.no/. Aineisto CC BY 4.0:
https://creativecommons.org/licenses/by/4.0/
Sovellus rajaa tunnit, näyttää ne valitussa aikavyöhykkeessä, pyöristää arvot
ja piirtää omat käyrät. MET Norwayn kuvia tai logoa ei kopioida.
User-Agent ja palvelun Expires-välimuistiohje huomioidaan.

## Ilmatieteen laitos

Skandinavian piste-ennuste virallisesta avoimesta WFS-palvelusta:
https://opendata.fmi.fi/wfs
Lähde Ilmatieteen laitos, https://www.ilmatieteenlaitos.fi/.
CC BY 4.0 ja avoimen datan käyttöehdot:
https://www.ilmatieteenlaitos.fi/avoin-data-lisenssi
Sovellus rajaa tunnit ja piirtää omat käyrät.
Sadekartta https://www.ilmatieteenlaitos.fi/sadekartta avautuu erillisenä,
muuttamattomana verkkosivuna. Verkkosivun ja avoimen WFS-datan käyttöehdot
ovat eri käyttötapauksia; karttakuvaa tai sivun sisältöä ei irroteta kopioiksi.
Sivuston ehdot: https://www.ilmatieteenlaitos.fi/tietoa-sivustosta

## Open-Meteo ja paikkahaku

Ennustepalvelu: https://open-meteo.com/en/docs
Geokoodaus: https://open-meteo.com/en/docs/geocoding-api
Tietojen lisenssi CC BY 4.0, ilmaisen API:n käyttö on ei-kaupallista:
https://open-meteo.com/en/terms
Paikkanimet GeoNames, https://www.geonames.org/.
Tuuli pyydetään metreinä sekunnissa, ajat UTC Unix-aikoina. Edeltävän tunnin
sademäärä kohdistetaan widgetin alkavan tunnin ennusteväliin.

## Foreca ja Windy

Forecan oma sadetutka avautuu muuttamattomana osoitteesta
https://www.foreca.fi/sadetutka. Logoja, karttatiiliä tai ennustetietoja ei
kopioida Android-widgetteihin. Ehdot https://www.foreca.fi/kayttoehdot.
Lisensoitu ennuste-API: https://developer.foreca.com/.

Windyn viralliset upotusnäkymät:
https://embed.windy.com/config/map ja https://embed.windy.com/config/forecast.
Lähdemerkinnät, kartta ja ennustetaulukko säilyvät. Point Forecast API:ta,
sen muutettua testidataa tai toisen palvelun Windyksi nimettyä dataa ei käytetä.

RainViewerin vaihtoehtoinen sadekartta avautuu palvelun omana sivuna:
https://www.rainviewer.com/weather-radar-map-live.html
Sen karttatiiliä tai API-aineistoa ei kopioida sovelluksen omaksi kartaksi.

## Android ja rakennustyökalut

Sovellus käyttää Androidin omia Activity-, WebView-, RemoteViews-, Canvas-
ja JobScheduler-rajapintoja. Android SDK:n lisenssit koskevat työkalujen
käyttöä; SDK:ta tai JDK:ta ei toimiteta APK:ssa.
Gradle https://gradle.org/ ja Android Gradle Plugin
https://developer.android.com/build ovat rakennusriippuvuuksia.
JUnit 4 (Eclipse Public License 1.0) ja JSON-java (public domain, 20240303)
ovat yksikkötestien riippuvuuksia eivätkä sisälly APK:hon.
Robolectric 4.14.1 (MIT) ja sen Android-testikirjastot ovat myös vain testien
riippuvuuksia: https://robolectric.org/.

## Ubuntu-värit

https://design.ubuntu.com/brand/colour-palette
Ubuntu-tavaramerkki kuuluu Canonicalille. Sovelluksen oma tumma väriteema
ei tarkoita Canonicalin hyväksyntää tai virallista Ubuntu-julkaisua.
