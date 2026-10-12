# Tarkistukset

## Ubuntu 26.10 Dark ja järjestelmän oletuskuvakkeet · 12.10.2026 · 1.8.0

- 212 yksikkö- ja käyttöliittymätestiä läpäistiin. Näihin sisältyvät uuden
  yhteisen teeman, widgettikohtaisten valintojen, vanhan kellovalinnan,
  vapaaehtoisen kuvakevaihdon ja palautuksen tarkistukset.
- 12 todellisen Qt-käyttöliittymän testiä tarkistaa myös uuden
  **Käytä järjestelmän oletuskuvakkeita** -painikkeen molemmilla sivuilla.
  Oletus luetaan koneen asentamasta GNOME-asetuksesta. Toiminto säilyttää
  widgettien teeman ja taustakuvan, poistaa kuvakkeiden seurannan ja palauttaa
  sovelluksen tekemät käynnistinkuvakekorjaukset. Levy- ja työpöytävirheiden
  palautus sekä käynnistinten palautuksen osittaisen onnistumisen palaute testataan.
- Neljän kuvaketeeman erillinen asennin läpäisi 50 testiä. Kussakin teemassa
  on 423 validia SVG:tä. Uuden teeman kaikki 97 erilaista kuvaa renderöitiin,
  ja esikatselu tarkistettiin. Vanhat kolme kuvaketeemaa säilyvät muuttumattomina.
- Paletin värilähde on Ubuntun virallinen brändisivu. Valkoinen, lämmin harmaa
  ja oranssi teksti saavuttavat vähintään 4,5:1-kontrastin mustalla ja tummalla
  munakoison sävyisellä pinnalla.
- Taustakuva dekoodattiin kokonaan: 1672 × 941. Sovelluksen ja teema-repon
  alkuperäiset PNG:t ja luontikuvaukset ovat tavuntarkasti samat. Erillisen
  teemapaketin 24 widgettikehysluonnosta validoitiin.
- Paikallisen päivityskanavan Qt-hyväksyntätestille sallitaan nyt kymmenen
  minuuttia, jotta kaikkien teemojen, fonttien ja kellonäyttöjen renderöinti
  ehtii valmistua myös hitaassa ympäristössä. Epäonnistunut testi estää julkaisun.

## Taustakuvatoimintojen palaute 1.6.2

- Videolla työpöydän taustakuva vaihtui, mutta toiminnon kuittaus jäi
  vieritettävän sivun alareunaan. Kuittaus on siirretty painikkeiden lähelle.
- Käyttöliittymätesti tarkistaa toiminnon onnistumis- ja virheviestin näkyvyyden
  sekä nykyisen teeman kuvan asettamisen erillään gallerian valinnasta.
- Paketti käyttää samaa asetusrakennetta ja riippuvuuksia kuin 1.6.1.

## Kellon näyttötapa ja widgettien tekstivärit 1.6.1

- 159 yksikkötestiä läpäistiin; 25 uutta kellon näyttötavan ja värien testiä.

- Kellojen näyttötapa, oma diginumeroiden koko ja väri sekä kahdeksan widgetin
  tekstivärikartta validoidaan ja tallennetaan atomisesti. Puuttuvat valinnat
  säilyttävät aiemman ulkoasun; vanhan tiedoston lukeminen ei kirjoita levyyn.
- Oikeiden Qt-sivujen luonnokset, esikatselu, tallennus, eri sivujen samanaikaiset
  muokkaukset ja levyvirheen jälkeinen uudelleenyritys tarkistetaan. Digitaalinen,
  analoginen ja yhdistelmäkello toimivat kaikissa teemoissa. Todellinen digiajan
  fonttikoko kasvaa 80–140 % sekä erillisessä digissä että kellotaulun sisällä.
- Kolmen fontin, ajanlaskun ja näyttötavan tekstit pysyvät rajoissa myös
  sekuntien piilotuksen ja nollan prosentin taustan kanssa.
- Taustakuvien oikeat hiirellä avatut alasvetovalikot tarkistetaan ilman Diaa
  ja Dia-tuen kanssa. Tallentamattomat valinnat säilyvät sivun vaihdossa ja
  muiden asetusten muutoksissa. GNOMEn erillisen lukituskuvan rajoitusta ei ohiteta.
