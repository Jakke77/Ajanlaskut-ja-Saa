# Ajanlaskut ja Sää 1.7.1 · kuvakkeet sovelluksen sisältä

[Lataa ajanlaskut-ja-saa_1.7.1_all.deb](https://github.com/Jakke77/Ajanlaskut-ja-Saa/raw/refs/heads/packages/v1.7.1/ajanlaskut-ja-saa_1.7.1_all.deb).
Yksityinen repo edellyttää GitHubiin kirjautumista. Tiedoston **Download raw file** lataa paketin.
Lataa myös [SHA256SUMS](SHA256SUMS) halutessasi tarkistamista varten.

Asenna latauskansiosta:

```bash
sudo apt install ./ajanlaskut-ja-saa_1.7.1_all.deb
```

**Valitse vanhasta ohjelmasta Lopeta sovellus.** Ikkunan × voi vain piilottaa sen.
Käynnistä uusi järjestelmäasennus komennolla `/usr/bin/ajanlaskut-ja-saa`.
Ikkunan otsikossa ja alareunassa näkyy nyt **1.7.1**.

## Kuvaketoiminnot

Avaa **Asetukset → vieritä alas → Sovelluskuvakkeet** tai vastaava kohta **Taustakuvat**-sivulta.

1. **Asenna ja korjaa sovelluskuvakkeet** asentaa kolme teemaa ja korjaa myös Firefoxin ja Thunderbirdin Snap-käynnistimet sekä GIMPin apt-kuvan.
2. **Käytä nykyisen teeman kuvakkeita** vaihtaa kuvakkeet heti.
3. **Kuvakkeet teeman vaihtuessa → Vaihda teeman mukana** ja tallennus ottaa vapaaehtoisen automaattisen vaihdon käyttöön.

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

Käytä samaa päivityskansiota, jonka nykyinen `codex-ajanlasku status` ilmoittaa.
Kun status näyttää **1.7.1**, lopeta vanha ohjelma valikosta ja käynnistä `codex-ajanlasku run`.
Molemmat asennukset käyttävät samoja kalenterimerkintöjä. Päivitys ei tyhjennä niitä.

Myös zipistä käynnistetty `python3 main.py` voi avata jo käynnissä olevan vanhan ohjelman.
Sulje siksi vanha kokonaan ennen lähdekoodin kokeilua.
[1.7.1-lähdepaketti](Ajanlaskut-ja-Saa-1.7.1-lahdekoodi.zip) sisältää Python-koodin;
repon oletushaaran ZIP ei ole sama tiedosto.

## Tarkistus

```bash
sha256sum -c SHA256SUMS
```

191 testiä läpäisi. Puretusta deb-paketista tarkistettiin myös versionumero, kuvakepaneelit molemmilla sivuilla ja käynnistyksen säilyttävä toiminta.
Katso [QA.log](QA.log). Paketti vaatii Python 3.10:n ja PyQt6:n vähintään 6.8.

[Lähdekoodi ja täydet päivitysohjeet](https://github.com/Jakke77/Ajanlaskut-ja-Saa/tree/codex/icon-theme-sync).
