# Ajanlaskut ja Sää 1.12.1 · Windows 10

Windows 10:n **64-bittinen versio 1809 tai uudempi**. Paketti sisältää oman
Pythonin, Qt:n, WebEnginen ja aikavyöhyketiedot. Pythonia ei tarvitse asentaa.

## Käynnistys

1. Pura koko `Ajanlaskut-ja-Saa-1.12.1-Windows10-x64.zip` pysyvään kansioon,
   esimerkiksi oman käyttäjäkansiosi Sovellukset-kansioon.
2. Käynnistä **Ajanlaskut-ja-Saa.exe** puretusta kansiosta.
3. Halutessasi aja **Luo-pikakuvakkeet.cmd**. Se lisää kaksi pikakuvaketta
   nykyisen käyttäjän Käynnistä-valikkoon. Pääkäyttäjän oikeuksia ei tarvita.

**Vain-widgetit.cmd** avaa valitut työpöytäwidgetit. Ilmoitusalueen kuvakkeesta
saat pääikkunan takaisin. **Lopeta sovellus** sulkee myös widgetit.

## Veri Aika ja Otavakello · 1.12.1

Sivupalkin **Veri Aika** näyttää 777 päivän vuodet eli 111 seitsemän päivän viikkoa. Alkupiste on
**26.6.2026 klo 01:07:07 Suomen aikaa**; päivä ja uusi viikko vaihtuvat aina
klo 01:07:07 paikallista Suomen aikaa myös kesä- ja talviaikana. Viikot jatkuvat
alkupisteestä eteenpäin. Vuosi vaihtuu aina 777 paikallisen päivän jälkeen;
vuoden viimeinen viikko on 111. viikko. Ajanlasku on sovelluksen oma luova kalenteri.

Vuoden jokaiselle päivälle on pysyvä miehen ja naisen nimipari. Keksityt nimet
saavat vaikutteita verestä, elämänkierron ja biologian sanastosta sekä
mielikuvituksesta. Nimiparit toistuvat vuoden mukana, ja syntymäpäivän
nimen voi tarkistaa **Nimikalenterit → Oma nimi** -näkymästä. Ne ovat
sovelluksen omia nimiä, eivät virallisen nimipäiväkalenterin tietoja.

Kalenterin, etusivun ja widgetin Otava lasketaan Oulun taivaalle oikean
kellonajan mukaan. **Ajanlaskuwidgetit → Näyttötapa → Otavakello** on
vaihtoehtoinen analoginen kello, jossa seitsemän tähden kuvio toimii
symbolisena sekuntiviisarina. Se ei esitä tähtien liikettä sekuntikierrossa.

**Asetukset → Teema → Veri Aika · Veriyö** valitsee sovelluksen oman hyvin
tumman punasävyisen teeman. Windowsin vaalea, tumma ja järjestelmän teema
säilyvät valittavina. **Windowsin ulkoasu** näyttää mukana tulevien
staattisten taustakuvien esikatselut. Avaa valittu kuva ja aseta se
Windowsin kuvankatselussa työpöydän taustakuvaksi. Elävä Otava piirretään
kalenteriin ja widgettiin; taustakuva on kuvitus.

## Windowsin omat teemat

Oletuksena **Windows · järjestelmän teema** ja **Segoe UI**. Sovellus seuraa
Windowsin vaaleaa/tummaa sovellustilaa ja tehosteväriä noin kahden sekunnin
kuluessa. Suuren kontrastin tila käyttää Windowsin järjestelmävärejä myös
silloin, kun sovelluksessa on valittu vaalea tai tumma Windows-teema.

**Asetukset → Teema** tarjoaa myös erilliset vaalean ja tumman tilan valinnat.
Vaaleassa tilassa käytetään Windowsin natiivia Qt-tyyliä; tummassa Qt:n
palettia kunnioittavaa Fusion-tyyliä. Kellot ja säägraafit piirretään samoilla
väreillä. **Käytä valittua teemaa kaikissa widgeteissä** yhdistää niiden ilmeen.

**Windowsin ulkoasu** avaa Windowsin omat teema-, väri-, taustakuva-,
lukitusnäyttö- ja suuren kontrastin asetukset. Työpöydän kuvakkeet ja
taustakuvat valitaan siellä.

## MIKES-aika

Kellot lukevat Windowsin järjestelmäaikaa. Kun Windowsin Internet-aikapalvelin
on jo **time.mikes.fi**, sama synkronoitu aika tulee suoraan sovellukseen.
Sovelluksella ei ole toista NTP-kelloa eikä se muuta Windows Time -palvelua.

**Asetukset → Aika ja sää** näyttää Windowsin tallennetun NTP-palvelinasetuksen
ja avaa Windowsin päivämäärä- ja aika-asetukset. Tallennettu palvelinasetus ei
yksin todista viimeisen synkronoinnin onnistumista. Aikavyöhyke on oletuksena
Europe/Helsinki; kesäaika huomioidaan mukana toimitettavalla tzdata-kirjastolla.

