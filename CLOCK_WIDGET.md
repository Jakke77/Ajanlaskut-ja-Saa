# Komponentit: ajanlaskukellot ja widgettiteemat · 1.6.1

## Tarve ja nykyiset mallit

Erilliset Varjoajan, Tähtiajan ja gregoriaanisen kellot vievät turhaan samaa tilaa.
Yhteinen `DesktopSurface('combined')` käyttää samaa paneelia, fonttimittausta,
taustakuva- ja kalenteripainikkeita kuin vanhat kellot. Säägraafin ennuste,
kartta, välimuisti, paikka ja palveluasetukset säilyvät teemanvaihdossa.

## Ominaisuudet ja variantit

| Ominaisuus | Oletus | Toiminta |
|---|---|---|
| Vaihtotapa | järjestyksessä | kiinteä valinta, järjestys tai satunnainen |
| Ajanlaskut | kaikki neljä uudessa asennuksessa | vähintään yksi, satunnainen ei toista heti samaa |
| Vaihtoväli | 77 sekuntia | 1–3600 s, ei sama asetus kuin sään 77 minuuttia |
| Kelloteema | sovelluksen yhteinen | widgetille voi valita Kuparin, Hallan, Ubuntun tai ajanlaskun oman teeman |
| Näyttötapa | teeman oletus | digitaalinen, analoginen, Otavakello tai yhdistelmä; valinta erikseen jokaiselle kellolle |
| Digikellon numerokoko | yhteinen 100 % | oma 80–140 % valitulle kellolle; fontti säilyy yhteisenä |
| Widgetin tekstiväri | teeman mukaan | oma väri kaikille kahdeksalle widgetille; korostus- ja sääsuureiden värit säilyvät |
| Digikellon numeroväri | widgetin tekstiväri | oma väri valitulle kellolle tai widgetin värin seuraaminen |
| Varjoajan oma teema | Kupari | kuparipaletti ja kiertoradat |
| Tähtiajan oma teema | Astraali | tumma vihertävä pohja ja kultainen korostus |
| Gregoriaanisen oma teema | Aamunkajo | sinertävä pohja ja vaalea kalenteriruudukko |
| Sisältö | kello, päiväys, päivänimi, vaihe, tavallinen päiväys, vyöhyke, sää | merkintä ja seuraava muistutus valinnaiset |

Ajanlaskun omat värit ovat `theme.py`:n `CALENDAR_THEMES`-tunnuksia;
Kupari, Halla ja Ubuntu ovat yhteisiä `THEMES`-paletteja. Paneelin säde on 16,
sisäleveys 430, tekstin reunaväli 22 loogista pikseliä. Sisältökoostumus käyttää
`clock_config.clock_layout`-paikkoja. Piilotettu kenttä supistaa paneelia, mutta
ajanlaskun vaihtuminen ei muuta paneelin kokoa tai sijaintia. Kaikki kolme
ajanlaskua näyttävät tavallisen paikallisen kellonajan, eivät eri nopeudella käyviä kelloja.

## Widgettikohtaiset teemat

Teema valitaan erikseen kaikille kahdeksalle widgetille: yhteiselle kellolle,
kolmelle erilliselle kellolle, tuntisäägraafille, Varjosään kolmen päivän
näkymälle sekä Varjoajan ja Tähtiajan kuukausiwidgeteille.
**Työpöytäwidgetit → Teema** tarjoaa yhteisen teeman, Kuparin, Hallan ja Ubuntun.
Kelloissa voi lisäksi valita **Ajanlaskun oma teema**. Ubuntu vaihtaa paletin ja
käyttää oletuksena analogista kellotaulua ja digitaalista aikaa. **Näyttötapa**
voi valita digin, analogin tai molemmat missä tahansa teemassa.

**Ajanlaskuwidgetit**-sivulla teema ja sisällöt koskevat valittua kellowidgettiä.
Esikatselu näyttää luonnoksen ennen tallennusta. Tallennus yhdistää vain
muokatut widgettien teema- ja värivalinnat sekä kelloprofiilien kentät viimeisimpään tilaan.
Toisella sivulla tallennetut muiden widgettien valinnat tai muokkaamattomat
sisältökentät säilyvät.