- Pelkkä ulkoasun muutos säilyttää sääpalvelun, ennusteen, kartan, ajastimet,
  kalenterit ja kierron määräajan. Käyttäjän dataa tai oikeaa GNOME-istuntoa
  ei muuteta. Julkaisupaketti testataan uudelleen puretusta lähde-ZIPistä.

## Widgettikohtaiset teemat 1.6.0

- 134 yksikkötestiä läpäistiin. Uudet 13 testiä kattavat harvan teemakartan,
  vanhojen kelloteemojen säilymisen, uuden asennuksen yhteisen oletusteeman,
  widgettikohtaisen valinnan, paletin ja virheellisten valintojen atomisen hylkäyksen.
- Eristetty Qt-toimintatesti käyttää oikeita Työpöytäwidgetit-,
  Ajanlaskuwidgetit- ja Asetukset-sivuja. Kaikilla kahdeksalla widgetillä on oma
  teemavalinta. Tallentamaton luonnos ei muuta työpöytää; tallennus säilyy
  asetustiedoston uudelleenluvussa. Yhteisen teeman seuraajat vaihtuvat,
  erikseen valitut paletit säilyvät ja Käytä valittua teemaa kaikissa widgeteissä
  palauttaa kaikki seuraamaan yhteistä teemaa.
- Eri sivujen keskeneräiset teema- ja sisältövalinnat yhdistetään uusimpiin
  asetuksiin vain muokattujen avainten ja kenttien osalta. Pakotettu levykirjoitusvirhe
  jättää aiemman tiedoston, asetukset ja näkyvän sääpaletin ennalleen.
- Pelkkä teemavalinta, yhteisen teeman valinta Asetukset-sivulla sekä kellon
  teeman ja sisällön yhteinen tallennus säilyttävät ennusteen, sääpalvelun,
  hakuvälin, Windyn, ajastimet ja kalenteriolion. Verkkohaku- ja
  karttalatauskutsujen puuttuminen tarkistetaan erikseen. Widgettikohtainen
  teema ei kirjoita taustakuva-asetuksia; yhteinen teema käyttää aiempaa politiikkaa.
- Riippumaton Qt-tarkistus kattoi myös piilotetun widgetin tallennetun teeman
  käyttöönoton ensimmäisessä näyttämisessä sekä sääpaletin ja kellosisällön
  muuttamisen samassa asetuskokonaisuudessa.
- `previews/widget-theme-desktop.png` on Qt:llä renderöity yhdistelmäkuva
  Ubuntu-kellosta, Halla-säägraafista ja Kupari-kuukausiwidgetistä. Sää on
  kuvassa merkitty esimerkkisääksi. Testit käyttävät offscreen-alustaa ja
  taustakuvien muistialustaa; käyttäjän dataa tai oikeaa GNOME-istuntoa ei muuteta.
  Julkaisutoiminto toistaa koko testin puretusta lähde-ZIPistä ennen kanavan päivitystä.


## Ubuntu-teema ja analoginen kello 1.5.0

- 121 yksikkötestiä läpäistiin. Uudet testit kattavat Ubuntu-valintojen
  tallennuksen, vanhojen tietojen säilymisen, viisareiden kulmat,
  kellotaulun tilavarauksen, sekuntivalinnan ja läpinäkyvän taustan.
- Eristetty Qt-toimintatesti käyttää oikeita kellon ja yhteisen teeman
  asetussivuja. Tallentamaton valinta näkyy esikatselussa; kellon oma
  tallennus ei vaihda sääwidgetin palettia, kokoa, paikkaa, taustakuvaa tai
  ajanlaskukierron määräaikaa. Yhteinen Ubuntu-teema käyttää nykyistä
  taustakuvan vaihtopolitiikkaa ja jättää lukituskanavan ennalleen.
- Kaikki kellosisällöt sovittuvat kolmella fonttiperheellä, tekstikoon
  80–160 % rajoilla ja kellon numeroiden 140 % koolla. Kolmen ajanlaskun
  vaihto säilyttää widgetin mitat ja paikan. Kellotaulu kasvattaa aiemman
  digitaalisen kellon vaatimaa vähimmäiskorkeutta.
