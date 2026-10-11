# Ajanlaskut ja Sää 1.6.2 — valmis deb-paketti

[Lataa ajanlaskut-ja-saa_1.6.2_all.deb](https://github.com/Jakke77/Ajanlaskut-ja-Saa/raw/refs/heads/packages/v1.6.2/ajanlaskut-ja-saa_1.6.2_all.deb)

Avaa latauslinkki GitHubiin kirjautuneena. Tiedoston **Download raw file** lataa myös paketin.

Asenna latauskansiosta:

```bash
sudo apt install ./ajanlaskut-ja-saa_1.6.2_all.deb
```

Jos käytät aiempaa `codex-ajanlasku`-käyttäjäasennusta, päivitä myös se uuden debin asentamisen jälkeen. Aja ilman sudoa:

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

Käytä samaa päivityskansiota, jonka `codex-ajanlasku status` ilmoittaa.

**Valitse vanhasta ohjelmasta Lopeta sovellus** ja käynnistä `codex-ajanlasku run`. Ikkunan × voi vain piilottaa vanhan ohjelman. Jos käytät pelkkää järjestelmäasennusta, käynnistys on `/usr/bin/ajanlaskut-ja-saa`. Molemmat asennustavat käyttävät samoja asetuksia ja merkintöjä.

Paketti tarvitsee Python 3.10:n sekä PyQt6:n ja sen multimediaosan vähintään 6.8. APT tarkistaa riippuvuudet.

## Korjaus 1.6.2:ssa

Taustakuvan toimintojen onnistumis- ja virheviestit näkyvät painikkeiden vieressä. Ne jäivät aiemmin sivun alareunaan ja näyttivät siltä, ettei painaminen tehnyt mitään.

**Aseta Ubuntu-teeman tausta** (tai Kupari/Halla) asettaa sovelluksen nykyisen teeman kuvan. **Työpöydän taustaksi** asettaa galleriassa valitun kuvan.

Erillinen lukitusnäytön kuva ja vaihtuvat kuvat vaativat käytössä olevan **Dia Wall 77** -lisäosan. Ilman sitä GNOMEn lukitusnäyttö seuraa työpöydän taustaa. Puuttuva tuki kerrotaan valikoissa.

Mukana ovat myös 1.6.1:n digi-, analogi- ja yhdistelmäkellot, omat diginumeroiden koot ja värit sekä tekstivärit kaikille kahdeksalle widgetille.

## Tarkistus

159 yksikkötestiä ja eristetyt Qt-käyttöliittymätestit läpäistiin myös puretusta julkaisun lähdepaketista.
Onnistumis- ja virhepalaute pysyy näkyvissä 1440×800-ikkunassa ilman lisävieritystä.
Oikea päivitys 1.6.1 → 1.6.2 → palautus 1.6.1 → 1.6.2 säilytti asetustiedoston tavut, värit, merkinnät ja muistutukset.

Lataa myös SHA256SUMS ja tarkista samasta latauskansiosta:

```bash
sha256sum -c SHA256SUMS
```

SHA256: `e6117e4da3f90f886c52312fc9d0cd9ac88af6e23b1a06dc422251de706951dd`

[Lähdekoodi ja käyttöohje](https://github.com/Jakke77/Ajanlaskut-ja-Saa/tree/e58a508a02b2b3f4844fa226dcb8e128956a82bf)

Tämä haara sisältää vain asennuspaketin, tarkisteen ja ohjeen.
