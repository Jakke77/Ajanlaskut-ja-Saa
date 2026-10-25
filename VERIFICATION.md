# Tarkistukset

## Otavan suunta ja 26 minuutin tarkistus · 1.12.3

Koko Ubuntu-sarja: 425 testiä läpäisi. Uusi yhteinen sampler testataan heti
käynnistyksessä, täsmälleen 26 minuutin rajalla, lepotilan jälkeen ja kellon
korjauksessa. Kesä-/talviajan toistuva tunti käyttää UTC-kestoa. Näkymät jakavat
saman näytteen ja laskenta-ajankohdan; myös virheelliset aikaleimat tarkistetaan
välimuistin ollessa täynnä. Päivän selaus ei muuta taivaskuvan nykyhetkeä.

Otavan tähtipaikkojen aiemmat riippumattomat Astropy/ERFA-vertailut säilyvät.
Alkaidin suunta ja korkeus tulevat samasta seitsemän tähden laskennasta, eivät
kellon viisarin kulmasta. Zeniitti/itä/länsi ja taivaannapa ovat kiinteitä
vertailusuuntia. Oikea Qt renderöi tähtikuvat ja widgetin sekä tarkisti yhteisen
näytteen. Kellon symbolisen sekuntiviisarin viisi testiä läpäisivät ennallaan.


## Veri Ajan ruutukalenteri ja nimikirja · 1.12.2

- Koko Ubuntu-lähteen yksikkö- ja Qt-sarja: **419 testiä läpäisi**.
- Seitsemän sarakkeen ja viiden viikon ruudukon 23 selausjaksoa kattavat
  kaikki 777 päivää täsmälleen kerran; vuoden viimeisessä jaksossa on yksi
  viikko. Jakson/vuoden vaihto, paikallinen klo 01:07:07 raja, päivävalinta,
  merkinnät ja vuosien 1900–2100 rajat ovat Qt-testeissä.
- Kalenterit-valikon Veri Aika pysyy kalenterisivulla. Valitun päivän nimet
  ja merkitykset näkyvät saman päivän tiedoissa. Leveässä ikkunassa tiedot
  ovat oikealla ja pienessä alla. 1560×1000 ja 1020×720 tarkistettiin ilman
  vaakavieritystä. Vanha kuukausikalenteri palautuu toiseen ajanlaskuun vaihtaessa.
- Kaikilla 1 554 alkuperäisellä nimellä on pysyvä, yksilöllinen selitys.
  Alkuperäinen nimiluettelo säilyi tavulleen samana. Jokainen selitys on
  sidottu oikeaan nimeen, sukupuoleen ja vuoden päivään. Puuttuva, toistuva,
  väärään päivään sidottu tai lähteetön tietue hylätään.
- Symboliset nimimerkitykset on merkitty kirjaimellisella `**`-merkillä.
  37 nimiryhmän sanatausta erotetaan runollisesta merkityksestä. Taustojen
  18 lähdesivua luettiin ja niiden sanasto tarkistettiin; samankaltaisesta
  nimestä ei päätellä historiallista alkuperää. Kopioitu selitys säilyttää
  sekä merkinnän `** tämän keksin :)` että erilliset lähdeosoitteet.
- HTML- ja Markdown-nimikirja kattavat samat 777 nimiparia. Mukana olevat
  tiedostot vastaavat täsmälleen generaattorin tulosta. HTML toimii ilman
  ulkoisia resursseja; Qt Chromium tarkisti haun, viikon/päivän suodatuksen,
  tyhjän tuloksen, haun tyhjennyksen ja 500 pikselin näkymän. Tulostustyyli
  sisältää koko nimikirjan ja näyttää lähdeosoitteet.
- Pääikkunan ruutukalenteri ja nimikirja renderöitiin oikealla Qt:lla
  tilapäisessä asetuskansiossa ilman säähakuja. Kalenterin selaus ja
  nimihaku eivät muuta asetuksia, kalenterimerkintöjä tai syntymäpäivää.