- Alkuperäinen Ubuntu-taustakuva on 1920 × 1080 pikseliä. PNG ja SVG ovat
  samat sovelluksessa ja teema-repossa. `previews/ubuntu-desktop.png` on
  Qt:llä renderöity yhdistelmäkuva, jonka analoginen ja digitaalinen
  esimerkkiaika on 10.10.2026 klo 10.10.30.
- Toimintatesti ajetaan offscreen-alustalla ja taustakuvien muistialustalla;
  oikeaa GNOME-istuntoa tai käyttäjän dconf-asetuksia ei muuteta.
  Aiemmat kalenteri-, sää-, fontti-, ikkunajärjestys-, koonmuutos- ja
  päivitystestit läpäistiin myös. Julkaisutoiminto toistaa testit puretusta
  lähdearkistosta ennen kanavan päivitystä ja tallentaa tulokset QA.logiin.
- Version 1.4.0 asetusten tarkistus ei hyväksy uusia Ubuntu-teematunnisteita.
  `UPDATES.md` neuvoo tallentamaan aiemmat teemavalinnat ennen palautusta;
  merkintöjä sisältävää asetustiedostoa ei korvata vanhalla varmuuskopiolla.

## Halla-yön tausta ja teemanvaihto 1.4.0

- Halla-yön taustakuva luotiin sisäänrakennetulla kuvanluonnilla. Kuva
  tarkistettiin visuaalisesti ja oikea tarkkuus 1672 × 941 luettiin pikseleistä.
  Sama kuva, catalog.json ja luontikuvaus ovat sovelluksessa ja paikallisessa
  teema-repossa. Yksityistä GitHub-repoa ei julkaista tai päivitetä tässä.
- 113 yksikkötestiä läpäistiin. Uudet kahdeksan kattavat oikean teemakuvan,
  puuttuvan oletuksen, muuttumattoman vanhan tilan, oletusvalinnan ja säilyttämisen,
  kuvatiedoston metatiedot sekä tausta-/asetustallennuksen yhteisen palautuksen.
- Eristetty Qt-testi vaihtaa Kuparin/Hallan teemoja oikeasta asetussivusta ja
  yhteisestä ohjaimesta. Oletuksena työpöytä seuraa teemaa; lukituskanava ei
  muutu. Säilytä-valinta, molempien kohteiden nimenomainen valinta ja
  nykyisen teeman kuvan asettaminen testataan muistissa olevalla alustalla.
  Asetus- ja taustakuvavalinnat sopivat 1020 ja 1280 pikselin ikkunaan
  ilman vaakavieritystä; molempien sivujen esikatselut tarkistettiin.
- Käynnistys, sama teema, fontin vaihto ja ajanlaskujen kierto eivät kirjoita
  taustakuvia. Tietojen tallennusvirhe ja GNOMEn osittainen kirjoitusvirhe
  palauttavat aiemman teeman ja taustat. Lukituksen avaimet säilyvät.
- Ikkunajärjestys, kaikki kahdeksan widgettiä, reunoista/kulmista koonmuutos,
  fontit, kalenterit, sää, päivityskomento ja aiemmat toiminnot testataan edelleen.
  Lopullisen julkaistun ZIPin eristetyn testin tulokset tallentuvat QA.logiin.
- Ikkunoiden järjestys ja kaikkien kahdeksan widgetin koonmuutos läpäistiin
  uudelleen oikeassa XWayland-istunnossa eristetyllä datalla. Ikkunanhallinnan
  asynkroniset tilaviestit odotetaan rajatusti ennen lukutarkistusta.

## Ikkunajärjestys ja omat widgetkoot 1.3.0

- Päällekkäisyys toistettiin oikeassa GNOME/XWayland-istunnossa ilman käyttäjän
  dataa: Qt.Tool ja NORMAL+UTILITY jäivät pääikkunan päälle, NORMAL+BELOW ei.
  Nykyisten widgettien WM_TRANSIENT_FOR-, UTILITY- ja BELOW-vihjeet luettiin.
