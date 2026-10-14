# Ajanlaskut · Sää Android

Erillinen Android-sääsovellus ja kotinäyttöwidgetit. Se toimii ilman Ubuntu-
sovellusta, käyttäjätiliä ja API-avainta. Android 8.0 tai uudempi (API 26).

## Asentaminen

Lataa [APK ja tarkiste](https://github.com/Jakke77/Ajanlaskut-ja-Saa/tree/packages/android/v0.1.0)
puhelimeen GitHubiin kirjautuneena. Avaa `Ajanlaskut-Saa-Android-0.1.0.apk` ja
salli pyydettäessä asennus käyttämällesi selaimelle tai tiedostosovellukselle.
Kyseessä on kehitysavaimella allekirjoitettu ensimmäinen testiversio; sitä ei
ole julkaistu Google Playhin. Tarkiste on samassa kansiossa `SHA256SUMS`-tiedostossa.

Avaa **Ajanlaskut · Sää**, valitse sääpalvelu ja paikka, ja tallenna.
Paikan voi hakea nimellä tai syöttää koordinaatteina. Oletuspaikka on
Pöllönkangas, Oulu. Sovellus ei pyydä laitteen sijaintilupaa.

## Widgetit

Paina kotinäytön tyhjää kohtaa pitkään, avaa **Widgetit** ja etsi
**Ajanlaskut · Sää**. Lisää haluamasi koko ja valitse sen asetukset:

- **1×1:** nykyisen tunnin lämpötila ja lähteen lyhyt tunnus.
- **2×1:** lämpötila, tuuli ja paikka.
- **4×2:** lämpötila ja seuraavien tuntien ennustegraafi.

Ennustewidgettiä voi venyttää esimerkiksi kokoon **4×4**, jolloin käyrille
ja sademäärille jää enemmän tilaa. Ennustejakso voi olla 12 tai 24 tuntia.

Jokaiselle widgetille voi tallentaa oman palvelun, paikan ja väriteeman.
Widgetin koko ja uudelleenkoon muuttamisen mahdollisuus riippuvat myös
puhelimen kotinäyttösovelluksesta. Pienimmän oletuskoko on yksi ruutu.

**Enn.** tarkoittaa nykyisen tunnin ennustetta, ei lämpömittarin havaintoa.
Ilmainen lähdevalinta on **Yr / MET Norway**, **Ilmatieteen laitos** tai
**Open-Meteo**. Puuttuva tieto näkyy viivana; sovellus ei täytä sitä toisen
palvelun arvoilla. Vanha välimuistitieto merkitään vanhaksi.

Taustapäivitys pyydetään noin 30 minuutin välein. Android voi siirtää hakua
virransäästön tai verkkoyhteyden takia. Widgetin päivityspainike ja sovelluksen
päivitys hakevat tietoa myös käyttäjän pyynnöstä. Pienen widgetin painaminen
avaa sovelluksen, suuremmissa on myös oma päivityspainike. Palvelun vähimmäishakuväli
ja MET Norwayn Expires-välimuistiohje säilyvät.

## Kartat ja verkkonäkymät

Sovelluksessa voi avata Forecan ja Ilmatieteen laitoksen omat sadekartat sekä
Windyn virallisen kartan tai kartattoman tuntiennusteen. Verkkosivut säilyttävät
omat evästevalintansa, tekijämerkintänsä ja toimintonsa. Saman sivun voi avata
puhelimen selaimeen.

Forecan ja Windyn tietojen tuominen omiin Android-widgetteihin vaatisi
erilliset lisensoidut API-oikeudet. Tässä sovelluksessa niitä käytetään
palvelujen omina verkkonäkyminä. Windyn ennusteen alle ei sijoiteta muiden
palvelujen tietoja.

## Tietosuoja ja lähteet

Asetukset ja viimeisin ennuste tallentuvat sovelluksen yksityiseen
välimuistiin. Verkkohaku lähettää valitut koordinaatit sääpalvelulle ja
paikanhakutekstin Open-Meteon geokoodauspalvelulle. Verkkosivuilla on niiden
omat verkkopyynnöt ja tietosuojaehdot. Sovelluksessa ei ole analytiikkaa,
mainoskirjastoa tai käyttäjätunnuksia. HTTPS-varmenteet tarkistetaan.

Sääaineiston lähteet ja lisenssit: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
Ubuntun värit perustuvat [viralliseen väripalettiin](https://design.ubuntu.com/brand/colour-palette).
Sovellus on Jakke77:n itsenäinen projekti.

## Rakentaminen

Tarvitset JDK 17 tai 21, Android SDK:n API 35:n ja build-tools 35.0.0:n.
Gradle wrapper käyttää Gradlea 8.11.1 ja Android Gradle Pluginia 8.9.3.
Aseta `ANDROID_HOME` SDK:n kansioon ja aja projektin juuressa:

```bash
./gradlew testDebugUnitTest assembleDebug
```

APK syntyy polkuun `app/build/outputs/apk/debug/app-debug.apk`.
Yksikkötestit tarkistavat palvelujen aidot tietoformaatit, UTC-aikojen ja
tuntisateen kohdistuksen sekä puuttuvan tai vanhan ennusteen käsittelyn.
Robolectric-testit käyttävät lisäksi Androidin widgettien asetteluita,
RemoteViews-näkymiä ja ohjelmallista Canvas-piirtoa.
Kotinäyttöwidgetit pitää lisäksi kokeilla omassa puhelimessa: ensimmäistä
versiota ei ole testattu fyysisessä Android-laitteessa.

Tämän pilviympäristön tarkistettu rakennuskomento on
`/workspace/shared/android-build.sh testDebugUnitTest assembleDebug`.
Se säilyttää välityspalvelimen, TLS-luottamuksen ja työkalujen välimuistit
`/workspace/shared`-kansiossa. Pysyvästi käynnissä olevaa palvelinta ei tarvita.
