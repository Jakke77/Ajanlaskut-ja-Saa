#!/usr/bin/env python3
"""Piirtää alkuperäisen Ubuntu-fanitaustakuvan Pythonin vakiokirjastolla."""
from math import cos, radians, sin
from pathlib import Path
from random import Random

ROOT = Path(__file__).resolve().parent
WIDTH, HEIGHT = 1920, 1080
CX, CY = 610, 540


def point(radius, angle):
    theta = radians(angle)
    return f"{CX + radius * cos(theta):.3f},{CY + radius * sin(theta):.3f}"


def arc(radius, start, end):
    return f"M{point(radius, start)}A{radius},{radius} 0 {int(end-start > 180)},1 {point(radius, end)}"


def artwork():
    layers = ['''<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080" role="img" aria-labelledby="title desc">
<title id="title">Ubuntu · oranssi tähtikello</title>
<desc id="desc">Itsenäinen Ubuntu-fanitaustakuva: oranssi kolmen kiertoratasolmun tunnus tähtikellon sisällä, tumma munakoisonvärinen tausta ja rauhallinen oikea reuna. Alkuperäinen SVG-vektoripiirros, 10.10.2026.</desc>
<defs>
  <linearGradient id="background" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="#21162a"/><stop offset=".52" stop-color="#17121f"/><stop offset="1" stop-color="#100e17"/>
  </linearGradient>
  <radialGradient id="ambient" cx=".32" cy=".50" r=".44">
    <stop stop-color="#562735" stop-opacity=".58"/><stop offset=".45" stop-color="#3c2033" stop-opacity=".28"/><stop offset="1" stop-color="#17121f" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="dial" cx=".43" cy=".40" r=".7">
    <stop stop-color="#35202f" stop-opacity=".82"/><stop offset=".7" stop-color="#201725" stop-opacity=".75"/><stop offset="1" stop-color="#17121f" stop-opacity=".2"/>
  </radialGradient>
  <radialGradient id="halo">
    <stop stop-color="#e95420" stop-opacity=".09"/><stop offset=".64" stop-color="#e95420" stop-opacity=".025"/><stop offset="1" stop-color="#e95420" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="orange" x1=".1" y1="0" x2=".9" y2="1">
    <stop stop-color="#ff8a4c"/><stop offset=".48" stop-color="#e95420"/><stop offset="1" stop-color="#bd371d"/>
  </linearGradient>
  <linearGradient id="rim" x1=".1" y1="0" x2=".9" y2="1">
    <stop stop-color="#d08461" stop-opacity=".85"/><stop offset=".4" stop-color="#6e3c36" stop-opacity=".65"/><stop offset=".7" stop-color="#e95420" stop-opacity=".7"/><stop offset="1" stop-color="#6e3c36" stop-opacity=".1"/>
  </linearGradient>
  <linearGradient id="horizon" x1="0" y1="0" x2="1" y2="0">
    <stop stop-color="#6e3c36" stop-opacity="0"/><stop offset=".25" stop-color="#6e3c36" stop-opacity=".24"/><stop offset=".58" stop-color="#6e3c36" stop-opacity=".05"/><stop offset="1" stop-color="#6e3c36" stop-opacity="0"/>
  </linearGradient>
</defs>
<rect width="1920" height="1080" fill="url(#background)"/>
<rect width="1920" height="1080" fill="url(#ambient)"/>
<path d="M120 884C550 856 860 878 1500 904M178 912C540 894 910 914 1590 930" fill="none" stroke="url(#horizon)" stroke-width="1"/>
<circle cx="610" cy="540" r="475" fill="url(#halo)"/>
''']
    # Sparse, deterministic stars stop before the quiet right-hand widget region.
    random = Random(20261010)
    for _ in range(45):
        x, y = random.uniform(168, 1160), random.uniform(132, 970)
        if ((x-CX)**2 + (y-CY)**2)**.5 < 395:
            continue
        radius = random.choice((.7, .9, 1.2))
        opacity = random.uniform(.15, .35)
        layers.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius}" fill="#c6aebd" opacity="{opacity:.3f}"/>')
    layers.append('''
<g fill="none">
  <ellipse cx="610" cy="540" rx="442" ry="174" transform="rotate(-27 610 540)" stroke="#b97a60" stroke-opacity=".19" stroke-width="1"/>
  <ellipse cx="610" cy="540" rx="425" ry="161" transform="rotate(-27 610 540)" stroke="#6e3c36" stroke-opacity=".28" stroke-width=".7"/>
  <ellipse cx="610" cy="540" rx="388" ry="258" transform="rotate(41 610 540)" stroke="#6e3c36" stroke-opacity=".14"/>
  <circle cx="610" cy="540" r="367" stroke="#6e3c36" stroke-opacity=".16"/>
  <circle cx="610" cy="540" r="351" stroke="#6e3c36" stroke-opacity=".14" stroke-dasharray="1 14"/>
  <circle cx="610" cy="540" r="330" fill="url(#dial)" stroke="url(#rim)" stroke-width="1.2"/>
  <circle cx="610" cy="540" r="325" stroke="#6e3c36" stroke-opacity=".5"/>
  <circle cx="610" cy="540" r="280" stroke="#6e3c36" stroke-opacity=".35" stroke-width=".8"/>
  <circle cx="610" cy="540" r="255" stroke="#6e3c36" stroke-opacity=".3"/>
  <circle cx="610" cy="540" r="240" stroke="#c6aebd" stroke-opacity=".11" stroke-width=".8"/>
</g>
''')
    # Mechanical dial marks suggest timekeeping without numbers or interface text.
    for index in range(120):
        angle = index * 3 - 90
        major = index % 10 == 0
        middle = index % 5 == 0
        end = 297 if major else 304 if middle else 310
        color = "#e95420" if major else "#c6aebd"
        opacity = .82 if major else .32 if middle else .16
        layers.append(f'<path d="M{point(317, angle)}L{point(end, angle)}" stroke="{color}" opacity="{opacity}" stroke-width="{2 if major else 1}"/>')
    layers.append('''
<g fill="none" stroke-linecap="round">
  <path d="M610 186A354 354 0 0 1 864 294" stroke="#e95420" stroke-width="1.8" stroke-opacity=".7"/>
  <path d="M287 686A354 354 0 0 0 575 892" stroke="#c6aebd" stroke-width=".8" stroke-opacity=".22"/>
  <path d="M936 587A330 330 0 0 1 818 796" stroke="#e95420" stroke-width="2" stroke-opacity=".75"/>
  <path d="M506 294A267 267 0 0 1 828 386" stroke="#c6aebd" stroke-width=".8" stroke-opacity=".17"/>
  <path d="M371 622A253 253 0 0 0 640 791" stroke="#e95420" stroke-width=".8" stroke-opacity=".37"/>
  <path d="M610 272V294M610 786V808M342 540H364M856 540H878" stroke="#c6aebd" stroke-opacity=".13"/>
</g>
<!-- Three orbital nodes form an original interpretation of the Ubuntu emblem. -->
<g fill="none" stroke="url(#orange)" stroke-width="26" stroke-linecap="round">
''')
    for start in (42, 162, 282):
        layers.append(f'<path d="{arc(148, start, start+96)}"/>')
    layers.append('</g>')
    for angle in (-90, 30, 150):
        x, y = point(191, angle).split(",")
        layers.append(f'<circle cx="{x}" cy="{y}" r="24" fill="url(#orange)"/>')
        layers.append(f'<circle cx="{x}" cy="{y}" r="32" fill="none" stroke="#e95420" stroke-opacity=".1"/>')
    # A small central stellar jewel anchors the orbital emblem.
    layers.append('''
<circle cx="610" cy="540" r="99" fill="none" stroke="#6e3c36" stroke-opacity=".22" stroke-width=".8"/>
<path d="M610 523L614 536L627 540L614 544L610 557L606 544L593 540L606 536Z" fill="#fff4ed" fill-opacity=".78"/>
<circle cx="610" cy="540" r="3" fill="#e95420"/>
<circle cx="999" cy="342" r="5" fill="#e95420"/>
<circle cx="999" cy="342" r="12" fill="none" stroke="#e95420" stroke-opacity=".15"/>
<circle cx="236" cy="727" r="3" fill="#c6aebd" fill-opacity=".48"/>
<circle cx="274" cy="395" r="2.5" fill="#c6aebd" fill-opacity=".3"/>
</svg>
''')
    return "\n".join(layers)


def main():
    output = ROOT / "ubuntu-oranssi-tahtikello.svg"
    output.write_text(artwork(), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