- Itsenäiset NORMAL-widgetit, SKIP_TASKBAR/SKIP_PAGER ja todellinen
  _NET_CLIENT_LIST_STACKING tarkistettiin normaalin ja suurennetun pääikkunan,
  widgetistä avatun kalenterin ja sään sekä sääwidgetin QDialogin kanssa.
  Tarkistus tehtiin myös on_top-valinnan ollessa päällä; asetusta ei nollattu.
- 105 yksikkötestiä läpäistiin. Uudet yhdeksän testiä kattavat kaikki reunat,
  kulmien vastareunan ankkuroinnin, minimi-/maksimirajat, vanhan tilan säilymisen,
  widgettikohtaisen koon atomisen tallennuksen, resetoinnin ja kirjoitusvirheen.
- Qt-tapahtumilla vedettiin kaikkien kahdeksan widgetin kokoa lukitusta paikasta
  huolimatta; muut widgetit ja asetukset säilyivät. Kaikki kahdeksan suuntaa,
  koon pysyvyys, oletuskoon palautus ja Esc-peruminen läpäistiin myös oikeassa
  XWayland-testissä. Hiiritapahtumat olivat ohjelmallisia testitapahtumia.
- Säägraafi ja verkkoyhteydetön Windy sovittuivat uuteen kokoon. Fonttitestit,
  ajanlaskujen vaihto ja aiemmat toiminnot läpäistiin edelleen. Uuden paketin
  lopullinen eristetty testi ajetaan julkaisutoiminnossa ja tallentuu QA.logiin.
- Testidata oli tilapäisessä hakemistossa; taustakuvien alustasovitin oli
  muistissa. Käyttäjän merkintöjä, widgetkokoja tai GNOMEn lukitusasetuksia ei
  muutettu testeissä. Tämän julkaisun käyttöönotto tarkistetaan erikseen.

## Oma paikallinen päivityskomento 1.2.1

- Lähdekansion 96 yksikkötestiä ja koko eristetty Qt-toimintatesti läpäistiin.
  Aiemmat kahdeksan widgettiä, seitsemän sivua, kellon vaihto, fonttien sovitus,
  lisäkalenterit, taustakuvatoiminnot ja yhden instanssin ohjaus toimivat edelleen.
- Päivityksen 21 uutta testiä kattavat tarkistuksen ilman asennusta, toistuvan
  upgraden, versionvaihdon, palautuksen ja uusien merkintöjen säilymisen.
  Muuttunut ZIP tai julkaisuluettelo, versioristiriita, puuttuva riippuvuus,
  hakemistosta poistuva polku, linkki, tuntematon komento ja sudo hylätään.
- Vaurioituneen aktiivisen ohjelman palautus tarkistetulle edelliselle versiolle
  läpäistiin. Asennustiedon kirjoitusvirheessä aktiivinen kohde, käynnistin ja
  asennustieto palautuvat. Valikkokäynnistin varmuuskopioidaan; pois käytöstä
  oleva kirjautumiskäynnistin pysyy pois käytöstä eikä puuttuvaa luoda.
- Hallitun asennuksen kirjautumiskäynnistin osoittaa vakaaseen current-linkkiin.
  Vanhan saman version ohjelmakansion tarkisteen ristiriita hylätään.
- Julkaisutestin pakotettu epäonnistuminen jättää vanhan latest.jsonin ja
  päivitystiedoston ennalleen; virheloki jää paikalliseen qa-failures-kansioon.
- Julkaisutoiminto testaa puretun todellisen ZIPin ennen julkaisuluettelon vaihtoa.
  Sen tulos löytyy kunkin julkaistun version QA.logista. Käyttäjäasennuksen
  käyttöönoton tulos kirjataan erikseen paikallisen päivityskansion ohjeeseen.

Komento ei käytä aptia, sudoa tai verkkoyhteyttä. Testit eivät vaihda käyttäjän
oikeita taustoja tai lukitusasetuksia. Päivityksen rajat ja tarkistuslista:
`UPDATES.md`. Ulkoista julkaisua tai automaattista päivitysseurantaa ei tehdä.

