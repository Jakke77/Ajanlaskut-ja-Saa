# Oma päivityskomento · 1.2.1 ja uudemmat

## Veri Aika: 777 päivää ja nimiparit · 1.12.1

Ubuntu: lataa alla oleva deb-paketti. Windows: lataa ja pura
[Windows 1.12.1](https://github.com/Jakke77/Ajanlaskut-ja-Saa/releases/tag/windows-v1.12.1)
uuteen kansioon ja käytä uuden kansion käynnistintä; asetukset säilyvät omassa käyttäjäkansiossa.

Uudet valinnat: **sivuvalikko → Veri Aika**, **Ajanlaskuwidgetit → Näyttötapa →
Otavakello** ja **Asetukset → Teema → Veri Aika · Veriyö**. Viikko alkaa
26.6.2026 klo 01:07:07 Suomen aikaa ja toistuu seitsemän paikallisen päivän välein.
Vuodessa on nyt **777 päivää eli 111 viikkoa**. Vuosi 0002 alkaa
11.8.2028 klo 01:07:07. Päivä- ja viikkonumerot palaavat silloin ykköseen.
Kalenterissa, etusivulla ja widgetissä näkyy vuoden numero.

Vuoden jokaiselle päivälle on oma pysyvä nimipari. Valitse syntymäpäivä
**Nimikalenterit → Oma nimi** -sivulla. Widgetin **Päivän nimipari** on
valinnainen sisältökenttä; valinta löytyy Ajanlaskuwidgetit-sivulta.
Aiemmat merkinnät, aikarajat ja teemavalinnat säilyvät.
Kaksi tummaa taustakuvaa löytyvät Taustakuvat-sivulta.

Viides kuvaketeema ylittää vanhan käyttäjäpäivittimen 2000 tiedoston rajan.
Deb-asennus toimii suoraan. Käyttäjäasennuksessa päivitä myös päivityskansion
helper alla olevalla järjestelmäasennuksen käyttöönottoketjulla tai uuden
lähde-ZIPin mukana tulevalla `packaging/build.py --publish-channel` -komennolla.
Version 1.12.1 helper hyväksyy enintään 4096 tiedostoa säilyttäen tavumäärä- ja polkutarkistukset.

Jos sovellusvalikon kuvake avaa vanhan version, lopeta vanha prosessi ja avaa:

```bash
/usr/bin/ajanlaskut-ja-saa --page blood
/usr/bin/ajanlaskut-ja-saa --version
```

Versioksi tulee 1.12.1. Järjestelmäasennus ja `codex-ajanlasku` ovat edelleen
erillisiä asennuksia; katso alla oleva vanhan käyttäjäasennuksen päivitysohje.


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

## Valmiin deb-paketin asentaminen

Lataa [ajanlaskut-ja-saa_1.12.1_all.deb](https://github.com/Jakke77/Ajanlaskut-ja-Saa/raw/refs/heads/packages/v1.12.1/ajanlaskut-ja-saa_1.12.1_all.deb)
ja halutessasi tarkista sen SHA256SUMS samasta
[packages/v1.12.1-kansiosta](https://github.com/Jakke77/Ajanlaskut-ja-Saa/tree/packages/v1.12.1).
Yksityinen repo edellyttää GitHubiin kirjautumista. Avaa pääte latauskansioon:

```bash
sudo apt install ./ajanlaskut-ja-saa_1.12.1_all.deb
```

Tämä päivittää **järjestelmäasennuksen**, joka käynnistyy komennolla
`/usr/bin/ajanlaskut-ja-saa`. Jos käytät aiempaa `codex-ajanlasku`-käyttäjäasennusta,
päivitä myös se alla olevalla [deb-asennuksen käyttöönottoketjulla](#komennon-käyttöönotto-deb-asennuksesta).
Ketju rakentaa nyt 1.12.1-version päivitetystä `/usr/share/ajanlaskut-ja-saa`-kansiosta.
Sen jälkeen käytä `codex-ajanlasku run` -komentoa. Asennukset käyttävät samaa
asetustiedostoa, joten merkintöjä ei tarvitse siirtää.

Valitse ennen uuden version käynnistystä vanhasta ohjelmasta **Lopeta sovellus**.
Ubuntu tarvitsee paketin ilmoittamat PyQt6-riippuvuudet, vähintään version 6.8.

**Jos kuvakevalintoja ei näy:** versiot 1.6.x eivät sisällä niitä. Tarkista ensin
`/usr/bin/ajanlaskut-ja-saa --version` ja käyttäjäasennukselle
`codex-ajanlasku status` sekä `codex-ajanlasku run --version`.
Pelkkä deb-asennus ei vaihda `codex-ajanlasku`-käyttäjäasennuksen versiota;
aja myös alla oleva käyttöönottoketju, jos käynnistät sen kautta.
Sulje vanha ohjelma **Lopeta sovellus** -komennolla ja käynnistä sen jälkeen
uusi. Myös zipistä ajettu `python3 main.py` voi ohjata käynnistyksen jo avoinna
olevaan vanhaan ohjelmaan, koska molemmat käyttävät samaa asetustiedostoa.
Uuden ohjelman otsikossa lukee **Ajanlaskut ja Sää 1.12.1**.
Kuvaketoiminnot ovat **Asetukset → vieritä alas → Sovelluskuvakkeet**.

**Kuu ja nimikalenterit:** versiosta 1.10.0 lähtien uudet sivut ovat **Valo ja aurinko** sekä **Nimikalenterit**. Valitse syntymäpäivä nimihakuun tai avaa suomalainen kuukalenteri toiselta välilehdeltä. Kuukalenteri on selvästi merkitty laskennallinen tulkinta; Vaahtokuu kuuluu 13 kuukauden vuoteen.

**Sadekarttojen koko:** versio 1.9.1 avaa Forecan ja Ilmatieteen laitoksen kartat sisältöalueen kokoisina. Sivuston otsikot ja sivuvalikot eivät enää vie kartan tilaa. Kartan omat säätimet ja lähdemerkinnät säilyvät.

**Sadekartat ja tuntiennuste:** versiosta 1.9.0 lähtien valitse **Sää → Palvelu → Näkymä**. Forecalla ja Ilmatieteen laitoksella on oma sadekartta; Windyllä voi valita kartan tai kartattoman tuntiennusteen. Sama valinta on sääwidgetin oikean painikkeen valikossa.

**Windy-kartta:** versio 1.8.1 korjaa kartan näkyviin tullessa tapahtuvan latauksen ja uudelleenyrityksen. Päivitä myös pääikkunan kartta **Sää → Päivitä** -painikkeella tai kartan **Yritä uudelleen** -painikkeella.

**Ubuntu 26.10 Dark** löytyy versiosta 1.8.0: valitse se **Asetukset → Teema**
-valikosta ja tallenna. Taustakuvan ja kuvakkeiden automaattiset vaihdot ovat
erillisiä valintoja. Kuvakkeet voi ottaa heti käyttöön **Sovelluskuvakkeet**
-osion painikkeilla. [Uuden teeman käyttöönotto](README.md#ubuntu-2610-dark--versio-180).

Versio 1.8.0 sisältää myös **Käytä järjestelmän oletuskuvakkeita** -painikkeen
**Asetukset**- ja **Taustakuvat**-sivujen **Sovelluskuvakkeet**-osiossa.
Se valitsee järjestelmän oman oletuskuvaketeeman, palauttaa sovelluksen
tekemät sovelluskuvakekorjaukset ja poistaa kuvakkeiden automaattisen
teemanvaihdon käytöstä. Aiemman teeman varmuuskopiota ei tarvita.

**Uudesta Dark-teemasta vanhaan ohjelmaversioon:** ennen palautusta versioon
1.7.1 tai aiempaan valitse **Asetukset → Teema → Kupari, Halla tai Ubuntu**,
rastita **Käytä valittua teemaa kaikissa widgeteissä** ja tallenna. Näin myös
widgettien ja kellojen uudet teemavalinnat vaihtuvat vanhan version tuntemiksi.
Jos palaat versioon 1.4.0 tai aiempaan, valitse Kupari tai Halla.

## Eri versiot järjestelmä- ja käyttäjäasennuksessa

Jos `/usr/bin/ajanlaskut-ja-saa --version` näyttää esimerkiksi **1.8.1** mutta
`codex-ajanlasku run --version` näyttää **1.6.0**, deb on päivittänyt vain
järjestelmäasennuksen. Ubuntu 26.10 Dark puuttuu vanhasta käyttäjäasennuksesta.
Versiosta 1.8.2 lähtien on **Ohje → Tietoa sovelluksesta** -toiminnon, josta näet
käynnissä olevan ohjelman version ja asennuskansion.

Saat jo asennetun järjestelmäversion näkyviin näin:

1. Valitse nykyisestä ohjelmasta **Lopeta sovellus**. Ikkunan × voi vain piilottaa sen.
2. Aja `/usr/bin/ajanlaskut-ja-saa --page settings`.
3. Valitse **Asetukset → Ulkoasu ja työpöytä → Teema → Ubuntu 26.10 Dark** ja tallenna.

Päivitä myös käyttäjäasennus järjestelmään asennetusta versiosta alla olevalla
ketjulla. Se lukee nykyisen `codex-ajanlasku`-komennon päivityskansion, joten
myös oma erikseen valittu kansio säilyy. Aja ilman sudoa:

```bash
(
  set -eu
  umask 022
  ajanlasku_kanava="$(codex-ajanlasku status | /usr/bin/python3 -c 'import sys; p="Päivityskansio: "; c=next((r[len(p):].rstrip("\n") for r in sys.stdin if r.startswith(p)), ""); print(c) if c.startswith("/") else sys.exit("Päivityskansiota ei löytynyt. Tarkista codex-ajanlasku status.")')"
  /usr/bin/python3 /usr/share/ajanlaskut-ja-saa/packaging/build.py \
    --publish-channel "$ajanlasku_kanava" &&
  /usr/bin/python3 "$ajanlasku_kanava/update-upgrade.py" setup &&
  "$HOME/.local/bin/codex-ajanlasku" update &&
  "$HOME/.local/bin/codex-ajanlasku" upgrade &&
  "$HOME/.local/bin/codex-ajanlasku" run --version
)
```

Ketjun ensimmäinen rakentamisvaihe testaa paketin ja voi kestää useita minuutteja.
Jos jokin vaihe epäonnistuu, ketju pysähtyy. Kun lopun versionumero vastaa
järjestelmäasennusta, lopeta vanha ohjelma kokonaan ja avaa
`"$HOME/.local/bin/codex-ajanlasku" run --page settings`.
Kalenterimerkinnät säilyvät; älä poista asetuskansiota.

## Paikallinen päivityskansio

### Uuden GitHub-version tuominen nykyiseen käyttäjäasennukseen

GitHubiin yhdistetty muutos tulee koneelle, kun uusi lähdepaketti julkaistaan
omaan päivityskansioon. Lataa nimenomaan
[1.12.1-lähdepaketti](https://github.com/Jakke77/Ajanlaskut-ja-Saa/raw/refs/heads/packages/v1.12.1/Ajanlaskut-ja-Saa-1.12.1-lahdekoodi.zip)
GitHubiin kirjautuneena. Repon oletushaaran ZIP sisältää julkaistuja asennuspaketteja;
se ei ole sama tiedosto kuin lähdepaketti. Avaa pääte latauskansioon ja suorita:

```bash
(
  umask 022
  ajanlasku_kanava="$HOME/.local/share/ajanlaskut-ja-saa/paivitykset"
  ajanlasku_lahde="$(mktemp -d)" &&
  /usr/bin/python3 -m zipfile -e Ajanlaskut-ja-Saa-1.12.1-lahdekoodi.zip "$ajanlasku_lahde" &&
  /usr/bin/python3 "$ajanlasku_lahde/Ajanlaskut-ja-Saa/packaging/build.py" \
    --publish-channel "$ajanlasku_kanava" &&
  "$HOME/.local/bin/codex-ajanlasku" update &&
  "$HOME/.local/bin/codex-ajanlasku" upgrade &&
  "$HOME/.local/bin/codex-ajanlasku" status
)
```

Tämä olettaa, että nykyinen `codex-ajanlasku` on rekisteröity yllä olevaan
päivityskansioon. `status` näyttää käytössä olevan kansion. Vaihda tarvittaessa
`ajanlasku_kanava` vastaamaan sitä. Komento käyttää ladatun lähdepaketin versiota;
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

Widgettikohtaiset teemat 1.6.0 tallentuvat valinnaiseen `widget_themes`-karttaan.
Versio 1.6.1 lisää kellojen näyttötavan, diginumeroiden koon ja numerovärin
`clock_displays`-karttaan sekä kaikkien widgettien tekstivärit `widget_text_colors`-karttaan.
Versio 1.6.0 ohittaa uudet kentät ja käyttää aiempaa kellon ulkoasua.
Palautus ei poista uusia värivalintoja tai merkintöjä.
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