## Asetukset, käynnistys ja päivitys

Kalenterimerkinnät, muistutukset ja asetukset tallentuvat kansioon
`%LOCALAPPDATA%\AjanlaskutJaSaa`. Sovelluskansioon ei tallenneta käyttäjätietoja.
Sääpaikan voi valita nimellä; Windows-versio ei käytä Ubuntun sijaintipalvelua.
Verkottomana kalenterit toimivat ja sää käyttää aiemmin haettua välimuistia.

**Asetukset → Avaa valitut widgetit kirjautuessa** lisää vain tämän sovelluksen
käynnistysarvon nykyisen käyttäjän rekisteriin:
`HKCU\Software\Microsoft\Windows\CurrentVersion\Run\AjanlaskutJaSaa`.
Valinnan poistaminen poistaa arvon. Valitse sovelluskansiolle pysyvä paikka
ennen pikakuvakkeiden tai automaattikäynnistyksen käyttöönottoa.

Päivitys: lopeta sovellus, pura uusi paketti ja käynnistä uusi EXE. Käyttäjätiedot
säilyvät. Jos kansion polku muuttui, luo pikakuvakkeet uudelleen ja poista
automaattikäynnistys käytöstä sekä ota se uudelleen käyttöön uudessa versiossa.

## Toiminnan tarkistus

**Widgetit ja koko näytön pelit · 1.11.2:** sovellus käsittelee näytön resoluution,
käytettävissä olevan työpöytäalueen ja DPI-skaalauksen muutokset. Widgetin valittu
koko palautetaan näyttötilan muutoksen rauhoituttua. Paikka sovitetaan tarvittaessa
tilapäisesti pienemmälle työpöydälle; normaali paikka palautuu näyttötilan palatessa.
Näyttötilan muutos ei tallenna suurentunutta kokoa tai tilapäistä paikkaa asetuksiin.
Pelin aktivoituminen tai hiiren kaappauksen katkeaminen peruu keskeneräisen koonmuutoksen.
Reunoista muuttaminen, yksilöllisten kokojen tallennus ja oletuskoon palautus säilyvät.

**Säähaun yhteydet · 1.11.1:** Windows-paketti sisältää nyt certifin Mozillan
julkiset juurivarmenteet. Niitä käytetään Windowsin oman varmennevaraston lisäksi,
jotta Yr:n ja Ilmatieteen laitoksen HTTPS-haku ei jää riippumaan siitä, mitkä
juurivarmenteet Windowsiin on ennestään asennettu. Palvelimen ja osoitteen
varmennus pysyy käytössä. Päivitys yrittää vanhat epäonnistuneet haut uudestaan;
toimiva välimuisti ja palvelimen ilmoittamat hakurajoitukset säilyvät.

**Tarkista-verkkoyhteys.cmd** kokeilee Yr:n, FMI:n ja Forecan oikeita hakuja
Oulun Oinaansuon koordinaateilla tilapäiskansiossa. Se näyttää haettujen tuntien
määrän tai virheen syyn. Käyttäjän asetuksiin ja säävälimuistiin ei kirjoiteta.
Tämä tarkistus tarvitsee verkkoyhteyden. Sovelluksen virheviestit erottavat nyt
varmennevirheen, aikakatkaisun, osoitteen selvitysvirheen ja HTTP-virhekoodin.

**Tarkista-toiminta.cmd** ajaa eristetyt testit tilapäiskansiossa. Se tarkistaa
Windows-teemat, kellot, aikavyöhykkeet, kalenterimerkinnät, välimuistin
prosessilukituksen ja sovellusten välisen avauspyynnön. Se ei muuta työpöydän
asetuksia, automaattikäynnistystä tai aikapalvelua. Verkkohaku on testissä pois.

## Paketin rakentaminen

Lähdekoodi on paketissa. Lukitut riippuvuudet ja latausten SHA-256-tarkisteet:
`packaging/windows/requirements.txt` ja `packaging/windows/downloads.json`.
Paketin `DEPENDENCIES.json` sisältää samat ladattujen riippuvuuksien tarkisteet.

Lataa Pythonin embeddable ZIP Python.orgista ja Windows x64 -wheelit PyPI:stä
erilliseen välimuistikansioon. Rakenna Zig 0.15.2:lla Linuxissa tai Windowsissa:

```
python packaging/build_windows.py --output outputs/windows --cache DOWNLOADS --zig PATH/TO/zig
```

Rakentaja tarkistaa lataukset ennen purkamista. Se ei lataa tai asenna mitään
eikä sisällytä käyttäjän tietoja. `SHA256SUMS` sisältää valmiin ZIPin tarkisteen.
