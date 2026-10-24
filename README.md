# Ajanlaskut ja Sää 1.12.2 · Ruutukalenteri ja nimikirja

**[Lataa Ubuntu-deb](https://github.com/Jakke77/Ajanlaskut-ja-Saa/raw/refs/heads/packages/v1.12.2/ajanlaskut-ja-saa_1.12.2_all.deb)**
· [Windows 10/11 x64](https://github.com/Jakke77/Ajanlaskut-ja-Saa/releases/tag/windows-v1.12.2)
· [Lähdekoodin ZIP](https://github.com/Jakke77/Ajanlaskut-ja-Saa/raw/refs/heads/packages/v1.12.2/Ajanlaskut-ja-Saa-1.12.2-lahdekoodi.zip)
· [SHA256SUMS](SHA256SUMS).

Yksityinen repo edellyttää GitHubiin kirjautumista.

## Veri Aika Kalenterit-sivulla

Valitse **Kalenterit → Veri Aika**. Samalla sivulla näkyy seitsemän sarakkeen
ruutukalenteri, jossa on viisi viikkoa eli 35 päivää kerrallaan. Vuodessa on
edelleen **777 päivää eli 111 viikkoa**. Viimeisessä selausjaksossa on yksi
viikko. Selausjaksot eivät ole uusia kuukausia.

Valitse päivän ruutu: päivän nimet, merkitykset ja yhteiset kalenterimerkinnät
näkyvät päivän tiedoissa. Leveässä ikkunassa tiedot ovat ruudukon oikealla
puolella, pienessä sen alla. Myös Otavan yhteydessä oleva Veri Aika -sivu
käyttää samaa monirivistä kalenteria.

## Nimet ja niiden merkitykset

**Nimikalenterit → Veri Ajan nimikirja** sisältää kaikkien **1 554 nimen**
selitykset ja haun. Selityksen voi kopioida talteen. Syntymäpäivä valitaan
edelleen **Nimikalenterit → Oma nimi** -välilehdellä.

Sanatausta ja sen lähteet ovat erikseen nimelle kirjoitetusta symbolisesta
merkityksestä. Kaikki nimikirjan henkilökohtaiset vertauskuvat on merkitty
kirjaimellisella `**`-merkillä ja selitteellä **`** tämän keksin :)`**.
Samankaltainen nimi ei todista historiallista alkuperää. Esimerkiksi:

- **Venosis:** Kotiin palaavan elämänvirran muistaja. `**`
- **Venosisa:** Kotiin palaavan elämänvirran säilyttäjä. `**`
- **Rubino:** Rubiininpunaisen elinvoiman kantaja. `**`

Taustoissa on 37 nimiryhmää ja 18 tarkistettua lähdettä. Alkuperäiset
777 nimiparia ja niiden päiväsijoitukset säilyivät tavulleen samoina.

**Säilytettävä nimikirja:** [Markdown-versio](Veri-Ajan-nimikirja.md) ja
[ladattava HTML-versio](https://github.com/Jakke77/Ajanlaskut-ja-Saa/raw/refs/heads/packages/v1.12.2/Veri-Ajan-nimikirja.html).
Tallenna HTML omalle koneelle ja avaa selaimessa. Nimikirjan haku ja tulostus
toimivat ilman sovellusta tai verkkoyhteyttä; vain lähdelinkin avaaminen käyttää
verkkoa. Sovelluksen **Avaa tulostettava nimikirja** avaa saman tiedoston.
Selaimen tulostuksesta nimikirjan voi myös tallentaa PDF:ksi.

## Päivitys

Ubuntu: avaa pääte latauskansioon ja suorita:

```bash
sudo apt install ./ajanlaskut-ja-saa_1.12.2_all.deb
```

Sulje vanha ohjelma **Lopeta sovellus** -painikkeella, ja avaa päivitetty asennus:

```bash
/usr/bin/ajanlaskut-ja-saa --page calendar
/usr/bin/ajanlaskut-ja-saa --version
```

Versioksi tulee **1.12.2**. `codex-ajanlasku` on erillinen käyttäjäasennus;
[sen päivitysohje](https://github.com/Jakke77/Ajanlaskut-ja-Saa/blob/codex/veri-namebook-calendar/UPDATES.md)
on lähdekoodin mukana. Molemmat asennukset käyttävät samoja asetuksia ja merkintöjä.

Windows: pura uusi ZIP uuteen pysyvään kansioon. Sulje vanha sovellus ja
avaa uuden kansion **Ajanlaskut-ja-Saa.exe**. **Luo-pikakuvakkeet.cmd**
päivittää pikakuvakkeet uuteen kansioon. Pythonia ei tarvitse asentaa erikseen.
Asetukset ja merkinnät säilyvät käyttäjän tietokansiossa.

## Tarkistukset

**419 Ubuntu-yksikkö- ja Qt-testiä läpäisi.** Kaikki 777 päivää näkyvät
23 selausjaksossa täsmälleen kerran. Vuoden raja, Suomen aikaraja, merkinnät,
syntymäpäivähaku, selitysten kopiointi ja 1560×1000/1020×720-asettelu tarkistettiin.
Valmiin deb-paketin ja lähde-ZIPin kaikki **2 332 tiedostoa** vastaavat lähdettä;
myös turvallinen käyttäjäpäivittimen purku ja puretun version käynnistys tarkistettiin.

HTML:n haku, päivä- ja viikkosuodatus, tyhjä tulos, haun tyhjennys ja 500 pikselin
näkymä testattiin oikealla Qt Chromium -selaimella. Mukana olevat HTML- ja
Markdown-tiedostot vastaavat täsmälleen generaattorin tulosta.

[Testiloki](QA-unit.log) · [Pakettivertailu](QA-package.json) · [Qt-tarkistus](QA-ui.json)
· [HTML-selaintesti](QA-namebook-browser.json) · [Nimikirjan tarkistus](QA-namebook-export.json).

![Veri Ajan ruutukalenteri ja päivän selitykset](veri-ruutukalenteri.png)
![Veri Ajan nimikirjan haku ja lähteet](veri-nimikirja.png)
