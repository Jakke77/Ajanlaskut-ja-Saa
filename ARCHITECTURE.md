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
                10 sovellusnäkymää     9 desktop-widgettiä
```

`State` hallitsee vain tämän sovelluksen asetuksia, merkintöjä, muistutuksia ja
ikkunapaikkoja. `Calendars` muuntaa saman todellisen päivän neljälle ajanlaskulle.
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

`ClockRotation` käyttää monotonista aikaa ja neljän ajanlaskun tunnisteita.
Ulkoasun tai sisällön muutos ei aloita vaihtoväliä uudelleen. Viisi kelloprofiilia
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

## Kuu, nimiparit ja päivän valo · 1.10.0

`astronomy` käyttää samaa PyMeeus-lähdekirjastoa. TT-ephemeridit muunnetaan
UTC-hetkiksi; paikallisen päivän rajat otetaan IANA-aikavyöhykkeestä.
Nousu-/laskuhaut käyttävät interpoloituja tuntikoordinaatteja, todellisen
UTC-hetken tähtiaikaa, Kuun topokeskistä parallaksia, yläreunaa ja vakioitua
refraktiota. Viiden minuutin välin molemmat ääriarvot tarkennetaan ennen
horisontin ylitysten hakua. Päivät voivat kestää 23, 24 tai 25 tuntia, eikä
vain nousun tai laskun puuttumista tulkita koko päivän kaamokseksi.
Kellot käyttävät samaa minuuttivälimuistia, valitut päivät paikallista keskipäivää.

`namedays` lukee versionoidun `assets/calendar-names.json`-nimilistan.
Varjoajan 390 ja Tähtiajan 510 nimiparia toistuvat omassa kuukauden/päivän
kohdassaan. Syntymäpäivähaku jatkaa nimikiertoa modulo-laskulla taaksepäin;
se ei muuta vuoden yksi rajaa, ajanlaskujen päiväyksiä tai merkintöjen avaimia.

`finnish_calendar` on erillinen, selvästi nimetty moderni tulkinta Katajalan
kuvauksesta. Joulukuu sisältää talvipäivänseisauksen, ja 13 kuunkierron vuosi
saa Vaahtokuun helmikuun jälkeen. Uudetkuut määrittävät Helsingin siviilipäivät.
PyMeeusin vaihehaun siemenet otetaan alle kuunkierron välein, jotta lähin
edellinen uusikuu ei jää etsimättä vuosirajan lähellä. Tätä ei lisätä
Varjoajan tai Tähtiajan muunnossääntöihin.

`celestial_ui` laskee päivä- ja kuukausitaulukot keskeytettävässä QThreadissä.
Tulokset sisältävät päivä-/paikka-/aikavyöhykeavaimen ja vanhat vastaukset
hylätään. QObject-slotit katkaisevat jonossa olevat vastaukset vastaanottajan
tuhoutuessa; sammutus keskeyttää ja odottaa vain omia työntekijöitä.
Nimihaku ei kirjoita syntymäpäivää asetuksiin. Suomalaisen kalenterin merkinnät
avaavat yhteisen NoteDialogin ja käyttävät olemassa olevia siviilipäivän avaimia.

## Widgettiteemat ja luonnosten tallennus · 1.6.0–1.6.1

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
kellot käyttävät oletuksena `ubuntu_clock`-piirtäjää; sää- ja kuukausiwidgetit saavat sen värit.

Versiossa 1.6.1 valinnainen `clock_displays` on neljän kellon harva kartta. Osittaisen valinnan
`mode` on `theme`, `digital`, `analog` tai `both`; `digit_scale` on oma
digitaalisten numeroiden koko 80–140 %. `digit_color` on valinnainen `#RRGGBB`-väri. Puuttuva näyttötapa käyttää teeman
oletusta (Ubuntu: molemmat, muut: digitaalinen), ja puuttuva koko seuraa yhteistä
`widget_clock_scale`-asetusta. `clock_display` ratkaisee samat valinnat
työpöydälle ja esikatselulle. Näyttötapa on teemasta riippumaton; pelkkä
analoginen kello jättää digiajan piirtämättä. Kuparin ja Hallan kellotauluissa
ei piirretä Ubuntun tunnusta. Vanha tiedosto täydentyy vain muistissa.