Valinnainen `settings.widget_themes` on harva kartta: siinä ovat vain erikseen
tallennetut widgettivalinnat. `shared` seuraa sovelluksen yhteistä teemaa ja
`copper`, `frost` sekä `ubuntu` valitsevat kiinteän paletin. `calendar` on sallittu
vain viidelle kelloprofiilille. Puuttuva kellon avain käyttää vanhaa `time_theme`-valintaa;
muut widgetit seuraavat ilman omaa avainta yhteistä teemaa. Valinnat ratkaisee
`widget_themes.py`, jota myös esikatselu käyttää.

**Asetukset → Käytä valittua teemaa kaikissa widgeteissä** tyhjentää tallennettaessa
`widget_themes`-kartan ja asettaa `time_theme`-valinnaksi `shared`. Valittu yhteinen
teema tulee näin myös vanhoihin ajanlaskun omia värejä käyttäviin kelloihin.
Widgettien näkyvyysvalinnat säilyvät.

Sääwidgetin paletin vaihto piirtää nykyisen ennusteen uudelleen. Se ei tee
verkkohakua, lataa Windyä tai käynnistä sään ajastuksia uudelleen.
Kellon ajanlaskukierto jatkuu samalla määräajalla teeman tai sisällön vaihtuessa.
Analoginen kellotaulu tarvitsee enemmän korkeutta: lyhyt kello voi kasvaa
vähimmäiskokoon ja siirtyä näytön sisään.

## Tilat ja vuorovaikutus

- Normaalitila: valitut kentät ja widgetin valitsema teema; ajanlaskun oma teema
  vaihtaa värit näkyvän ajanlaskun mukana.
- Ajastettu: laskuri alatunnisteessa, monotoninen ajastus ei riipu kellon säädöstä.
  Koneen herätessä yksi vaihto; ei nopeaa rästiin jääneiden vaihtojen sarjaa.
- Kiinteä: valinta pysyy myös seuraavalla käynnistyksellä.
- Satunnainen: yksi ajanlasku on sallittu; useammasta valitaan eri kuin edellinen.
- Puuttuva sää: hakutila tai oikea virhe; ei keksittyä ennustetta.
- Tyhjä merkintä/muistutus: sanallinen tyhjä tila.
- Esikatselu: käyttää oikeaa widgetin piirtäjää mutta ei muuta asetuksia, paikkoja
  tai widgetin näkyvyyttä. Sää ei ole keksittyä, ellei kuva ole nimetty testikuvaksi.
- Tallennusvirhe: aiempi pysyvä tila säilyy, käyttöliittymä näyttää virheen.

## Saavutettavuus

PyQt:n omat valintaruudut, yhdistelmäkentät ja painikkeet tukevat Tabia, Spacea,
nuolia ja Enteriä. Widgetin työkalupainikkeilla on `accessibleName`, tooltip sekä
näppäimistöfokus. Sisältö välitetään myös widgetin saavutettavaan nimeen.
Tekstin ja kellon numerokoon säädöt säilyvät erillisinä widgetin koosta.
Fontin mittaus rajaa jokaisen tekstirivin omaan kenttään; pitkä teksti lyhenee ja
näkyy kokonaan tooltipissa. Piilotetut sisältökentät eivät vuoda tooltippiin.

## Päivitys ja rajat

Vanha asetustiedosto täydentyy rikkomatta aiempia widgetvalintoja. Uusi asennus
avaa yhteisen kellon ja sääwidgetin, ja kellot seuraavat yhteistä teemaa.
Vanhan tiedoston olemassa oleva `time_theme` säilyy. Jos se puuttuu, lukija
käyttää aiempaa `calendar`-valintaa; puuttuva `widget_themes` täydentyy tyhjäksi
kartaksi. Pelkkä lukeminen ei kirjoita tiedostoa uudelleen.
Painike **Korvaa erilliset kellot** piilottaa
vain kolme erillistä kellopaneelia. Niiden sisällöt ja vanhat sijainnit säilyvät.
Yhteinen kello perii ensimmäisen näkyvän vanhan kellon sijainnin.

