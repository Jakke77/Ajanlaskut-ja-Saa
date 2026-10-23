# Tähtitietojen vertailu · 23.10.2026

Vertailulähde: US Naval Observatory, sen viralliset HTTPS-rajapinnat.
Vastaukset haettiin TLS-tarkistusta käyttäen. Sovelluksen laskenta ei kutsu
näitä palveluita; se käyttää mukana olevaa PyMeeus-kirjastoa paikallisesti.

## Oulu 23.10.2026 · 65.0701, 25.5071 · Europe/Helsinki

| Tapahtuma | USNO | Sovellus |
| --- | --- | --- |
| Auringonnousu | 08:36 | 08:36 |
| Auringonlasku | 17:27 | 17:27 |
| Siviilihämärän alku | 07:44 | 07:44 |
| Siviilihämärän loppu | 18:19 | 18:19 |
| Kuunnousu | 16:47 | 16:47 |
| Kuunlasku | 04:09 | 04:09 |

[Alkuperäinen JSON-vastaus ja lähdeosoite](references/oulu.json).

## New York 8.3.2026 · kellonsiirtopäivä

Auringonnousu 07:19 ja lasku 18:55 täsmäsivät USNO:n minuuttilukemiin.
Kuu laski 09:23 eikä noussut kyseisenä päivänä. Sovellus säilytti laskun,
näytti nousun puuttumisen eikä tulkinnut Kuuta koko päiväksi horisontin alle.
Paikallinen päivä oli 23 tunnin mittainen.

[Alkuperäinen JSON-vastaus ja lähdeosoite](references/new-york.json).
USNO-pyynnöissä annettiin vertailupäivän kiinteä UTC-siirtymä (+3 / −4).
Sovellus käyttää IANA-aikavyöhykkeitä myös tuleville tapahtumille.

## Kuunvaiheet ja reunatapaukset

USNO:n vuoden 2026 [UTC-vaihetaulukko](https://aa.usno.navy.mil/api/moon/phases/year?year=2026):
uusikuu 10.10. 15:50, ensimmäinen neljännes 18.10. 16:12 ja täysikuu
26.10. 04:12. Laskennan ero oli alle kaksi minuuttia. Tuleva täysikuu näkyy
Suomessa **26.10. klo 06:12**, sillä kesäaika päättyy jo 25.10.

Testit kattavat myös 19.10.2026 kuvan ristiriidan, oikean kasvavan/vähenevän
sirpin, Helsingin 23/25 tunnin päivät, Tromssan yöttömän yön, kaamoksen ja
talven siviilihämärän. Vuosien 1899–2101 talvipäivänseisauksen edellinen
uusikuu tarkistettiin koko ilmoitetun 1900–2100-alueen ja sen reunojen vuoksi.
Kuuvuodessa on 12 tai 13 lunatiota. Vaahtokuu seuraa helmikuuta, kuukausissa
on 29 tai 30 päivää, eikä kuukausien väliin jää aukkoja.

Suomalaisen kuukalenterin sääntö on sovelluksen oma, käyttöliittymässä selvästi
merkitty tulkinta. Keksityt nimiparit ovat erillistä sovelluksen aineistoa.
Nousuajat kuvaavat tasaisen horisontin ja vakioidun ilmakehän laskennallista
yläreunaa; maastoa ja todellista säätä ei mallinneta.
