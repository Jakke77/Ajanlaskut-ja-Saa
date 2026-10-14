# Ajanlaskut ja Sää 1.9.0 · Sadekartat ja Windyn tuntiennuste

**[Lataa deb-paketti](https://github.com/Jakke77/Ajanlaskut-ja-Saa/raw/refs/heads/packages/v1.9.0/ajanlaskut-ja-saa_1.9.0_all.deb)**
· [Lähdekoodin ZIP](https://github.com/Jakke77/Ajanlaskut-ja-Saa/raw/refs/heads/packages/v1.9.0/Ajanlaskut-ja-Saa-1.9.0-lahdekoodi.zip)
· [SHA256SUMS](SHA256SUMS).
Yksityinen repo edellyttää GitHubiin kirjautumista.

Valitse **Sää → Palvelu → Näkymä**:

- Foreca ja Ilmatieteen laitos: oma ennustegraafi tai palvelun oma sadekartta.
- Windy: sääkartta tai kartaton tuntiennuste valitulle paikalle.
- Yr / MET Norway: aiempi 12/24 tunnin ennustegraafi.

Sama valinta löytyy sääwidgetin oikean painikkeen valikosta ja säilyy
palvelukohtaisesti. Windyn virallinen ennuste sovitetaan myös pieneen widgettiin;
sen data, aikajana ja merkinnät säilyvät. Web-näkymä tarjoaa uudelleenyrityksen
ja saman sivun avaamisen selaimessa. FMI:n kartta on Suomen yhteinen kartta;
Foreca käyttää tunnistettua paikkakarttaa tai Suomen sadetutkaa.

Mukana ovat myös aiemmat Ubuntu 26.10 Dark, taustakuvat, neljä kuvaketeemaa,
järjestelmän oletuskuvakkeiden palautus ja **Ohje → Tietoa sovelluksesta**.

## Asentaminen ja käynnistäminen

Avaa pääte latauskansioon:

```bash
sudo apt install ./ajanlaskut-ja-saa_1.9.0_all.deb
```

Valitse vanhasta ohjelmasta **Lopeta sovellus**; pelkkä ikkunan × voi piilottaa sen.
Käynnistä uusi järjestelmäasennus:

```bash
/usr/bin/ajanlaskut-ja-saa --page weather
/usr/bin/ajanlaskut-ja-saa --version
```

Versioksi tulee **1.9.0**. Kalenterimerkinnät ja aiemmat teema-asetukset säilyvät.
Ubuntun PyQt6:n pitää olla vähintään 6.8. Kartat ja Windyn tuntiennuste tarvitsevat
myös `python3-pyqt6.qtwebengine`-paketin; tarvittaessa sivun voi avata selaimeen.

**Jos käynnistät `codex-ajanlasku run` -komennolla**, päivitä myös sen erillinen
käyttäjäasennus. Pelkkä deb-asennus ei päivitä sitä.
[Nykyisen päivityskansion säilyttävä käyttöönottoketju](https://github.com/Jakke77/Ajanlaskut-ja-Saa/blob/codex/weather-radar-forecast/UPDATES.md#eri-versiot-järjestelmä--ja-käyttäjäasennuksessa)
ja [lähde-ZIPistä päivittäminen](https://github.com/Jakke77/Ajanlaskut-ja-Saa/blob/codex/weather-radar-forecast/UPDATES.md#uuden-github-version-tuominen-nykyiseen-käyttäjäasennukseen).

## Tarkistukset

281 yksikkö-/Qt-testiä läpäisi. Laaja eristetty käyttöliittymätesti läpäisi.
Paketin ja lähde-ZIPin kaikki 1864 tiedostoa verrattiin byteittäin lähdekoodiin;
SHA256SUMS tarkistettiin. Windyn oikea tuntiennuste ladattiin Qt WebEnginellä
TLS-tarkistuksen säilyttäen. Forecan/FMI:n sivut ja hallinta latautuivat,
mutta niiden karttagrafiikkaa ei voitu varmistaa puuttuvan WebGL:n vuoksi.
[Testiloki](QA-unit.log) · [laaja testi](QA-self-test.log) · [selainkoe](QA-live-browser.md).

Erillinen [Android-sovellus ja sen APK](https://github.com/Jakke77/Ajanlaskut-ja-Saa/tree/packages/android/v0.1.0)
toimivat puhelimessa itsenäisesti; ne eivät kuulu tähän Ubuntu-pakettiin.
