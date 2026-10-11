# Yhteisen sovelluksen rakenne

## Tavoite ja rajat

Yksi paikallinen Ubuntu-sovellus, yhteinen käyttöliittymä ja erikseen näytettävät
työpöytäwidgetit. Nykyisten sovellusten omia tiedostoja ei muuteta. Ei pilvisynkkaa,
käyttäjätiliä tai uutta palvelinta. PyQt6 on jo käytössä lähdeprojekteissa ja
käyttäjän koneessa. Sään kuparinen ulkoasu on yhteisen teeman lähtökohta.

```text
                   Controller / yksi QApplication
                      │          │           │
               yhteinen State   Calendars    Weather + DailyWeather
                      │          │           │
                   MainWindow ──┴───────────┤
                      │                      │
                7 sovellusnäkymää      8 desktop-widgettiä
```

`State` hallitsee vain tämän sovelluksen asetuksia, merkintöjä, muistutuksia ja
ikkunapaikkoja. `Calendars` muuntaa saman todellisen päivän kolmelle ajanlaskulle.
Sääkerros tarjoaa kaikille ikkunoille samat ennusteet; yksittäinen widgetti ei
käynnistä erillistä verkkohakua tai vanhaa sovellusta.

## Tietomalli ja tapahtumat

Merkintöjen avaimet ovat todellisia `YYYY-MM-DD`-päiviä, eivät kuvitteellisen
kalenterin kuukauden numeroita. Näin kalenterin vaihto ei luo kahta eri tapahtumaa.
Muistutuksilla on tunniste, UTC-aika, teksti ja toimitusmerkintä. Asetukset
sisältävät yhteiset värit, fontin ja paikan sekä kahdeksan näkyvyysvalintaa.
Tallennus on atominen ja tiedostolla on vain käyttäjän luku-/kirjoitusoikeus.

Ohjaimen signaalit erottavat kellon tikityksen, asetusten muutoksen ja merkintöjen
muutoksen. Yhteisen teeman vaihto päivittyy sovelluksen näkymiin ja sitä seuraaviin
widgetteihin yhdellä asetuskokonaisuudella.
Varjoajan ja Tähtiajan aiemmat muunnossäännöt säilyvät; alkuperäisten sovellusten
käyttöliittymät eivät kuulu uuteen prosessiin.

`ClockRotation` käyttää monotonista aikaa ja vain kolmen ajanlaskun tunnisteita.
Ulkoasun tai sisällön muutos ei aloita vaihtoväliä uudelleen. Neljä kelloprofiilia
sisältävät riippumattomat kenttävalinnat; sama `clock_layout` ja `DesktopSurface`
piirtävät sekä työpöydän että tallentamattoman esikatselun. Kellon tai lisäkalenterien
asetukset säilyttävät sään nykyisen toiminnan. Kellosisällön ja kellon oman teeman
samanaikainen tallennus käyttää myös tätä rajattua päivityspolkua.

`almanac` tarjoaa välimuistitetut convertdate-muunnokset oikeille kalentereille
valitun siviilipäivän keskipäivällä. Se ei korvaa kuvitteellisia muunnossääntöjä,
merkintöjen tunnisteita tai muistutusaikoja. Persialainen laskenta on rajattu
1900–2100. Sovelluksen `vendor/` sisältää muuttamattoman convertdate 2.4.0:n ja
PyMeeus 0.5.12:n lähdekoodit ja lisenssit; järjestelmässä asennettuja vastaavia
kirjastoja voi käyttää niiden sijaan. Kalenterimuunnokset eivät käytä verkkoa.

## Widgettiteemat ja luonnosten tallennus · 1.6.0

Kaikilla kahdeksalla widgetillä on oma teemavalinta. Yhteinen kello ja kolme
erillistä kelloa käyttävät `PROFILE_KEYS`-tunnuksia; muut näkymät ovat tuntisää,
kolmen päivän Varjosää sekä kaksi kuukausiwidgettiä. `State.settings.widget_themes`
on valinnainen harva kartta widgetin tunnuksesta teemavalintaan. Sallittuja
valintoja ovat `shared`, `copper`, `frost` ja `ubuntu`; `calendar` hyväksytään
vain neljälle kellolle. Validoitu kartta tallentuu samassa atomisessa
asetuskokonaisuudessa muiden tietojen kanssa.

