"""Portable, offline Veri Aika name books with explicit authored meanings.

The exported files contain the whole fixed calendar, not user birthdays or
notes.  Browser search runs locally; only opening a source link uses a network.
"""
import argparse
from collections import defaultdict
from datetime import timedelta
from html import escape
from pathlib import Path
from urllib.parse import urlsplit

from .blood_time import DAYS_PER_YEAR, EPOCH_DATE, WEEKS_PER_YEAR

TITLE = 'Veri Ajan nimikirja'
LEGEND = '** tämän keksin :)'
GENDERS = {'male': 'Miehen nimi', 'female': 'Naisen nimi'}
INTRO = ('Nimien symboliset merkitykset on kirjoitettu tätä nimikirjaa varten. '
         'Niitä ei pidä tulkita todisteiksi nimen historiallisesta alkuperästä. '
         'Sanatausta ja vaikutteet esitetään erikseen lähteineen.')
DATES_NOTE = ('Esimerkkipäivämäärät kuuluvat Veri Ajan ensimmäiseen vuoteen, '
              'joka alkaa 26.6.2026 klo 01:07:07 Suomen aikaa. Sama nimi toistuu '
              '777 päivän välein vuodenpäivän mukaan, ei kiinteänä gregoriaanisena nimipäivänä.')


def _entries(entries):
    if entries is None:
        from .blood_names import meanings
        entries = meanings()
    result = tuple(entries)
    for item in result:
        if type(item.day_of_year) is not int or not 1 <= item.day_of_year <= DAYS_PER_YEAR:
            raise ValueError('Nimikirjan vuoden päivän pitää olla 1–777.')
        if item.gender not in GENDERS:
            raise ValueError('Nimikirjan nimityyppi ei ole tuettu.')
    return sorted(result, key=lambda item: (item.day_of_year, item.gender != 'male'))


def _date(day):
    civil = EPOCH_DATE + timedelta(days=day - 1)
    return f'{civil.day}.{civil.month}.{civil.year}'


def _position(day):
    return f'{(day - 1) // 7 + 1}. viikko · {(day - 1) % 7 + 1}. päivä'


def _source_url(url):
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise ValueError('Lähdelinkin pitää olla HTTP- tai HTTPS-osoite.')
    return url


_STYLE = '''
:root { color-scheme:dark; --bg:#070508; --card:#160b12; --border:#56303c;
  --accent:#f0788b; --text:#f5eaf0; --muted:#bfa9b4; }
* { box-sizing:border-box; }
body { max-width:72rem; margin:auto; padding:2rem 1.2rem; background:var(--bg);
  color:var(--text); font:1rem/1.6 system-ui,sans-serif; }
h1 { font-size:clamp(2rem,6vw,3.8rem); margin:.2em 0; line-height:1.15; }
h2 { font-size:1.15rem; margin:0 0 1rem; }
h3 { font-size:1.4rem; margin:.1rem 0; overflow-wrap:anywhere; }
a { color:var(--accent); overflow-wrap:anywhere; }
p { margin:.6rem 0; }
.eyebrow,.meta { color:var(--muted); }
.eyebrow { letter-spacing:.12em; font-size:.8rem; }
.legend { border-left:.25rem solid var(--accent); padding:.6rem 1rem; }
.invented { color:var(--accent); font-weight:bold; white-space:nowrap; }
.controls { margin:2rem 0; padding:1.2rem; background:var(--card);
  border:1px solid var(--border); border-radius:.8rem; }
.filters { display:flex; flex-wrap:wrap; gap:1rem; align-items:end; }
label { display:flex; flex-direction:column; gap:.3rem; }
.query { flex:1 1 19rem; }
input,button { font:inherit; color:inherit; border:1px solid var(--border);
  border-radius:.4rem; padding:.6rem; background:var(--bg); }
input[type=number] { width:7rem; }
button { cursor:pointer; }
input:focus-visible,button:focus-visible,a:focus-visible { outline:3px solid var(--accent);
  outline-offset:3px; }
.day { margin:2.5rem 0; border-top:1px solid var(--border); padding-top:1.2rem; }
.pair { display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,25rem),1fr));
  gap:1rem; }
.entry { padding:1.2rem; background:var(--card); border:1px solid var(--border);
  border-radius:.8rem; min-width:0; }
.entry dt { font-weight:bold; margin-top:.8rem; }
.entry dd { margin:0; }
.entry ul { padding-left:1.2rem; }
.entry li { margin:.3rem 0; }
.print-note { display:none; }
footer { border-top:1px solid var(--border); margin-top:3rem; padding-top:1rem; }
[hidden] { display:none!important; }
@media print {
  :root { color-scheme:light; --bg:white; --card:white; --border:#999;
    --accent:#71152b; --text:black; --muted:#333; }
  body { max-width:none; padding:0; font:10pt/1.4 sans-serif; }
  h1 { font-size:24pt; }
  .controls,.no-results { display:none!important; }
  .print-note { display:block; }
  .day[hidden],.entry[hidden] { display:block!important; }
  .pair { display:block; }
  .entry { break-inside:avoid; margin:.7rem 0; border-radius:0; }
  .day { margin:1.4rem 0; }
  h2 { break-after:avoid; }
  a { text-decoration:none; color:inherit; }
  a::after { content:' (' attr(href) ')'; font-size:8pt; }
}
'''

