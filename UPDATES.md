# Oma päivityskomento · 1.2.1 ja uudemmat

Tämä päivittää vain **Ajanlaskut ja Sää** -sovelluksen käyttäjäasennuksen.
Se ei päivitä Codexia tai Ubuntua, eikä käytä aptia, sudoa tai verkkopalvelua.

## Päivittäinen käyttö

```bash
codex-ajanlasku update && codex-ajanlasku upgrade
```

`update` tarkistaa paikallisen julkaisuluettelon ja ZIP-paketin tarkisteen.
`upgrade` tarkistaa paketin uudelleen, purkaa sen erilliseen hakemistoon,
tarkistaa riippuvuudet ja vaihtaa ohjelman käynnistyskohteen uuteen versioon.
Jos versio on jo käytössä, mitään ei asenneta uudelleen.

**Päivityksen jälkeen valitse ohjelmasta Lopeta sovellus**, ja avaa se uudelleen:

```bash
codex-ajanlasku run
```

Pääikkunan sulkeminen tai widgetin × ei välttämättä lopeta koko sovellusta.
Päivitys ei katkaise käynnissä olevaa ohjelmaa tai tallenna sen puolesta.
Uusi versio tulee käyttöön seuraavassa kokonaan uudessa käynnistyksessä.

Muut komennot:

```bash
codex-ajanlasku status      # asennettu ja viimeksi tarkistettu versio
codex-ajanlasku rollback    # edellinen ohjelmaversio takaisin
codex-ajanlasku run --page clocks
codex-ajanlasku run --widgets-only
```

Sulje ja avaa koko sovellus uudelleen myös palautuksen jälkeen. Palautus vaihtaa
vain ohjelmaversion: **uusia kalenterimerkintöjä ei palauteta taaksepäin**.
Ensimmäisessä täysin uudessa asennuksessa ei vielä ole edellistä versiota.

## Paikallinen päivityskansio

Tämän koneen julkaisukansio on:

```text
/home/jakke77/Documents/Codex/2026-10-05/t/outputs/Ajanlaskut-ja-Saa
```

Sen juureen tulevat `update-upgrade.py` ja `latest.json`. Tarkistetut paketit,
niiden SHA256SUMS ja QA.log jäävät version mukaan nimettyihin `paketit/`-kansioihin.
Vanhoja toimituspaketteja tai taustakuvia ei poisteta.

Komento löytää **vain tähän kansioon julkaistut versiot**. Se ei etsi uusia
versioita GitHubista eikä tee uutta ohjelmaversiota lähdekoodin muutoksista.
Siksi `ajan tasalla` tarkoittaa ajan tasalla tämän paikallisen kanavan kanssa.
Säätiedot päivittyvät erikseen sovelluksen omilla asetuksilla.

Kertaluonteinen komennon rekisteröinti, jos se puuttuu:

```bash
python3 /home/jakke77/Documents/Codex/2026-10-05/t/outputs/Ajanlaskut-ja-Saa/update-upgrade.py setup
```

Komento asentuu käyttäjän `~/.local/bin`-hakemistoon, jonka pitää olla PATHissa.
Tiedostoa voi käyttää myös suoraan: `python3 …/update-upgrade.py update` ja
`python3 …/update-upgrade.py upgrade`. Näissä `…` korvataan yllä olevalla koko polulla.

## Mikä säilyy?

Ohjelmaversiot ovat erillään käyttäjän tiedoista:

- Ohjelma: `~/.local/share/ajanlaskut-ja-saa/program/releases/`.
- Aktiivinen versio: saman hakemiston `current`-linkki ja `installation.json`.
- Asetukset ja merkinnät: `~/.local/share/ajanlaskut-ja-saa/state.json`, ennallaan.
- Käytössä olevat taustakuvat, säävälimuistit ja teema-repo: ennallaan.
- Ennen version vaihtoa otettu asetusten ja käynnistinten kopio: `program/backups/`.

Ohjelman valikkokäynnistin ja oma `ajanlaskut-ja-saa`-komento ohjataan aktiiviseen
käyttäjäasennukseen. Alkuperäinen käynnistin varmuuskopioidaan. Mahdollinen
kirjautumiskäynnistin säilyttää päällä/pois-valintansa; puuttuvaa ei luoda.
Lähdekansiota `/home/jakke77/Ohjelmat/Ajanlaskut-ja-Saa` ei korvata.
Vanhaa järjestelmään asennettua deb-versiota ei poisteta eikä apt-lähteitä muuteta.
Käyttäjäasennuksen käynnistimet ovat ensisijaisia. Älä käytä vanhan version
absoluuttista `/usr/bin/ajanlaskut-ja-saa`-komentoa tämän asennuksen avaamiseen.

Puuttuva riippuvuus, muuttunut tarkiste, muuttunut julkaisutieto tai vioittunut
ohjelmakansio keskeyttää asennuksen. Muokattuja ohjelmatiedostoja ei korvata
hiljaa. Versionvaihdon virheessä aiempi käynnistyskohde ja käynnistimet palautetaan.
Samanaikaiset päivitykset estetään lukolla. `rollback` tarkistaa edellisen version
ennen käyttöönottoa ja voi auttaa myös aktiivisen version tiedostojen vaurioituessa.

SHA256 on paikallisen paketin eheystarkistus, **ei digitaalinen allekirjoitus**.
Päivityskansion kirjoittajiin täytyy luottaa. Älä julkaise sinne tuntematonta koodia.
Varmuuskopiot sisältävät yksityisiä merkintöjä ja kuuluvat vain omalle käyttäjälle.
Niitä ei pakata ohjelman julkaisuihin. Päivitys ei muuta taustoja, lukituksen
turva-asetuksia, kalentereita tai widgettien näkyvyyttä.

## Uuden version julkaiseminen paikallisesti

Kehittäjä muuttaa lähdekoodia ja kasvattaa `asaa/__init__.py`-tiedoston VERSIONia.
Samaa versionumeroa ei saa julkaista uudelleen eri sisältöisenä.
Lähdekansiossa suoritetaan:

```bash
python3 packaging/build.py --publish-channel /home/jakke77/Documents/Codex/2026-10-05/t/outputs/Ajanlaskut-ja-Saa
```

Julkaisutarkistus:

1. Rakenna ZIP ja deb ilman käyttäjän tietoja tai työdataa.
2. Pura oikea ZIP erilliseen hakemistoon ja tarkista sen versionumero.
3. Aja puretun paketin kaikki yksikkötestit ja Qt-toimintatesti ilman verkkohakuja
   ja oikeita taustakuva-/lukitusmuutoksia. Testivirhe ei vaihda julkaisuluetteloa.
4. Säilytä onnistunut paketti ja QA.log muuttumattomana version mukaan.
5. Kirjoita tarkisteet sisältävä `latest.json` vasta onnistuneiden tarkistusten jälkeen.
6. Tarkista käyttäjäasennus omilla update-, upgrade- ja status-komennoilla.
   Käynnistä koko ohjelma uudelleen ja tarkista widgetit sekä merkintöjen säilyminen.
7. Jos uusi ohjelma ei toimi, käytä rollbackia ja avaa ohjelma uudelleen.
   Älä palauta state.json-varmuuskopiota uuden merkinnän yli.

Tämä on paikallinen julkaisu, ei GitHub-julkaisu tai apt-pakettivarasto.
Automaattista ajastettua päivitystä tai seurantaa ei ole otettu käyttöön.