`widget_themes.widget_theme_selection` käyttää puuttuvalle kellon avaimelle
olemassa olevaa `time_theme`-valintaa ja muille widgeteille `shared`-valintaa.
`widget_theme` ratkaisee `shared`-valinnan yhteisestä `THEMES[theme]`-paletista,
`calendar`-valinnan näkyvän ajanlaskun `CALENDAR_THEMES`-paletista ja kiinteän
valinnan suoraan `THEMES`-paletista. `widget_theme_choices` tarjoaa samat
valinnat työpöytäwidgettien sivulle ja kellon esikatseluun. Ubuntu-paletin
kellot käyttävät `ubuntu_clock`-piirtäjää; sää- ja kuukausiwidgetit saavat sen värit.

Uudessa asennuksessa `time_theme` on `shared` ja kartta tyhjä, joten yhteinen
teema ulottuu kaikkiin widgetteihin. Vanhaa tiedostoa luettaessa tallennettu
`time_theme` säilyy; puuttuva arvo täydentyy `calendar`-valinnaksi ja puuttuva
kartta tyhjäksi. Lukeminen ei kirjoita käyttäjän tiedostoa. Erillinen `shared`-avain
voi ohittaa vanhan kellon `calendar`- tai `ubuntu`-fallbackin.

`WidgetsPage` ja `ClocksPage` pitävät tallentamattomat valinnat luonnoksina.
Teemakarttaa tallennettaessa pohjaksi kopioidaan viimeisin kartta ja vaihdetaan
vain luonnoksessa muokatut widgetin avaimet. Kelloprofiileissa yhdistetään vain
muokatut sisältökentät. Asetussignaalit päivittävät luonnoksen muokkaamattomat
valinnat, joten toisella sivulla tallennettu uudempi valinta säilyy.
Kellon esikatselu käyttää erillisiä teema-, ajanlasku- ja sisältöylikirjoituksia
muuttamatta tallennettua tilaa.

Asetussivun **Käytä valittua teemaa kaikissa widgeteissä** on nimenomainen
kaikkien teemavalintojen palautus yhteiseen teemaan. Tallennus tyhjentää kartan
ja asettaa `time_theme`-arvoksi `shared`; näkyvyys ja kellosisällöt säilyvät.
Yksittäisen widgetin teemavalinta ei kirjoita taustakuva-asetuksia. Yhteinen
sovellusteema noudattaa edelleen tallennettua teeman mukana vaihtuvan taustan valintaa.

`Controller.configure` vertaa muuttuneita asetuksia ja sääwidgetin todellista
palettia. Paletin muuttuessa `SharedWeather.apply_widget_theme` vaihtaa piirto-
ja painikevärit ja kutsuu `update`-piirtoa. Se säilyttää ennusteen, palveluvalinnan,
Windy-näkymän sekä sää- ja kellokierron ajastukset; verkkohakuja, karttalatauksia
tai ajastusten uudelleenkäynnistyksiä ei tehdä. Säägraafin lämpö-, sade- ja
tuulisarjojen semanttiset värit säilyvät.

## Sää, viat ja yksittäisinstanssi

Tuntisää käyttää taustatyöntekijää, päiväennuste Qt:n asynkronista verkkokerrosta.
Paikat ja tarjoajat on erotettu välimuistissa. Vanhentunut/puuttuva tunti ei
muutu tekaistuksi nollaksi; verkkovirheessä näytetään saatavilla oleva välimuisti
ja virhe. Hakuväli on oletuksena 77 minuuttia, mutta palvelujen omia HTTP- ja
uusintahakurajoja noudatetaan. Windy ladataan vasta karttanäkymää käytettäessä.

QLockFile estää kaksi kirjoittajaa samaan asetustiedostoon. Käyttäjäkohtainen
paikallissocket ohjaa toisen käynnistyksen ensimmäisen prosessin oikeaan näkymään.
Vanhojen kalenterien tuonti on kertaluonteinen, paikallinen ja lukevan kopioinnin
periaatteella toteutettu. Tallennusvirheessä aiempi tila säilyy muistissa ja levyllä.

