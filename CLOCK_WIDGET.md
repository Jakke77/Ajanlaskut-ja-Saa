# Komponentti: yhteinen ajanlaskuwidget · 1.2.0

## Tarve ja nykyiset mallit

Erilliset Varjoajan, Tähtiajan ja gregoriaanisen kellot vievät turhaan samaa tilaa.
Uusi `DesktopSurface('combined')` käyttää samaa lasipaneelia, fonttimittausta,
taustakuva- ja kalenteripainikkeita kuin vanhat kellot. Säägraafin/kartan omaa
piirtoa, välimuistia, paikkaa tai palveluasetuksia ei muuteta.

## Ominaisuudet ja variantit

| Ominaisuus | Oletus | Toiminta |
|---|---|---|
| Vaihtotapa | järjestyksessä | kiinteä valinta, järjestys tai satunnainen |
| Ajanlaskut | kaikki kolme | vähintään yksi, satunnainen ei toista heti samaa |
| Vaihtoväli | 77 sekuntia | 1–3600 s, ei sama asetus kuin sään 77 minuuttia |
| Kelloteema | ajanlaskun oma | vaihtoehtona sovelluksen yhteinen Kupari/Halla |
| Varjoaika | Kupari | nykyinen kuparipaletti ja kiertoradat |
| Tähtiaika | Astraali | tumma vihertävä pohja ja kultainen korostus |
| Gregoriaaninen | Aamunkajo | sinertävä pohja ja vaalea kalenteriruudukko |
| Sisältö | kello, päiväys, päivänimi, vaihe, tavallinen päiväys, vyöhyke, sää | merkintä ja seuraava muistutus valinnaiset |

Värit ovat `theme.py`:n `CALENDAR_THEMES`-tunnuksia. Paneelin säde on 16,
sisäleveys 430, tekstin reunaväli 22 loogista pikseliä. Sisältökoostumus käyttää
`clock_config.clock_layout`-paikkoja. Piilotettu kenttä supistaa paneelia, mutta
ajanlaskun vaihtuminen ei muuta paneelin kokoa tai sijaintia. Kaikki kolme
ajanlaskua näyttävät tavallisen paikallisen kellonajan, eivät eri nopeudella käyviä kelloja.

## Tilat ja vuorovaikutus

- Normaalitila: vain valitut kentät ja käynnissä olevan ajanlaskun värit.
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
avaa yhteisen kellon ja sääwidgetin. Painike **Korvaa erilliset kellot** piilottaa
vain kolme erillistä kellopaneelia. Niiden sisällöt ja vanhat sijainnit säilyvät.
Yhteinen kello perii ensimmäisen näkyvän vanhan kellon sijainnin.

Kuusi oikeaa rinnakkaiskalenteria ovat erillistä lisätietoa Tähtiajan valitusta
päivästä, eivät uusi sääntö sen 510 päivän kierrolle. Master-valinta piilottaa
sekä lisätiedot, päiväruutujen lisäpäiväyksen että lisäkalenterien tooltipit.
Kukin kalenteri valitaan erikseen; näyttöpaikka on Tähtiaika tai kaikki kalenterit.
Kellojen symboliset kuuvaiheet eivät muutu tähtitieteellisiksi kuuvaiheiksi.
