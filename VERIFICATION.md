# Tarkistukset · 14.10.2026 · 0.1.0

- `testDebugUnitTest lintDebug assembleDebug` onnistui.
- 37 testiä läpäisi, ei virheitä tai ohituksia: 24 palveluparseri-, aikaraja-
  ja välimuistitestiä, 6 widgetin tietojen esitystestiä sekä 7 Androidin
  todellisten RemoteViews-asettelujen ja Canvas-piirron testiä Robolectricilla.
- Yr/MET Norwayn, FMI:n ja Open-Meteon oikeat HTTPS-API-vastaukset
  parsittiin sovelluksen omilla käännetyillä Java-luokilla. Jokaisesta löytyi
  nykyisen tunnin lämpötila/tuuli ja vähintään 12 tuntia ennustetta.
- Android API 28:n asettelut suoritettiin testissä: 1×1, 2×1 ja suuremmat
  ennustewidgetit. −42° mahtui 40×40 dp soluun myös fonttiskaalalla 1,3.
  Testit tarkistivat erilliset widgettiasetukset, lähdemerkinnät, puuttuvan
  nykyhetken, natiivisti piirretyn lämpökäyrän/sateen ja bitmapin kokorajan.
- Tuntiväli perustuu UTC-aikoihin. Puuttuva tunti katkaisee lämpökäyrän;
  myöhemmillä tunneilla ei täytetä 12/24 tunnin rajauksen aukkoja.
  Puuttuva sade merkitään erikseen eikä sitä esitetä kuivana tuntina.
- Androidlint: 0 virhettä, 38 varoitusta. Varoitukset koskevat muun muassa
  vain suomenkielisiä tekstejä ja pieniin widgetteihin tarkoitettua tekstikokoa.
  Virheitä ei piilotettu baseline- tai ignore-määrityksillä.
- Lopullisen APK:n Android v2 -allekirjoitus, sovellustunnus, versio ja
  kaikkien kolmen widgetin metadata tarkistettiin APK:n sisältä.
  Sovellustunnus `fi.jakke77.saawidget`, versio 0.1.0, minSdk 26, targetSdk 35.
  SHA256: `06d7a68b9e408f7f0ce0c10f28fa6c17d03b684d51aa7cbe225101c741af8198`.
- Rakennustyökalujen viralliset tarkistussummat täsmäsivät. JDK 21.0.12.1,
  Gradle 8.11.1, AGP 8.9.3 ja SDK/build-tools 35 toimivat pilvessä.
  Setup-skripti ajettiin myös uudelleen. Proxy- ja TLS-tarkistukset säilyivät.

Ensimmäinen testiversio on kehitysavaimella allekirjoitettu sivuladattava APK.
Fyysistä Android-puhelinta, emulaattoria tai valmistajien kotinäyttösovelluksia
ei ajettu tässä ympäristössä. Robolectricin Android-suoritustestit eivät
korvaa widgetin lisäämisen ja Androidin virransäästön kokeilua omassa puhelimessa.
QA-kuvat sisältävät **esimerkkiennusteen**, eivät oikeita säähavaintoja.