## Työpöytäikkunoiden järjestys ja koko

`windowing.WindowLayers` käyttää itsenäisiä NORMAL-ikkunoita eikä Qt.Tool-
ikkunoita. GNOME piti UTILITY-/apuikkunat saman sovelluksen pääikkunan päällä
myös BELOW-tilassa. Tämä toistettiin XWaylandissa: pelkkä UTILITY-tyypin
irrottaminen transient-parentista ei korjannut kerrosjärjestystä; NORMAL korjasi.
X11:n SKIP_TASKBAR ja SKIP_PAGER pyydetään rajatulla EWMH-viestillä, joten
widgetit eivät lisää omia tehtäväpalkki- tai ikkunanvaihtajan merkintöjä.
Lisäriippuvuutta ei asenneta. Muilla Qt-alustoilla viestiä ei lähetetä.

Käyttäjän on_top säilyy, mutta näkyvä, ei-minimoitu pääikkuna tai QDialog antaa
widgeteille väliaikaisesti BELOW-tason. QWindow.setFlags vaihtaa vihjeet
paikallaan; QWidget.setWindowFlagsin piilotus rikkoisi widgetin päällä olevan
valintaikkunan. Siirtymät ovat tapahtumapohjaisia, eivät sekuntiajastettuja.
Pääikkunan sivuohjaus ei enää pura suurennettua tilaa.

`WidgetFrame` käsittelee kahdeksan reunaa, osoittimen ja hiiren tartunnan.
Hiiren liike muuttaa vain kyseisen pinnan kokoa; vapautus tallentaa koon ja
paikan yhtenä atomisena State-kirjoituksena. Esc peruu ennen tallennusta.
Minimi estää käyttöliittymän kutistamisen käyttökelvottomaksi. Fontit piirretään
yhtenäisellä mittakaavalla ilman vaakasuunnan venymistä, ja kalenterin ruudukko,
säägraafi ja kartta käyttävät lisätilan. Esikatselut eivät ole resizable desktop-
ikkunoita. Valinnainen widget_sizes säilyttää vanhan geometria- ja tietomallin
taaksepäin yhteensopivana; siitä ei tehdä käynnistyksessä tilamigraatiota.

