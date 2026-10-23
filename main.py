#!/usr/bin/env python3
"""Ajanlaskut ja Sää: single application, shared calendar and weather widgets."""
import argparse
import os
from pathlib import Path
import sys

def main():
    parser=argparse.ArgumentParser(description='Ajanlaskut ja Sää')
    parser.add_argument('--widgets-only',action='store_true',help='Näytä vain valitut työpöytäwidgetit')
    parser.add_argument('--no-widgets',action='store_true',help='Avaa sovellus ilman työpöytäwidgetejä')
    parser.add_argument('--page',choices=['overview','calendar','sunmoon','names','clocks','weather','widgets','settings','wallpapers'])
    parser.add_argument('--offline',action='store_true',help='Käytä vain paikallista säävälimuistia')
    parser.add_argument('--data-dir',type=Path,help='Erillinen asetusten ja kalenterin hakemisto')
    parser.add_argument('--self-test',action='store_true',help='Eristetty testi ilman verkkohakuja')
    parser.add_argument('--preview-dir',type=Path,help='Testin käyttöliittymäkuvat')
    from asaa import VERSION
    parser.add_argument('--version',action='version',version='Ajanlaskut ja Sää '+VERSION)
    args=parser.parse_args()
    if args.self_test:os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
    elif sys.platform.startswith('linux') and os.environ.get('DISPLAY'):os.environ.setdefault('QT_QPA_PLATFORM','xcb')
    from PyQt6.QtCore import QCoreApplication,Qt
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    from asaa.app import run
    return run(args)

if __name__=='__main__':raise SystemExit(main())