Kuusi oikeaa rinnakkaiskalenteria ovat erillistä lisätietoa Tähtiajan valitusta
päivästä, eivät uusi sääntö sen 510 päivän kierrolle. Master-valinta piilottaa
sekä lisätiedot, päiväruutujen lisäpäiväyksen että lisäkalenterien tooltipit.
Kukin kalenteri valitaan erikseen; näyttöpaikka on Tähtiaika tai kaikki kalenterit.
Versiosta 1.10.0 lähtien kellojen kuunvaihe ja valaistus lasketaan oikealle
hetkelle; ne ovat samat eri ajanlaskuissa. Varjoajan ja Tähtiajan omat päiväykset
säilyvät. Nimiparit näkyvät kalenterissa ja kellon vihjeessä.

## Veri Aika ja Otavan kaksi käyttötapaa · 1.12.0

`blood` on neljäs ajanlasku; viisi kelloprofiilia ovat `combined`, `shadow`,
`star`, `civil` ja `blood`. Päiväys käyttää aina Suomen klo 01:07:07 rajaa,
vaikka kellon tuntinäyttö seuraisi käyttäjän muuta aikavyöhykettä. Viikot
ovat jatkuvia seitsemän paikallisen päivän jaksoja alkupisteestä 26.6.2026.
`Calendars.at(system, moment)` pitää tämän eron erillään kuukausikalentereista.

Valinnainen `otava`-sisältökenttä piirtää Oulun todellisen pohjoistaivaan.
Se on oletuksena näkyvissä yhteisessä ja Veri Ajan kellossa, ja se voidaan
piilottaa kellojen sisältövalinnoista. Sama vakaan mittakaavan piirtäjä palvelee
etusivua ja Veri Ajan sivua. Kuvan pohjoisen taivaannavan ympärillä liikkuvaa
asentoa ei keskitetä tai kierretä uudelleen joka piirrolla.

Näyttötavat `otava` ja `otava_both` puolestaan käyttävät Otavaa symbolisena
sekuntiviisarina: yksi kierros minuutissa. `seconds=False` piilottaa tämän
kuvion, mutta ei varsinaista taivaskenttää. Tunti- ja minuuttiviisarit näyttävät
normaalin paikallisen ajan. Näyttötapa ja taivaskenttä ovat toisistaan riippumattomia.

Asetusten lukija täydentää puuttuvan blood-profiilin ja otava-kentät. Se ei
avaa uutta ikkunaa eikä muuta vanhaa tallennettua vaihtoon osallistuvien ajanlaskujen listaa.

## 777 päivän vuosi ja nimiparit · 1.12.1

`BloodDate.year`, `day_of_year` ja `week_of_year` jakavat vuoden 777 päivään
ja 111 viikkoon. Jatkuva `week` säilyy sisäisenä yhteensopivuustietona;
näkyvä päiväys käyttää vuoden sisäistä viikkoa. Vuoden vaihtumisen jälkeen
päivä on 1/777 ja viikko 1/111. Ensimmäinen raja on 11.8.2028 klo 01:07:07.

`nameday` on valinnainen 66 pikselin sisältökenttä: miehen ja naisen nimelle
on erilliset rivit. Se on oletuksena käytössä yhteisessä ja Veri Ajan kellossa.
Vanha profiili täydentyy kentällä lukiessa, ja tallennettu false säilyy.
Nimilista on versionoitu `assets/blood-names.json`; koko lista on pysyvä eikä
sovellus arvo nimiä. Nimet seuraavat samaa Suomen vuorokausirajaa kuin Veri
Ajan päivämäärä ja merkinnät. Pitkä vuosipäiväys ja nimet sovitetaan rivin
leveyteen pienentämällä tekstiä tarvittaessa, joten vuoden numero ei katoa.