_SCRIPT = '''
(() => {
  const form = document.querySelector('.controls');
  const query = document.getElementById('query');
  const day = document.getElementById('day');
  const week = document.getElementById('week');
  const sections = Array.from(document.querySelectorAll('.day'));
  const count = document.getElementById('result-count');
  const empty = document.getElementById('no-results');
  const update = () => {
    const words = query.value.normalize('NFKC').toLocaleLowerCase('fi').trim().split(/\\s+/).filter(Boolean);
    const wantedDay = day.value ? Number(day.value) : null;
    const wantedWeek = week.value ? Number(week.value) : null;
    let visible = 0;
    sections.forEach(section => {
      const allowed = (wantedDay === null || Number(section.dataset.day) === wantedDay)
        && (wantedWeek === null || Number(section.dataset.week) === wantedWeek);
      let matches = 0;
      section.querySelectorAll('.entry').forEach(entry => {
        const show = allowed && words.every(word => entry.dataset.search.includes(word));
        entry.hidden = !show;
        if (show) matches += 1;
      });
      section.hidden = !matches;
      visible += matches;
    });
    count.textContent = `${visible} nimeä`;
    empty.hidden = visible !== 0;
  };
  form.addEventListener('submit', event => event.preventDefault());
  [query, day, week].forEach(input => input.addEventListener('input', update));
  document.getElementById('reset').addEventListener('click', () => {
    HTMLFormElement.prototype.reset.call(form); update(); query.focus();
  });
  document.getElementById('print').addEventListener('click', () => window.print());
  update();
})();
'''


