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

**Ubuntu-teemasta vanhaan versioon:** ennen palautusta versioon 1.4.0 tai
aiempaan valitse ja tallenna **Asetukset → Teema → Kupari tai Halla** sekä
**Ajanlaskuwidgetit → Kellon teema → Ajanlaskun oma tai Sovelluksen yhteinen**.
Vanhat versiot eivät tunnista Ubuntu-teeman tallennettuja valintoja.
Palautus säilyttää nykyiset merkinnät; älä korvaa `state.json`-tiedostoa vanhalla
varmuuskopiolla tätä varten.

## Paikallinen päivityskansio

### Uuden GitHub-version tuominen nykyiseen käyttäjäasennukseen

GitHubiin yhdistetty muutos tulee koneelle, kun uusi lähdepaketti julkaistaan
omaan päivityskansioon. Lataa repon **Code → Download ZIP** GitHubiin
kirjautuneena. Avaa pääte latauskansioon ja suorita:

```bash
(
  umask 022
  ajanlasku_kanava="$HOME/.local/share/ajanlaskut-ja-saa/paivitykset"
  ajanlasku_lahde="$(mktemp -d)" &&
  /usr/bin/python3 -m zipfile -e Ajanlaskut-ja-Saa-main.zip "$ajanlasku_lahde" &&
  /usr/bin/python3 "$ajanlasku_lahde/Ajanlaskut-ja-Saa-main/packaging/build.py" \
    --publish-channel "$ajanlasku_kanava" &&
  "$HOME/.local/bin/codex-ajanlasku" update &&
  "$HOME/.local/bin/codex-ajanlasku" upgrade &&
  "$HOME/.local/bin/codex-ajanlasku" status
)
```

Tämä olettaa, että nykyinen `codex-ajanlasku` on rekisteröity yllä olevaan
päivityskansioon. `status` näyttää käytössä olevan kansion. Vaihda tarvittaessa
`ajanlasku_kanava` vastaamaan sitä. Komento käyttää ladatun päähaaran versiota;
vanhasta `/usr/share/ajanlaskut-ja-saa`-kansiosta rakentaminen julkaisee edelleen
siellä olevan vanhan version.

Kun status näyttää uuden version, paina vanhan ohjelman vasemman valikon
alareunasta **Lopeta sovellus** ja käynnistä käyttäjäasennus:

```bash
"$HOME/.local/bin/codex-ajanlasku" run --page widgets
```

**Ikkunan × voi vain piilottaa pääikkunan.** Käynnissä oleva vanha ohjelma voi
muuten vastaanottaa uuden käynnistyskomennon ja näyttää edelleen vanhat valikot.
`"$HOME/.local/bin/codex-ajanlasku" run --version` näyttää levyversion;
kokonaan uusi käynnistys ottaa sen käyttöön.

Widgettikohtaiset teemat 1.6.0 tallentuvat valinnaiseen `widget_themes`-karttaan,
kellojen näyttötapa ja diginumeroiden oma koko `clock_displays`-karttaan.
Versio 1.5.0 lukee saman asetustiedoston ja käyttää aiempaa yhteistä teemaa ja
kelloteemaa; widgettikohtaiset valinnat eivät näy siinä. Digikellon koko käyttää
palautuksen jälkeen aiempaa yhteistä numerosäätöä. Uudet merkinnät säilyvät.

### Komennon käyttöönotto deb-asennuksesta

Deb-asennus tarjoaa `ajanlaskut-ja-saa`-komennon. `codex-ajanlasku` otetaan
käyttöön erikseen, kun paikallinen päivityskansio ja tarkistettu paketti on luotu.
Kun sovellus on asennettu `/usr/share/ajanlaskut-ja-saa`-kansioon, suorita ilman
sudoa:

```bash
ajanlasku_kanava="$HOME/.local/share/ajanlaskut-ja-saa/paivitykset"

/usr/bin/python3 /usr/share/ajanlaskut-ja-saa/packaging/build.py \
  --publish-channel "$ajanlasku_kanava" &&
/usr/bin/python3 "$ajanlasku_kanava/update-upgrade.py" setup &&
export PATH="$HOME/.local/bin:$PATH" &&
codex-ajanlasku update &&
codex-ajanlasku upgrade &&
codex-ajanlasku status
```

Rakentaminen tarvitsee `dpkg-deb`-työkalun ja ohjelman riippuvuudet järjestelmän
`/usr/bin/python3`:lle. Paketti testataan ennen päivityskansion julkaisua.
Testivirhe pysäyttää komentoketjun; tarkka syy jää kansion `qa-failures`-lokiin.

Tämä luo käyttäjäasennuksen **nykyisestä järjestelmään asennetusta versiosta**.
Uudemmat ohjelmaversiot pitää julkaista valittuun päivityskansioon erikseen.
`export` lisää komentopolun nykyiseen päätteeseen. Jatkossa `~/.local/bin` pitää
olla myös uuden pääteistunnon PATHissa; komennon voi aina ajaa täydellä polulla
`"$HOME/.local/bin/codex-ajanlasku"`.

Versiossa 1.4.0 GI-taustakuvatestin erillinen prosessi etsii ohjelmaa
työhakemistosta. Tämän version käyttöönotossa aja ensin
`cd /usr/share/ajanlaskut-ja-saa`, ja suorita yllä oleva ketju samassa päätteessä.
Korjattu testi löytää puretun paketin ohjelmakansion myös muualta käynnistettäessä.

### Aiempi konekohtainen julkaisukansio

Aiemmassa paikallisessa toimituksessa käytetty julkaisukansio oli:

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

Jos **tämä kansio ja sen `update-upgrade.py` sekä `latest.json` ovat olemassa**,
komennon voi rekisteröidä siitä:

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