## Veri Ajan 777 päivän vuodet ja nimiparit · 1.12.1

- Ubuntu-lähdekoodin koko yksikkö- ja Qt-sarja: **390 testiä läpäisi**.
- Vuoden viimeinen päivä on 777/777 ja viikko 111/111; seuraavana paikallisena
  klo 01:07:07 alkavat vuosi 0002, päivä 1/777 ja viikko 1/111. Ensimmäinen
  vuoden vaihtuminen on 11.8.2028. Viikon seitsemän päivän rytmi jatkuu katkeamatta.
- Vuoden raja lasketaan paikallisista päivämääristä. Myös 777×24+1 tunnin
  vuoden kesto kesä-/talviajan eri puolilla on erillinen regressiotesti.
- Staattisessa UTF-8-luettelossa on 777 nimiparia: 777 yksilöllistä miehen ja
  777 yksilöllistä naisen nimeä, pituus 4–12 kirjainta. Sukupuolten nimijoukot
  eivät leikkaa. Jokainen pari toistuu vastaavalla vuoden päivällä seuraavana
  777 päivän vuonna. Nimiankkurit suojaavat pysyviä päiväsijoituksia.
- Syntymäpäivähaku toimii myös ennen alkupäivää selvästi nimikierron
  sovituksena. Se ei muuta päivämäärää, merkintöjä tai asetuksia.
- Oikea Qt tarkisti vuoden vaihtumisen etusivulla, kalenterissa ja
  widgetissä, nimiparin kaksi näkyvää riviä, niiden piilotuksen ja asetuksen
  säilymisen. Widgetin koko pysyy samana vuoden vaihtuessa.
- Veri Ajan ja Nimikalenterit-sivun nimet, vuosiselaus, päivän vihjeet,
  syntymäpäivähaku ja siirtymä nimihakuun tarkistettiin myös 1020×720-koossa.
  Otavan taivaskuva käyttää yhä nykyhetkeä historiallisen valinnan rinnalla.
- Uudet nimet toimitetaan `assets/blood-names.json`-tiedostossa sekä
  Ubuntu- että Windows-pakettiin. Uusia riippuvuuksia tai verkkohakuja ei tarvita.

## Veri Aika, Oulun Otava ja Veriyö · 24.10.2026 · 1.12.0

- Ubuntu-lähdekoodin koko yksikkö- ja Qt-sarja: **370 testiä läpäisi**.
  Viikkorajan testi kattaa sekunnit ennen klo 01:07:07 ja sen jälkeen,
  Suomen kesä- ja talviajan 167/169 tunnin viikot sekä toisessa
  aikavyöhykkeessä näytettävän kellon. Ennen vuorokausirajaa myös
  widgetin merkintä pysyy Veri Ajan alkupäivän mukaisena.
  Laaja Qt-hyväksyntä läpäisi myös kaikki yhdeksän widgettiä, eri fontti-,
  koko-, teema- ja näyttötapayhdistelmät sekä tallennus- ja palautusvirheet.
- Oikean Qt-ohjaimen hyväksyntä tarkisti etusivun, viikkokalenterin,
  Kalenterit-valikon ohjauksen, kellon näyttötapojen tallentumisen,
  vanhojen asetusten täydentymisen ja erikseen piilotettavan tähtikuvan.
  Kaikki kymmenen sivuvalintaa näkyvät 1020×720-ikkunassa.
- Seitsemän tähden BSC5-luettelopaikat, ominaisliikkeet ja prekessio
  verrattiin Astropy 7.1 / ERFA -tuloksiin neljällä 2026 ajanhetkellä:
  taivaan kulmaero on alle 0,01 astetta. Myös tuetun 1900–2100 alueen
  reunat, tähtivuorokausi, kuuden tunnin kierto ja Oulun horisontti testattiin.
  Astropy ei ole sovelluksen tai offline-testien riippuvuus.