Viralliset rajapinnat: [Qt:n ikkunatyypit](https://doc.qt.io/qt-6/qt.html#WindowType-enum),
[EWMH:n ikkuna- ja tilavihjeet](https://specifications.freedesktop.org/wm/latest/ar01s05.html).

## Paikallisen päivityksen toteutus

`packaging/update_upgrade.py` on itsenäinen stdlib-komento. Sen julkaistu kopio
`update-upgrade.py` ja `latest.json` ovat käyttäjän valitsemassa Codexin
tuloshakemistossa. Komento ei käytä verkkoa, aptia tai sudoa.
`update` tarkistaa ja tallentaa ehdokasjulkaisun; `upgrade` tarkistaa sen uudelleen,
purkaa rajatun ZIPin staging-hakemistoon ja kokeilee ohjelman riippuvuuksien
latautumista erillisessä Python-prosessissa. Vain eheä paketti otetaan käyttöön.

Versiot ja tiedostokohtaiset tarkisteet ovat ohjelman omassa `program/releases/`
hakemistossa, erillään State-, sää- ja taustakuvadatasta. `current` vaihtuu
atomisena linkkinä, ja asennustieto sekä käyttäjäkäynnistimet kirjoitetaan
väliaikaistiedostosta. Virheessä kohde, asennustieto ja käynnistimet palautetaan.
fcntl-lukko estää kaksi samanaikaista päivittäjää. Käynnissä olevaa sovellusta
ei lopeteta automaattisesti; uusi versio vaatii koko sovelluksen uudelleenkäynnistyksen.
`startup.launcher_root` käyttää käyttäjäasennuksessa vakaata `current`-polkua.
Kirjautumiskäynnistystä ei oteta käyttöön päivityksen vuoksi.

`rollback` vaihtaa edellisen tarkistetun ohjelmaversion aktiiviseksi, mutta ei
palauta käyttäjädataa. Näin päivityksen jälkeen kirjoitetut muistiinpanot säilyvät.
Paketin paikallinen tarkiste on eheyden tarkistus, ei ulkoisen julkaisijan todennus.
Kanavaa päivittää vain kehittäjän `build.py --publish-channel`, joka ajaa oikean
ZIPin eristetyt yksikkö- ja Qt-testit ennen latest.jsonin vaihtoa. Ohje: `UPDATES.md`.

## Valinnat ja jatkossa arvioitavat asiat

Taustakuvakirjasto lukee paketin gallerian, versionoidun paikallisen teema-repon
ja käyttäjän tuonnit. `WallpaperManager` erottaa tiedostojen pysyvät kopiot,
GNOME-tuen havaitsemisen ja taustakuva-asetusten kirjoituksen. Kuvan kelpoisuus,
asetusten arvorajat ja kirjoitusoikeudet tarkistetaan ennen muutosta. Edellisen
valinnan varmuuskopio tallennetaan ennen ensimmäistä järjestelmäkirjoitusta.
Virheessä jo kirjoitetut asetukset palautetaan; palautuksen epäonnistuminen
näytetään. Varmuuskopiolle on sallittujen taustakuva-avainten lista, jotta siitä
ei voi palauttaa lukituksen tai todennuksen asetuksia.

Dia Wall 77:n käytössäolo tarkistetaan GNOME Shellin D-Bus-rajapinnasta. Sen
työpöytä- ja lukituskanavat pidetään erillään, mukaan lukien omat diaesitykset.
Gio-sovitin käyttää asennetun skeeman tyyppejä ja delay/apply-tallennusta.
Järjestelmäkirjoitus tapahtuu nimenomaisesta taustakuvapainikkeesta tai
tallennetusta yhteisen teeman vaihdosta, jos wallpaper_follow_theme on valittu
(oletus true). Kohde on oletuksena desktop; lock/both vaatii erillisen valinnan.
WallpaperLibrary.for_theme valitsee paketin versionoidun oletuskuvan eikä
riippuvuutta mahdollisesti siirretystä teema-reposta. Nykyinen kuva tai diaesitys
säilyy keep-valinnassa. Käynnistys, fonttimuutos, sama teema, kellojen kierto
ja pelkkä gallerian valinta eivät kirjoita tausta-asetuksia.

Sama ThemeWallpaperOptions-lomake palvelee asetussivua ja taustagalleriaa.
Teemaehdokas validoidaan ensin. WallpaperManager.apply tallentaa palautustiedot,
kirjoittaa ja tarkistaa taustan, ja vasta sitten kutsuu State-commitia.
Jos app-asetusten tallennus epäonnistuu, taustan edellinen asetuskokonaisuus
palautetaan; jos alustakirjoitus epäonnistuu, Statea ei muuteta. Manuaalisen
taustavalinnan asetukset käyttävät samaa yhteistä palautuspolkua.
Qt-testien alustasovitin on muistissa; oikean Gio-rajapinnan testi ajetaan erillisessä
prosessissa `GSETTINGS_BACKEND=memory`-asetuksella, ei käyttäjän dconf-asetuksilla.

Qt tarjoaa aidot erilliset läpikuultavat työpöytäikkunat ja yhtenäisen natiivin
lomakekäyttöliittymän. Vastineeksi WebEngine-kartta lisää valinnaisen riippuvuuden;
ilman sitä kartasta pääsee selaimeen. GNOME/Waylandissa käytetään XWaylandia
läpinäkyvien desktop-ikkunoiden yhteensopivuuden vuoksi.

JSON pitää paikallisen pienen kalenterin helposti varmuuskopioitavana. Jos mukaan
tulee suuri määrä tapahtumia, toistuvia muistutuksia tai pilvisynkka, arvioidaan
SQLite, versionoidut tuonnit ja ristiriitojen ratkaisu uudelleen. Foreca-sovitin
lukee julkista sivua ja voi muuttua; Yr ja FMI ovat vaihtoehtoisia lähteitä.
