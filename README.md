# Ajanlaskut ja Sää 1.9.1 · Sadekartat widgetin kokoisiksi

**[Lataa deb-paketti](https://github.com/Jakke77/Ajanlaskut-ja-Saa/raw/refs/heads/packages/v1.9.1/ajanlaskut-ja-saa_1.9.1_all.deb)**
· [Lähdekoodin ZIP](https://github.com/Jakke77/Ajanlaskut-ja-Saa/raw/refs/heads/packages/v1.9.1/Ajanlaskut-ja-Saa-1.9.1-lahdekoodi.zip)
· [SHA256SUMS](SHA256SUMS).
Yksityinen repo edellyttää GitHubiin kirjautumista.

**Forecan ja Ilmatieteen laitoksen sadekartta täyttää nyt sisältöalueen**
pääikkunassa ja sääwidgetissä. Versiossa 1.9.0 kartan mukana näkyivät sivustojen
otsikot ja sivuvalikot. Uusi versio avaa palvelun oman kartan suurennustoiminnon
sovelluksen sisällä. Ikkuna pysyy tavallisen kokoisena, ja kartan omat säätimet,
aikajana, selitteet ja lähdemerkinnät säilyvät.

Valitse **Sää → Foreca tai Ilmatieteen laitos → Sadekartta**. Sääwidgetissä
sama valinta löytyy oikean hiirenpainikkeen valikosta. Foreca käyttää valitun
paikan koordinaatteja; FMI näyttää Suomen yhteisen sadekartan, jota voi siirtää
kartan säätimillä. Palvelun mahdollinen evästevalinta tehdään sen omassa
ikkunassa. Valinta voi tulla uudelleen seuraavalla käynnistyskerralla.
Jos kartta ei avaudu, käytä **Yritä uudelleen** tai **Avaa selaimessa**.

Windyn sääkartta ja kartaton tuntiennuste ovat mukana, samoin aiemmat
ennustegraafit, Ubuntu 26.10 Dark, taustakuvat, kuvaketeemat ja
**Ohje → Tietoa sovelluksesta**. 12/24 tunnin valinta näkyy sovelluksen omissa
ennustegraafeissa; verkkokartoilla ja Windyn tuntiennusteella on oma aikajana.

## Asentaminen ja käynnistäminen

Avaa pääte latauskansioon:

```bash
sudo apt install ./ajanlaskut-ja-saa_1.9.1_all.deb
```

Valitse vanhasta ohjelmasta **Lopeta sovellus**; pelkkä ikkunan × voi piilottaa sen.
Käynnistä uusi järjestelmäasennus:

```bash
/usr/bin/ajanlaskut-ja-saa --page weather
/usr/bin/ajanlaskut-ja-saa --version
```

Versioksi tulee **1.9.1**. Kalenterimerkinnät ja aiemmat teema-asetukset säilyvät.
Ubuntun PyQt6:n pitää olla vähintään 6.8. Verkkokartat ja Windyn tuntiennuste
tarvitsevat `python3-pyqt6.qtwebengine`-paketin.

**Jos käynnistät `codex-ajanlasku run` -komennolla**, päivitä myös sen erillinen
käyttäjäasennus. Pelkkä deb-asennus ei päivitä sitä.
[Nykyisen päivityskansion säilyttävä käyttöönottoketju](https://github.com/Jakke77/Ajanlaskut-ja-Saa/blob/codex/weather-radar-forecast/UPDATES.md#eri-versiot-järjestelmä--ja-käyttäjäasennuksessa)
ja [lähde-ZIPistä päivittäminen](https://github.com/Jakke77/Ajanlaskut-ja-Saa/blob/codex/weather-radar-forecast/UPDATES.md#uuden-github-version-tuominen-nykyiseen-käyttäjäasennukseen).

## Tarkistukset

306 yksikkö-/Qt-testiä läpäisi. Molempien palvelujen todelliset sadekartat
tarkistettiin Qt WebEnginellä pääikkunan koossa, pieneksi muutettuna sekä
suoraan pieneen widgettiin käynnistettäessä. Evästevalinnat jäivät käyttäjälle,
ja TLS-tarkistus säilyi. `.deb` ja lähde-ZIP verrattiin byteittäin lähdekoodiin;
päivitysohjelman turvallinen purku ja SHA256SUMS tarkistettiin.

[Testiloki](QA-unit.log) · [Karttojen selainkoe](QA-live-browser.md)
· [Pakettitarkistus](QA-package.json).