- Otavakellon seitsemän tähden sekuntiviisari tarkistettiin oikeassa
  Qt-piirrossa eri sekunneilla, sekunnit piilotettuina ja läpinäkyvällä
  taustalla. Se on käyttöliittymässä erotettu todellisesta tähtitaivaasta.
- Veriyö-paletin teksti-, himmeä- ja korostusvärin kontrasti on vähintään
  7,12:1 taustaa ja pintaa vasten. Kaksi 1672×941-taustakuvaa ovat
  identtiset sovelluksessa ja teemarepossa. Staattinen kuvitus on merkitty.
- Kuvakerepon **51 testiä** ja sovelluksen **40 kuvaketestiä** läpäisivät.
  Neljän aiemman kuvaketeeman tiedostot säilyivät tavutasolla ennallaan.
- Windowsin paketissa ajettiin **90 testiä natiivilla Windows 2022
  -runnerilla**, mukana kaikki uudet Veri Ajan laskenta-, piirto- ja
  integraatiotestit. Myös koko Windows-käyttöliittymän hyväksyntä sekä
  Yr:n 24 ja FMI:n 26 tuntiennusteen TLS-haut mukana olevilla CA-varmenteilla
  läpäisivät. [Windows-ajo 40094226230](https://github.com/Jakke77/Ajanlaskut-ja-Saa/actions/runs/40094226230).
  High contrast ohittaa tarvittaessa Veriyö-värit säilyttäen käyttäjän valinnan.
- Käyttäjäasennuksen purkajan tiedostoraja on nyt 4096, jotta viides
  kuvaketeema mahtuu mukaan. Yli 2000 tiedoston julkaisu ja rajan ylittävä
  paketti testattiin; polku-, tiedostotyyppi- ja tavumäärärajat säilyvät.
- Windowsin paikallinen ristipaketti tarkistettiin erikseen: x64 PE-käynnistin,
  kahdeksan lukittua lataustarkistetta, ZIP:n CRC sekä kaikkien 187
  lähdetiedoston vertailu. Jaetut Veri Ajan moduulit ja taustakuvat ovat
  Ubuntu-version kanssa samat. Julkaistava Windows-ZIP on natiivin CI-ajon
  rakentama ja testaama, joten sen ZIP-tarkiste poikkeaa paikallisesta ristipaketista.

## Kuu, nimikalenterit ja päivän valo · 23.10.2026 · 1.10.0

- Lopullinen yksikkö- ja Qt-testisarja: 332 testiä läpäisi. Lisäksi uusi
  näkymä renderöitiin oikealla Qt:llä ja yhteisen päivän merkinnän tallennus
  tarkistettiin eristetyssä, verkkohakuja tekemättömässä sovellusinstanssissa.
- Yhteinen kuunvaihe korjaa 19.10.2026-kuvien ristiriidan. Varjoajan, Tähtiajan
  ja tavallisen kalenterin valitun päivän vaihe on sama. Oikeat Qt-kellopinnat
  näyttävät saman hetkellisen vaiheen ja omat nimiparinsa vihjeessä.
- Kuun lokakuun 2026 päävaiheet verrattiin US Naval Observatoryn UTC-taulukkoon:
  poikkeama alle kaksi minuuttia. Oulun 23.10.2026 Auringon ja Kuun nousu-/laskuajat
  sekä siviilihämärä täsmäsivät USNO:n minuuttilukemiin. New Yorkin 23 tunnin
  päivältä 8.3.2026 nousu ja lasku täsmäsivät; Kuulta puuttui nousu, mutta lasku
  oli oikein eikä päivää merkitty kokonaan horisontin alapuoliseksi.
- Helsingin 23/25 tunnin päivät, Tromssan yötön yö ja kaamos sekä talven
  siviilihämärä tarkistettiin. Tuleva täysikuu näytetään Helsingin talviajassa,
  ei nykyhetken kiinteällä UTC-siirtymällä.
- Vuosien 1899–2101 talvipäivänseisauksen edellinen uusikuu ja 12/13 kuukauden
  vuodet tarkistettiin. Vaahtokuu seuraa helmikuuta, kuukausissa on 29 tai 30
  päivää eikä kuukausien tai vuosien välille jää aukkoja. Vuoden 2023 joulukuun
  siemenhaun rajatapaus on erillinen regressiotesti.
- Nimiluettelo sisältää 390 Varjoajan, 510 Tähtiajan ja 390 suomalaisen kalenterin
  pysyvää nimiparia. Kummankin sukupuolen nimet ovat oman kalenterinsa sisällä
  yksilöllisiä. Syntymäpäivähaku toimii ennen alkupäiviä muuttamatta päiväysmuunnosta.
- Oikea Qt-käyttöliittymä avasi nimihaun, Vaahtokuun ja kuukauden valoajat.
  Syntymäpäivähaku ei kirjoita asetuksia. Vanhat vastaukset eivät vaihda uuden
  päivän tietoja, eikä kesken laskennan sulkeminen jätä työntekijää käyntiin.
  Uusien sivujen asettelu tarkistettiin myös 1020×720-ikkunassa.
- Kirjastot ja niiden lisenssit säilyivät mukana muuttamattomina. Tähtilaskenta
  ei tarvitse uusia paketteja, API-avaimia tai verkkohakua. Sääsivun aiemmat
  verkkopalvelut säilyvät erillisinä.

## Forecan ja FMI:n kartta widgetin kokoiseksi · 14.10.2026 · 1.9.1

- 306 yksikkö- ja Qt-testiä läpäisi. Uudet karttatestit kattavat palvelun oman
  suurennussäätimen käytön, vain tunnetun karttasivun sallimisen, evästeikkunan,
  puuttuvan säätimen, aikakatkaisun, palvelun vaihdon ja myöhäiset JS-vastaukset.
- Pääikkuna ja työpöytäwidgetti säilyvät tavallisina Qt-ikkunoina. Palvelun
  valitsema oma karttaelementti avautuu selaimen sisältöalueelle; verkkosivun
  HTML:ää, kartan säätimiä tai lähdemerkintöjä ei poisteta tai kopioida.
- Todellinen Qt WebEngine ja ohjelmallinen OpenGL näyttivät kummankin palvelun
  oikean sadekartan lopullisella tuotantototeutuksella. Pääikkunan kartta oli
  1200×817 ja 432×276-widgetin kartta 389×156. Aikajana, kartan alkuperäiset
  säätimet ja tekijämerkinnät pysyivät palvelun omassa näkymässä.
- Molemmat kartat avattiin myös suoraan pieneen widgettiin tuoreella
  selainprofiililla. FMI:n evästevalinta pysyy normaalissa selainzoomissa;
  valinnan jälkeen sivun yläpalkin peittämä suurennussäädin saadaan näkyviin
  väliaikaisella sovituksella. Valmis kartta palautuu normaaliin zoomiin.
- Foreca käyttää nykyistä `/tutka`-renderöijää ja palvelun omassa
  JavaScriptissä tuettuja `lt`-, `ln`-, `z`- ja `l`-parametreja. Oulun testissä
  kartan keskipiste vastasi valittuja koordinaatteja. FMI:n kartta pysyy Suomen
  yhteisenä karttana, eikä sille muodosteta keksittyä sijaintiparametria.
- Evästevalintoja ei tehdä tuotantokoodissa käyttäjän puolesta. Forecan
  alkuperäinen evästeikkuna esti karttasäätimen käytön testissä, ja tilaviesti
  pyysi tekemään valinnan. Poisheittoprofiilin testaaja painoi alkuperäistä
  Estä kaikki -painiketta; vasta sen jälkeen kartta avautui automaattisesti.
- Tilaviestit ja uudelleenyritys mahtuvat myös 389×189-kehykseen. Piilotettuna
  valmistuva verkkolataus odottaa näkymän avaamista; piilotus ei käynnistä
  kartan aikakatkaisua. Uudelleen avaaminen tarkistaa jo ladatun kartan ilman
  uutta HTTP-latausta. Kartan sulkeminen näyttää uudelleenyrityksen.
- Windyn alkuperäinen kartta ja tuntiennuste säilyvät. 12/24 tunnin valinta
  piilotetaan verkkokartoista ja palautetaan sovelluksen omiin graafeihin.
- Live-tarkistus tehtiin kertakäyttökontissa TLS-tarkistus säilyttäen.
  Isäntäympäristön CA-/NSS-asetuksia ei muutettu. Xvfb-paketin SHA256
  tarkistettiin allekirjoitetun Debian-julkaisun ja pakettimetadatan kautta.

## Sadekartat ja Windyn tuntiennuste · 14.10.2026 · 1.9.0

- Lopullinen yksikkö- ja Qt-testisarja: 281 testiä läpäisi. Mukana ovat
  palvelukohtaisen näkymän tallennus, vanhan asetustiedoston oletukset,
  yhteinen pääikkunan/widgetin valinta, piilotetun näkymän latauksen lykkäys,
  manuaalinen uudelleenlataus kesken ennustehaun ja kaikkien web-sivujen sulkeminen.
- Tallennusvirheen jälkeen sekä palvelu että näkymä säilyvät entisinä.
  Pääikkunan valinta ja widgetin oikean painikkeen toiminto raportoivat virheen
  kerran ja säilyttävät molemmat näkyvät sääpinnat.
- `main.py --self-test` läpäisi laajat ulkoasun, kahdeksan widgetin,
  kalenterin, muistutusten, tallennuksen ja yhden sovellusinstanssin tarkistukset.
  Lopputarkistukset tehtiin eristetyissä testihakemistoissa, ilman oikean
  GNOME-istunnon tai käyttäjän merkintöjen muuttamista.
- Forecan, Ilmatieteen laitoksen ja Windyn viralliset sivuosoitteet vastasivat
  HTTPS-pyyntöihin. Forecan cache-URL validoidaan ennen kaupungin kartan
  muodostamista; tuntematon tai muun palvelun URL avaa kansallisen sadetutkan.
  FMI:n kartta esitetään Suomen yhteisenä karttana ilman keksittyä paikkaparametria.
- Windyn kartaton tuntiennuste käyttää valitun paikan todellisia koordinaatteja.
  Sen oma taulukko ja aikajana säilyvät. Yr:n tai muiden palvelujen ennustetta
  ei esitetä Windyn datana eikä Windyn testirajapintaa käytetä oikeaan ennusteeseen.
- Todellinen Qt WebEngine avasi uuden yhteisen web-näkymän kautta paikallisen
  HTML-testisivun vasta näkyviin tulon jälkeen. Näkymällä oli positiiviset mitat,
  profiili oli yksityinen ja sivu/profiili vapautuivat sulkemisessa.
  Tämä paikallinen tarkistus ei yksin todista palvelujen verkkokarttatiilien
  tai WebGL:n toimintaa. TLS-varmenteiden tarkistusta ei ohiteta sovelluksessa.
- Lisäksi kaikki kolme virallista web-näkymää avattiin todellisessa
  Qt-selaimessa poisheittokontissa. HTTPS-varmenteet tarkistettiin kontin omassa
  luottamusympäristössä; isäntäympäristön pysyviä selainvarmenteita ei muutettu.
  Windyn tuntiennuste näytti oikeat lämpötilat, sademäärät, tuulet ja symbolit.
  Ennuste käyttää virallisen upotteen 187 pikselin korkeutta; karttaan vaihto
  palauttaa koko näkymäkorkeuden ja palvelun merkinnät säilyvät.
  Pienessä työpöytäwidgetissä selainzoom sovittaa kaikki ennusterivit
  käytettävään tilaan. Aito Qt-selaintesti ja kokotesti varmistivat, ettei
  selain- tai uudelleenyrityspainike peitä ennustetta, myös latausvirheessä.
  Forecan ja FMI:n sivut, JavaScript, kartan hallinta ja evästevalinnat latautuivat.
  Sadekarttojen karttagrafiikka jäi tarkistamatta kontin puuttuvan WebGL:n vuoksi.

## Tietoa sovelluksesta ja kahden asennuksen tunnistaminen · 13.10.2026 · 1.8.2

- 244 testiä läpäistiin. Uudet kolme Qt-testiä avaavat Tietoa sovelluksesta
  Ohje-valikosta, Asetuksista, sääwidgetistä ja ilmoitusalueelta.
- Dialogi näyttää prosessin lataaman version ja fyysisen asennuskansion.
  Ulkoasuluonnokset, asetukset ja työpöytä säilyvät avaamisen ja sulkemisen yli.
  Prosessin versionumero ei vaihdu, vaikka levyllä oleva versiotieto muuttuisi.
- Käyttäjän tulosteista tunnistettiin järjestelmäasennuksen 1.8.1 ja
  codex-ajanlasku-käyttäjäasennuksen 1.6.0 ero. Julkaistun 1.8.1-paketin
  todellisessa Qt-valikossa Ubuntu 26.10 Dark on neljäs näkyvä vaihtoehto;
  sama valinta löytyy myös kellojen ja kaikkien widgettien teemavalikoista.
- Päivitysohjeessa nykyinen käyttäjäasennuksen päivityskansio luetaan
  codex-ajanlasku status -komennosta. Muokattu polku ja välilyönnit säilyvät,
  eikä käyttäjän asetuskansiota poisteta päivitystä varten.

## Windyn käynnistyslataus ja uudelleenyritys · 12.10.2026 · 1.8.1

- 241 testiä läpäistiin. Uudet 29 Qt-testiä kattavat näkyvyyden jälkeen
  tapahtuvan latauksen, saman epäonnistuneen URL:n nimenomaisen uudelleenyrityksen,
  onnistuneen latauksen säilyttämisen ja turvallisen sulkemisen.
- Kaksi erillistä ohjainta käynnistetään samasta tallennetusta Windy-tilasta
  sekä näkyvällä että piilotetulla sääwidgetillä. Pääikkunan kartta saa oikean
  paikan, zoomin ja kerroksen ilman erillisen sääikkunan avaamista.
- Päivitä välittyy molemmille näkyville kartoille myös ennustehaun ollessa
  kesken. Automaattinen päivitys, fontin vaihto ja piilotetun näkymän
  synkronointi eivät pakota kartan latausta. Latausvirhe pysyy näkyvissä,
  kunnes käyttäjä yrittää uudelleen tai avaa karttanäkymän uudelleen.
- Karttanäkymässä ovat Yritä uudelleen ja Avaa Windy selaimessa. Selain
  avataan vain käyttäjän toiminnosta ja samalla karttarajauksella.
- Todellinen Qt WebEngine avasi paikallisen HTML-testisivun vasta näkyvyyden
  ja layoutin jälkeen; selaimen näkymällä oli positiiviset mitat. Tämä
  tarkistus ei ole Windyn karttatiilien tai WebGL:n verkkotesti. Virallinen
  embed-sivu vastasi myös HTTPS-pyyntöön HTTP 200:lla.
- Kartan lataustilaa ei tallenneta käyttäjän asetuksiin. WebEnginen
  yksityinen profiili, latausten ja lupapyyntöjen estot sekä TLS-tarkistus
  säilyvät. Käyttäjän oikeaa GNOME-istuntoa tai kalenterimerkintöjä ei muuteta.

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