`widget_text_colors` on kahdeksan widgetin valinnainen harva `#RRGGBB`-värikartta.
Puuttuva avain käyttää teeman värejä. `widget_theme` kopioi valitun paletin
`text`- ja `muted`-värit muuttamatta yhteisiä palettiolioita. Korostukset ja
sääsuureiden värit säilyvät. Kellon `digit_color` ohittaa widgetin tekstivärin;
esikatselun täydellinen luonnos ohittaa tallennetut kellovalinnat.
Värikartan muutokset kulkevat kevyttä ulkoasun päivityspolkua, joka ei hae säätä.

Uudessa asennuksessa `time_theme` on `shared` ja kartta tyhjä, joten yhteinen
teema ulottuu kaikkiin widgetteihin. Vanhaa tiedostoa luettaessa tallennettu
`time_theme` säilyy; puuttuva arvo täydentyy `calendar`-valinnaksi ja puuttuva
kartta tyhjäksi. Lukeminen ei kirjoita käyttäjän tiedostoa. Erillinen `shared`-avain
voi ohittaa vanhan kellon `calendar`- tai `ubuntu`-fallbackin.

`WidgetsPage` ja `ClocksPage` pitävät tallentamattomat valinnat luonnoksina.
Teemakarttaa tallennettaessa pohjaksi kopioidaan viimeisin kartta ja vaihdetaan
vain luonnoksessa muokatut widgetin avaimet. Kelloprofiileissa yhdistetään vain
muokatut sisältökentät. Näyttötapakartassakin
yhdistetään vain muokatut kentät, jotta toisen tallennuksen uusi koko säilyy
näyttötapaa vaihdettaessa ja yhteiseen kokoon palaaminen voi poistaa oman koon.
Signaalit päivittävät luonnoksen muokkaamattomat
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

## Veri Aika ja Otava · 1.12.0

`blood_time` erottaa paikallisen kalenteripäivän UTC-kestosta: alku on
26.6.2026 klo 01:07:07 Europe/Helsinki, ja rajat rakennetaan paikallisista
päivämääristä. Viikon todellinen kesto voi olla 167 tai 169 tuntia kesäajan
vaihtuessa. Viikkolaskuri jatkuu keskeytyksettä vuosipäivien yli.

`otava` sisältää seitsemän BSC5-luettelon tähden J2000-paikat ja ominaisliikkeet.
PyMeeus laskee prekession ja keskimääräisen tähtiajan; paikallinen horisontti
on Oulu 65.0121 N, 25.4651 E. Koordinaatit lasketaan geometrisesti ilman
refraktiota. Kiinteä pohjoiseen taivaannapaan keskitetty stereografinen
projektio säilyttää liikkeen ja suhteellisen muodon. `otava_ui.paint_otava`
piirtää saman asennon etusivulle, Veri Ajan kalenteriin ja valinnaiseen kellokenttään.

`ubuntu_clock` käyttää saman luettelon staattista muotoa erillisessä
`style='otava'`-tilassa sekuntiviisarina. Se ei sekoita sekuntikulmaa taivaan
asentoon. `VeriPage` selaa viikkoja muuttamatta reaaliaikaisen taivaskuvan aikaa.

## Veri Ajan 777 päivän vuosi ja nimet · 1.12.1

`blood_time` jakaa paikallisen ordinal-luvun 777 päivän jaksoihin. Vuodessa
on täsmälleen 111 seitsemän päivän viikkoa, joten vuoden raja on myös viikon
raja. `next_year()` laskee seuraavan paikallisen 01:07:07-rajan päivämääristä,
ei 777×24 tunnista. Aiempi jatkuva viikkonumero säilyy mallissa, mutta
käyttöliittymä näyttää vuoden sisäisen viikon ja vuoden numeron.

`blood_names` lukee staattisen, validoidun 777 nimiparin luettelon. Päivät
ovat 1-pohjaisia; syntymäpäivähaku sovittaa myös ennen alkua olevat päivät
modulo 777. `NamePair` on yhteinen aiempien nimikalenterien kanssa.
VeriPage ja NamesPage näyttävät nimet; etusivu ja kellon `nameday`-kenttä
käyttävät saman muunnetun Veri-päivän nimiparia. Haku ei kirjoita asetuksia.
