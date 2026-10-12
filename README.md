# Ajanlaskut ja Sää 1.8.0 · Ubuntu 26.10 Dark ja oletuskuvakkeet

[Lataa ajanlaskut-ja-saa_1.8.0_all.deb](https://github.com/Jakke77/Ajanlaskut-ja-Saa/raw/refs/heads/packages/v1.8.0/ajanlaskut-ja-saa_1.8.0_all.deb).
Yksityinen repo edellyttää GitHubiin kirjautumista. Tiedoston **Download raw file** lataa paketin.
Lataa myös [SHA256SUMS](SHA256SUMS) halutessasi tarkistamista varten.

Asenna latauskansiosta:

```bash
sudo apt install ./ajanlaskut-ja-saa_1.8.0_all.deb
```

**Valitse vanhasta ohjelmasta Lopeta sovellus.** Ikkunan × voi vain piilottaa sen.
Käynnistä uusi järjestelmäasennus komennolla `/usr/bin/ajanlaskut-ja-saa`.
Ikkunan otsikossa ja alareunassa näkyy nyt **1.8.0**.

## Ubuntu 26.10 Dark

Valitse **Asetukset → Teema → Ubuntu 26.10 Dark** ja tallenna.
**Käytä valittua teemaa kaikissa widgeteissä** vaihtaa myös erikseen valitut widgettien teemat.
Paletti käyttää [Ubuntun virallisia brändivärejä](https://design.ubuntu.com/brand/colour-palette).
Taustakuva seuraa teemaa, jos **Taustakuva teeman vaihtuessa → Vaihda teeman mukana** on käytössä.
Sen voi ottaa käyttöön myös **Taustakuvat → Aseta Ubuntu 26.10 Dark-teeman tausta** -painikkeella.

![Ubuntu 26.10 Dark · Tähtikehä](ubuntu-2610-dark-tahtikeha.png)

## Kuvaketoiminnot

Avaa **Asetukset → vieritä alas → Sovelluskuvakkeet** tai vastaava kohta **Taustakuvat**-sivulta.

1. **Asenna ja korjaa sovelluskuvakkeet** asentaa neljä teemaa ja korjaa myös Firefoxin ja Thunderbirdin Snap-käynnistimet sekä GIMPin apt-kuvan.
2. **Käytä nykyisen teeman kuvakkeita** vaihtaa kuvakkeet heti.
3. **Kuvakkeet teeman vaihtuessa → Vaihda teeman mukana** ja tallennus ottaa vapaaehtoisen automaattisen vaihdon käyttöön.
4. **Käytä järjestelmän oletuskuvakkeita** palauttaa koneen oman oletusteeman ja sovelluksen tekemät käynnistinkuvakekorjaukset. Se poistaa kuvakkeiden automaattisen vaihdon käytöstä ja säilyttää widgettien teeman sekä taustakuvan.

![Sovelluskuvakkeet ja uusi oletuspainike](ubuntu-dark-oletuskuvakkeet.png)

Teemapaketit sisältyvät sovellukseen. Kuvakevaihto ei tarvitse verkkolatausta.
Oletuksena nykyiset kuvakkeet säilyvät. Palautuspainikkeet palauttavat aiemman teeman ja käynnistinkuvakkeet.

## Jos käytät codex-ajanlasku-käyttäjäasennusta

Deb päivittää järjestelmäasennuksen. Käyttäjäasennus pitää päivittää erikseen.
Aja debin asennuksen jälkeen ilman sudoa:

```bash
(
  umask 022
  ajanlasku_kanava="$HOME/.local/share/ajanlaskut-ja-saa/paivitykset"
  /usr/bin/python3 /usr/share/ajanlaskut-ja-saa/packaging/build.py \
    --publish-channel "$ajanlasku_kanava" &&
  /usr/bin/python3 "$ajanlasku_kanava/update-upgrade.py" setup &&
  export PATH="$HOME/.local/bin:$PATH" &&
  codex-ajanlasku update && codex-ajanlasku upgrade && codex-ajanlasku status
)
```

Julkaisun laaja Qt-piirrostesti voi kestää useita minuutteja.

Käytä samaa päivityskansiota, jonka nykyinen `codex-ajanlasku status` ilmoittaa.
Kun status näyttää **1.8.0**, lopeta vanha ohjelma valikosta ja käynnistä `codex-ajanlasku run`.
Molemmat asennukset käyttävät samoja kalenterimerkintöjä. Päivitys ei tyhjennä niitä.

Myös zipistä käynnistetty `python3 main.py` voi avata jo käynnissä olevan vanhan ohjelman.
Sulje siksi vanha kokonaan ennen lähdekoodin kokeilua.
[1.8.0-lähdepaketti](Ajanlaskut-ja-Saa-1.8.0-lahdekoodi.zip) sisältää Python-koodin;
repon oletushaaran ZIP ei ole sama tiedosto.

## Tarkistus

```bash
sha256sum -c SHA256SUMS
```

212 sovellustestiä ja 50 kuvakeasentimen testiä läpäisi. Laaja Qt-hyväksyntätesti tarkisti myös kellot, widgetit, fontit ja taustakuvat. Puretusta deb-paketista tarkistettiin myös versionumero, kuvakepaneelit molemmilla sivuilla ja käynnistyksen säilyttävä toiminta.
[QA.log](QA.log) erottaa teemakokonaisuuden hyväksyntätestin, lopullisen 212 testin ajon ja lopullisen debin toimintatarkistuksen. Paketti vaatii Python 3.10:n ja PyQt6:n vähintään 6.8.

[Lähdekoodi ja täydet päivitysohjeet](https://github.com/Jakke77/Ajanlaskut-ja-Saa/tree/codex/ubuntu-2610-dark).
