# Veriyö Live 0.1.0 · Ubuntu ja Windows

Erillinen elävä taustakuvasovellus. Ei tarvitse Ajanlaskut ja Sää -asennusta.

- **[Asenna Ubuntuun: veriyo-live_0.1.0_all.deb](veriyo-live_0.1.0_all.deb?raw=true)**
- **[Windows ZIP ja julkaisun tiedot](https://github.com/Jakke77/Ajanlaskut-ja-Saa/releases/tag/veriyo-live-v0.1.0)**
- [Lähdekoodi ZIP](Veriyo-Live-0.1.0-lahdekoodi.zip?raw=true)
- [Käyttöohje ja lukitusnäytön rajat](KAYTTOOHJE.md)
- [Tarkisteet](SHA256SUMS)

Ubuntu:

```bash
sudo apt install ./veriyo-live_0.1.0_all.deb
```

Avaa **Veriyö Live**, kokeile esikatselua ja paina **Ota elävä tausta käyttöön**.
Sovellus käyttää paikkaa 65.071562, 25.507046. Valittavana Otava ja järvi tai Hiillos.
Työpöytä päivittyy oletuksena minuutin välein. Lukituskuva on ajantasainen pysäytyskuva;
jo avoimen lukitusnäytön virkistymistä käyttöjärjestelmä ei takaa.

![Veriyö Live](application.png)

![Otava ja järvi](otava-live.png)

Lähdecommit: `480837702b00bef1d118c506c2d87b217fab578c`. Kaikki 54 lähdetiedostoa verrattu byteittäin Debianiin ja
lähde-ZIP:iin. Molempien sisältä ajetut 29 testiä ja PNG-vienti läpäisivät tarkistukset.
GNOMEn oikeat gsettings/D-Bus/dconf-kirjoitukset, jatkaminen ja palautus tarkistettiin
yksityisessä testi-istunnossa. Käyttäjän varsinaista GNOME-/Windows-lukitusnäyttöä
ei ole pilviympäristössä. Katso [tarkistusraportti](QA-package.json).

Windowsin pakattu ajonaikainen ympäristö läpäisi samat testit (yksi vain Linuxille tarkoitettu testi ohitettiin), PNG-viennin ja natiivin taustakuvapolun lukemisen. [Windows-tarkistusloki](QA-native-windows.log) · [lopullinen toimitusraportti](QA-final-delivery.json).
