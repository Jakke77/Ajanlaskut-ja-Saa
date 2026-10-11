# Ajanlaskut ja Sää 1.6.1 — valmis Debian-paketti

[Lataa ajanlaskut-ja-saa_1.6.1_all.deb](https://github.com/Jakke77/Ajanlaskut-ja-Saa/raw/refs/heads/packages/v1.6.1/ajanlaskut-ja-saa_1.6.1_all.deb)

Yksityinen repo: avaa latauslinkki GitHubiin kirjautuneena. Myös tiedoston **Download raw file** lataa paketin.

Asenna latauskansiosta:

```bash
sudo apt install ./ajanlaskut-ja-saa_1.6.1_all.deb
```

Valitse vanhasta sovelluksesta **Lopeta sovellus**. Järjestelmäasennus käynnistyy komennolla `/usr/bin/ajanlaskut-ja-saa`.

Jos käytät aiempaa `codex-ajanlasku`-käyttäjäasennusta, päivitä myös se uuden debin asentamisen jälkeen. Aja seuraava ilman sudoa:

```bash
(
  umask 022
  ajanlasku_kanava="$HOME/.local/share/ajanlaskut-ja-saa/paivitykset"
  /usr/bin/python3 /usr/share/ajanlaskut-ja-saa/packaging/build.py \
    --publish-channel "$ajanlasku_kanava" &&
  /usr/bin/python3 "$ajanlasku_kanava/update-upgrade.py" setup &&
  export PATH="$HOME/.local/bin:$PATH" &&
  codex-ajanlasku update &&
  codex-ajanlasku upgrade &&
  codex-ajanlasku status
)
```

Käytä samaa päivityskansiota, jonka `codex-ajanlasku status` ilmoittaa. Lopeta vanha ohjelma kokonaan ja käynnistä `codex-ajanlasku run`. Molemmat asennustavat käyttävät samoja asetuksia ja merkintöjä.

Paketti vaatii Python 3.10:n sekä PyQt6:n ja sen multimediaosan vähintään 6.8. APT tarkistaa riippuvuudet.

## Muutokset

- Digitaalinen, analoginen tai yhdistelmäkello jokaiselle kellolle.
- Oma diginumeroiden koko 80–140 % ja numeroväri, esikatselu ennen tallennusta.
- Oma tekstiväri kaikille kahdeksalle widgetille; teeman väriin voi palata.
- Taustakuvavalintojen luonnokset säilyvät sivua päivittäessä. Erillinen lukituskuva ja vaihtuvat kuvat kertovat Dia Wall 77 -vaatimuksen. Ilman lisäosaa GNOMEn lukitusnäyttö seuraa työpöydän taustaa.

## Tarkistus

159 yksikkötestiä ja eristetyt Qt-käyttöliittymätestit läpäistiin myös puretusta julkaisun lähdepaketista.
Päivitys 1.6.0 → 1.6.1 → 1.6.0 → 1.6.1 säilytti asetustiedoston tavut, värit, merkinnät ja muistutukset.

Lataa myös SHA256SUMS ja tarkista latauskansiosta:

```bash
sha256sum -c SHA256SUMS
```

SHA256: `5f3695fc082e350d64c13d01b9f597a74d99c7476d4e39273086a95ddd8a1d41`

[Lähdekoodi ja käyttöohje](https://github.com/Jakke77/Ajanlaskut-ja-Saa/tree/5925f484e99b07313ea03b7bd414ddc63cf727c5)

Tämä haara sisältää vain valmiin asennuspaketin ja sen ohjeet. Ohjelman lähdekoodi on yllä linkitetyssä muutoksessa.