## Yhteinen ajanlaskuwidget ja lisäkalenterit 1.2.0

- 75 automaattista testiä läpi. Uudet testit kattavat kiinteän, järjestyksessä
  ja satunnaisesti vaihtuvan kellon, 77 sekunnin monotonisen ajastuksen,
  valitun osajoukon, yhden ajanlaskun, lepotilasta paluun ja fontin vaihdon
  vaikutuksen ajastukseen. Kelloprofiilit, vanhan tilan täydentäminen ja
  lisäkalenterien näkyvyys tallentuvat pysyvästi.
- Kuuden kalenterin päiväykset testattu tunnetuilla uuden vuoden päivillä ja
  edestakaisilla muunnoksilla vuosien 1900, 2000, 2024, 2026 ja 2100 rajoilla.
  Heprealaisen karkausvuoden Adar I/II ja juliaanisen vuosisadan karkauspäivä
  tarkistettu. Heprealaisen 16.9.2023 = 1. Tishri 5784 -ankkuri tarkistettu
  [Hebcalin omasta muuntimesta](https://www.hebcal.com/converter?gd=16&gm=9&gy=2023&g2h=1).
  Persialaisen sallitun alueen ulkopuolella näytetään puuttuva tieto.
- Qt-toimintatestit kattavat kaikki kahdeksan widgettiä ja seitsemän sivua,
  oikeat valintaruudut, tallennuksen, tallentamattoman esikatselun, kaikkien
  kellosisältöjen näyttämisen/piilottamisen ja erillisten kellojen yhdistämisen.
  Lisäkalenterien piilotus poistaa myös päivien ruutujen lisätiedot.
- Kolme fonttiperhettä ja tekstikoon 80–160 % rajat testattu, kellon numerot
  140 %. Kaikki yhdeksän sisältökenttää sovittuvat ilman rivien päällekkäisyyttä
  ja ilman koon tai paikan vaihtelua ajanlaskun vaihtuessa.
- Kellon tai lisäkalenterien valinta ei kutsu sääwidgetin ulkoasu-/karttapäivitystä.
  Sääwidgetin koko, paikka, tarjoaja ja paletti tarkistettiin muuttumattomina.
  `asaa/weather/widget.py` ja `asaa/services.py` säilyivät tavutasolla samoina.
- Käynnissä ollut 1.1.0 suljettiin normaalisti ja 1.2.0 avattiin
  Ajanlaskuwidgetit-sivulle. Yhteinen kello perii Varjoajan aiemman paikan;
  erilliset kellot piilotettiin mutta niiden valinnat ja paikat säilytettiin.
  Merkinnät, muistutukset, fonttisäädöt ja kaikki sääasetukset luettiin takaisin
  muuttumattomina. Yhteinen kello ja aiempi sääwidget ovat valittuina näkyviin.
- Työpöytä-/lukituskuvien kanavat, diaesitykset, `lock-enabled`, lukitusviive
  ja lisäosan kellotila pysyivät tarkassa ennen/jälkeen-lukuvertailussa samoina.
  Päivitystä edeltävä yksityinen tilavarmuuskopio on `work/`-kansiossa, jota
  ei sisällytetä toimitettavaan pakettiin. Julkaisua GitHubiin ei tehty.

`clocks.png`, `clock-shadow.png`, `clock-star.png`, `clock-civil.png`,
`star-calendars.png` ja `calendar-options.png` ovat Qt:n käyttöliittymäesikatseluja,
eivät koko GNOME-työpöydän kuvakaappauksia. Kuvien sää on merkitty esimerkkisääksi.
Käynnissä olevan sovelluksen valmius tarkistettiin paikallisella sivuohjauksella;
natiivin GNOME-raahauksen tai lukitusnäytön toimintaa ei simuloitu.

## Taustakuvat ja teema-repo 1.1.0

- 58 automaattista testiä läpi. Uudet testit kattavat kuvatiedoston kelpoisuuden,
  muuttamattoman alkuperäisen kuvan, tuontien päällekkäisyydet, repon polkujen
  rajauksen, asetusten täydentämisen vanhasta versiosta, työpöydän/lock-kanavan
  erottamisen, 77 minuutin diaesityksen ja tarkalleen aiemman valinnan palautuksen.
- Vioittunut kuva, puuttuva lisäosa, väärä valinta ja varmuuskopion tallennusvirhe
  eivät muuta järjestelmäasetuksia. Osittainen kirjoitusvirhe palauttaa jo
  kirjoitetut arvot. Varmuuskopiosta ei voi muuttaa `lock-enabled`-asetusta.
- Oikean PyGObject/Gio-rajapinnan tyyppimuunnokset, delay/apply ja luku takaisin
  testattu omassa prosessissa `GSETTINGS_BACKEND=memory`-asetuksella. Se käyttää
  asennettuja GNOME-skeemoja, ei käyttäjän dconf-asetuksia.
- Qt-toimintatestissä galleriasta painettiin oikeita kohdepainikkeita, testattiin
  kaikkien seitsemän widgetin taustakuvapainikkeet, paikallinen sivuohjaus,
  usean kuvan valinta, diaesitys ja palautus. Alustasovitin oli muistissa.
  Aiemmat fonttien sovitustestit ja widgetvalintojen säilyminen lopetuksessa
  läpäistiin edelleen.
- Nykyisen GNOME 50.1 -istunnon tuetut avaimet, arvorajat, kirjoitusoikeudet
  ja käytössä oleva Dia Wall 77 tarkistettiin lukevasti. Lukitusasetuksia ei
  muutettu. Työpöytää ei lukittu eikä lisäosaa asennettu uudelleen testaamista varten.
- Kuparinen tähtikello tarkistettiin visuaalisesti: oikealla on tumma widgetalue,
  ei upotettua käyttöliittymää tai tekstejä. Todellinen tarkkuus 1672 × 941.
  Teema-repon ja sovelluksen kuva ovat tarkistussummaltaan samat.
- Yksityinen GitHub-repo `Jakke77/Ajanlaskut-ja-Saa-Teemat` luotiin ja päähaaran
  commit sekä kuvan tiedostokoko ja Git-objektin tarkiste luettiin takaisin
  GitHubista. Ne vastaavat paikallista repoa.
- `.deb` purettiin omaan tilapäishakemistoon ja sen 58 testiä sekä koko Qt-
  toimintatesti läpäistiin. Lähdearkisto ei sisällä käyttäjän asetuksia tai työdataa.
- Käynnissä ollut 1.0.1 suljettiin normaalisti ja 1.1.0 avattiin Taustakuvat-sivulle.
  Paikallinen teema-repo liitettiin galleriaan. Asetukset, fonttikoot, widgettien
  näkyvyys ja paikat sekä merkinnät ja muistutukset luettiin takaisin samoina.
  Työpöytä-/lukituskanavien ja lukituksen asetukset pysyivät muuttumattomina.

`wallpapers.png` on sovelluksen gallerian Qt-esikatselu. Sen säädata on
merkitty esimerkkisääksi kuten aiemmissa testikuvissa. Lukitusnäytön lopullista
visuaalista näkymää ei varmennettu lukitsemalla käyttäjän istuntoa.

## Fonttikorjaus 1.0.1

Vianrajaus: fontin perhe oli valittavissa, mutta widgettien piirto käytti kiinteitä
pikselikokoja. Widgetin oletusskaala 77 % pienensi samalla tekstin 77 prosenttiin.
Korjaus: itsenäiset tekstin ja kellon numeroiden kokovalinnat, oletusteksti 130 %.
Fontin mittaus rajaa sisällön sille varattuun tilaan. Päiväennusteet on jaettu
kahdelle riville, jotta suurempi teksti ei peitä seuraavaa ennustetta.

Uudet testit kattavat vanhan asetustiedoston täydentämisen ilman käyttäjän
valintojen katoamista, fonttikokojen rajat ja pysyvyyden sekä kolmen fonttiperheen
koon 80–160 %. Kaikki seitsemän widgettiä tarkistetaan muuttamatta niiden mittoja
tai paikkaa. Kellon maksimikoko 140 % tarkistetaan samassa piirtoajossa.
Kaikki 42 automaattista testiä sekä Qt:n fontti- ja widgettitestit läpäistiin.
Päivityksen yhteydessä korjattiin myös tarkoituksellinen lopetus: sen pitää
sulkea ikkunat muuttamatta widgettien valintoja, eikä tulkita lopetusta yksittäisen
widgetin piilotukseksi. Erillinen Qt-tapahtumasilmukan testi tarkistaa tämän.

## Alkuperäisen version 1.0.0 tarkistus

- 40 automaattista testiä läpi: kolme ajanlaskua, rajat ja karkauspäivät,
  atominen tallennus, tuonti, muistutukset ja sääkerroksen välimuisti/parserit.
- Qt-toimintatesti läpi: viisi pääsivua, seitsemän widgettiä, näkyvyyden tallennus,
  Kupari/Halla-teeman ja fontin yhteinen vaihto sekä paikallinen yhden instanssin ohjaus.
- Oikean X11/XWayland-pääikkunan käynnistys ja reaaliaikainen säähaku läpi:
  Yr 24 tuntitietoa, Foreca 126, FMI 26; wttr.in kolme päivän ennustetta.
  Kaikki neljä palauttivat ennusteet ilman virhettä. Oletushakuväli 77 minuuttia.
- `.deb`-paketti purettiin erilliseen hakemistoon ja sen oma toimintatesti ajettiin.
  Paketointi ei vaadi pääkäyttäjää eikä muuta vanhoja sovelluksia.
- Käynnistimen sisältö luettiin takaisin ja työpöytätiedosto tarkistettiin.
  Oikeasta paikallisesta asetustiedostosta tarkistettiin kupariteema, kolme
  oletuswidgettiä, 77 minuutin hakuväli ja yhden vanhan päivämerkinnän onnistunut tuonti.
- Alkuperäisten Goottikalenterin ja Pöllönkankaan sääprojektien työkopiot säilyivät
  muuttamattomina. Uusi sovellus avattiin pääikkunana ilman uusia desktop-kopioita.

Kuvat `overview.png`, `calendar.png`, `weather.png`, `widgets.png`, `settings.png`,
`frost.png` ja `desktop-widgets.png` käyttävät merkittyä esimerkkisäätä.
`live-overview.png` on sovelluksen omasta ikkuna-renderöinnistä oikeilla ennusteilla;
se ei ole koko työpöydän kuvakaappaus. GNOMEn ikkunan sijoittelua/raahausta ja
laitteen sijaintilupaa ei testattu natiivin käyttöliittymän automaatiolla.
# Kuvaketeemojen sovellusintegraatio · 1.7.0

Kuvakkeet voi ottaa käyttöön Asetuksista tai Taustakuvat-sivulta. Automaattinen
vaihto on vapaaehtoinen ja oletuksena pois. Kupari-, Halla- ja Ubuntu-kuvakkeet
ovat paketissa; käynnistys, kellon kierto ja yksittäisen widgetin teemamuutos
eivät muuta työpöydän kuvakkeita. Sovelluskäynnistimien korjaus on erillinen toiminto.

Kuvaketeemojen backend- ja Qt-testit tarkistavat säilyttävän oletuksen, sivujen
luonnokset, Snap/apt-korjauksen rajapinnan sekä asetusten, taustakuvan ja kuvakkeiden
palautuksen virhetilanteessa. Palautus muistaa kulloisenkin käyttöönottokierroksen
alkuperäisen työpöytäteeman. Todellista Gio-asetuskirjoitusta on tarkistettu
`GSETTINGS_BACKEND=memory`-tilassa: vain `icon-theme` muuttuu, käyttäjän dconf säilyy.

Kuvakerepon 40 testiä, kaikkien 104 kuvakemallin renderöinti kolmessa paletissa
ja GTK-välimuistit tarkistettiin erikseen. Päivitys aiemmasta toimitetusta
kuvakepaketista säilyttää ylimääräiset tiedostot ja estää omien muokkausten korvaamisen.
Varsinainen sovellusvalikon ja telakan ulkoasu on vielä tarkistettava Ubuntu-istunnossa.
