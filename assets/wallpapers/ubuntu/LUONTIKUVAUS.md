# Ubuntu · oranssi tähtikello

Alkuperäinen käsin sommiteltu SVG-vektoripiirros, tehty 10.10.2026 tätä
teemarepoa varten. Kuva ei käytä ladattuja kuvia, fontteja tai ulkoisia
vektorielementtejä. Se ei ole kuvanluontipalvelun tuotos.

Lähde: `ubuntu-oranssi-tahtikello.svg`. PNG on viety Inkscapella kokoon
**1920 × 1080** pikseliä. Taustakuva on kokonaan peittävä.
`luo-taustakuva.py` tuottaa SVG-lähteen uudelleen Pythonin vakiokirjastolla.

## Sommittelu

Munakoison tummat sävyt `#17121f` ja `#2b1b33` muodostavat taustan.
Lämmin oranssi `#e95420` korostaa tähtikellon kehää ja kolmea kiertoratasolmua.
Hienot kehäviivat, pienet tähtipisteet ja vinot kiertoradat keskittyvät
vasempaan kolmannekseen. Oikean reunan 35 prosenttia jää rauhalliseksi ja
tummaksi työpöydän kelloille, kalenterille ja sääwidgeteille. Kuvassa ei ole
tekstejä, kellon numeroita tai käyttöliittymäelementtejä.

Kolmen solmun tunnus on oma geometrinen tulkinta Ubuntu-henkisestä
Circle of Friends -aiheesta. Ubuntu-nimi ja Circle of Friends -tavaramerkki
kuuluvat Canonicalille. Tämä on itsenäinen faniteema, ei Canonicalin
virallinen tai hyväksymä teema.

## Tuottaminen uudelleen

Repon juuressa:

```sh
python3 ubuntu/luo-taustakuva.py
inkscape ubuntu/ubuntu-oranssi-tahtikello.svg \
  --export-type=png --export-width=1920 --export-height=1080 \
  --export-filename=ubuntu/ubuntu-oranssi-tahtikello.png
```

SVG-lähteeseen voi muuttaa värejä ja viivojen sommittelua. Alkuperäinen
sommittelu on myös luontiskriptissä; SVG:n käsin tehdyt muutokset tulee
siirtää skriptiin ennen sen ajamista uudelleen.

## Oikeudet

Kuvaa ja lähdetiedostoja koskee sama yksityisen testausrepon käyttö kuin
repon muitakin kuvia. Erillistä avointa jakelulisenssiä ei ole määritetty;
mahdollinen julkinen julkaisu päätetään erikseen. Tavaramerkkejä ei lisensoida
tämän repon mukana.