def render_html(entries=None):
    """Render a complete standalone document, with local search and print CSS."""
    entries = _entries(entries)
    days = defaultdict(list)
    for item in entries:
        days[item.day_of_year].append(item)
    body = []
    for day, pair in days.items():
        body.append(f'<section class="day" data-day="{day}" data-week="{(day - 1) // 7 + 1}" '
                    f'aria-labelledby="day-{day}"><h2 id="day-{day}">Vuoden päivä {day}/777 · '
                    f'{_position(day)}<br><span class="meta">Esimerkkipäivä {_date(day)}</span></h2><div class="pair">')
        for item in pair:
            gender = GENDERS[item.gender]
            source_words = ' '.join(source.title for source in item.sources)
            search = ' '.join((item.name, item.meaning, item.background, gender,
                               _position(day), _date(day), source_words)).casefold()
            marker = ' <span class="invented" aria-label="tämän keksin">**</span>' if item.invented else ''
            links = ''.join(f'<li><a href="{escape(_source_url(source.url), quote=True)}" '
                            f'target="_blank" rel="noopener noreferrer">{escape(source.title)}</a></li>'
                            for source in item.sources)
            body.append(f'<article class="entry" data-search="{escape(search, quote=True)}" '
                        f'aria-labelledby="name-{day}-{item.gender}"><p class="meta">{gender}</p>'
                        f'<h3 id="name-{day}-{item.gender}">{escape(item.name)}</h3><dl>'
                        f'<dt>Nimen merkitys</dt><dd>{escape(item.meaning)}{marker}</dd>'
                        f'<dt>Sanatausta ja vaikutteet</dt><dd>{escape(item.background)}</dd>'
                        f'</dl><p><strong>Sanataustan lähteet</strong></p><ul>{links}</ul></article>')
        body.append('</div></section>')
    return f'''<!doctype html>
<html lang="fi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer">
<title>{TITLE}</title><style>{_STYLE}</style></head>
<body><header><p class="eyebrow">AJANLASKUT JA SÄÄ · VERI AIKA</p>
<h1>{TITLE}</h1><p>{DAYS_PER_YEAR} päivää · {WEEKS_PER_YEAR} viikkoa · {len(entries)} nimeä</p>
<p>{INTRO}</p><p class="legend"><strong>{LEGEND}</strong><br>
Kaksi tähteä merkitsee sovellusta varten keksittyä symbolista merkitystä.
Lähde kertoo sanataustasta; se ei vahvista keksittyä nimenselitystä.</p>
<p class="meta">{DATES_NOTE}</p></header>
<form class="controls" role="search" aria-label="Hae nimikirjasta"><div class="filters">
<label class="query" for="query">Hae nimeä, merkitystä tai sanataustaa
<input id="query" type="search" autocomplete="off" placeholder="Esimerkiksi Hemera tai sydän"></label>
<label for="day">Vuoden päivä<input id="day" type="number" min="1" max="777" placeholder="1–777"></label>
<label for="week">Viikko<input id="week" type="number" min="1" max="111" placeholder="1–111"></label>
<button id="reset" type="button">Tyhjennä haku</button>
<button id="print" type="button">Tulosta koko nimikirja</button></div>
<p><output id="result-count" aria-live="polite">{len(entries)} nimeä</output></p>
<noscript>Kaikki nimet näkyvät alla. Haku tarvitsee JavaScriptin; tiedosto ei hae tietoja verkosta.</noscript></form>
<p class="print-note">Tuloste sisältää kaikki nimikirjan nimet.</p>
<p id="no-results" class="no-results" hidden>Haulla ei löytynyt nimiä. Kokeile lyhyempää hakua tai tyhjennä suodattimet.</p>
<main>{''.join(body)}</main>
<footer><p>{LEGEND}</p><p>Veri Aika ja sen nimikierto ovat sovelluksen omia.
Nimikirja ei sisällä käyttäjän syntymäpäivää tai kalenterimerkintöjä.
Voit säilyttää tämän tiedoston ja lukea sitä ilman sovellusta tai verkkoyhteyttä.
Verkkoyhteyttä tarvitaan vain, jos avaat lähdelinkin.</p></footer>
<script>{_SCRIPT}</script></body></html>
'''


def _markdown(text):
    return text.replace('\\', '\\\\').replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]').replace('<', '&lt;').replace('>', '&gt;')


def render_markdown(entries=None):
    """Render a portable text archive whose invention marker stays literal in GFM."""
    entries = _entries(entries)
    lines = [f'# {TITLE}', '', f'{DAYS_PER_YEAR} päivää · {WEEKS_PER_YEAR} viikkoa · {len(entries)} nimeä',
             '', INTRO, '', '`**` tämän keksin :)', '',
             'Kaksi tähteä merkitsee keksittyä symbolista merkitystä. Sanataustan lähteet eivät vahvista nimenselitystä.',
             '', DATES_NOTE, '']
    previous = None
    for item in entries:
        day = item.day_of_year
        if day != previous:
            lines.extend([f'## Vuoden päivä {day}/777 · {_position(day)}', '',
                          f'Esimerkkipäivä {_date(day)}.', ''])
            previous = day
        marker = ' `**`' if item.invented else ''
        lines.extend([f'### {_markdown(item.name)} · {GENDERS[item.gender]}', '',
                      f'**Nimen merkitys:** {_markdown(item.meaning)}{marker}', '',
                      f'**Sanatausta ja vaikutteet:** {_markdown(item.background)}', '',
                      '**Sanataustan lähteet:**', ''])
        for source in item.sources:
            url = _source_url(source.url).replace('>', '%3E').replace('<', '%3C')
            lines.append(f'- [{_markdown(source.title)}](<{url}>)')
        lines.append('')
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Vie Veri Ajan nimikirja itsenäiseksi HTML- tai Markdown-tiedostoksi.')
    parser.add_argument('--html', type=Path, help='HTML-tiedoston kohdepolku')
    parser.add_argument('--markdown', type=Path, help='Markdown-tiedoston kohdepolku')
    args = parser.parse_args(argv)
    if not args.html and not args.markdown:
        parser.error('Anna --html, --markdown tai molemmat.')
    if args.html and args.markdown and args.html.resolve() == args.markdown.resolve():
        parser.error('HTML- ja Markdown-tiedostolla pitää olla eri kohdepolut.')
    entries = _entries(None)
    for path, render in ((args.html, render_html), (args.markdown, render_markdown)):
        if path:
            content = render(entries)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
            print(path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
