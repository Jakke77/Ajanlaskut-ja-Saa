"""Explicit, asynchronous place search with disambiguated results."""
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QListWidget, QDialogButtonBox)
from .providers import search_places

class SearchThread(QThread):
    result = pyqtSignal(object, str)
    def __init__(self, query, parent):
        super().__init__(parent)
        self.query = query
    def run(self):
        try:
            self.result.emit(search_places(self.query),'')
        except Exception:
            self.result.emit([], 'Paikkahaku ei onnistunut. Tarkista yhteys ja yritä uudelleen.')

class PlaceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Hae ennustepaikka')
        self.resize(450,350)
        self.worker = None
        self.places = []
        self.place = None
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        self.query = QLineEdit()
        self.query.setPlaceholderText('Esim. Kuivasjärvi tai Helsinki')
        self.query.setAccessibleName('Paikan nimi')
        self.search = QPushButton('Hae')
        row.addWidget(self.query); row.addWidget(self.search)
        layout.addLayout(row)
        self.status = QLabel('Valitse tuloksista oikea paikkakunta.')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.results = QListWidget()
        self.results.setAccessibleName('Paikkahaun tulokset')
        layout.addWidget(self.results)
        layout.addWidget(QLabel('Paikkahaku: Open-Meteo / GeoNames'))
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Käytä paikkaa')
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self.buttons.accepted.connect(self.select)
        self.buttons.rejected.connect(self.reject)
        self.results.currentRowChanged.connect(lambda i: self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(i>=0))
        self.results.itemDoubleClicked.connect(lambda _: self.select())
        layout.addWidget(self.buttons)
        self.search.clicked.connect(self.start)
        self.query.returnPressed.connect(self.start)

    def start(self):
        if self.worker and self.worker.isRunning(): return
        if len(self.query.text().strip()) < 2:
            self.status.setText('Kirjoita vähintään kaksi merkkiä.'); return
        self.results.clear(); self.places = []
        self.status.setText('Haetaan paikkoja…'); self.search.setEnabled(False)
        self.worker = SearchThread(self.query.text(),self)
        self.worker.result.connect(self.received)
        self.worker.finished.connect(self.finished_search)
        self.worker.start()

    def received(self, places, error):
        self.places = places
        self.results.addItems([p.name for p in places])
        self.status.setText(error or ('Valitse oikea paikkakunta.' if places else 'Paikkaa ei löytynyt. Kokeile lähintä kaupunkia.'))

    def finished_search(self):
        self.search.setEnabled(True)
        self.worker.deleteLater(); self.worker = None

    def select(self):
        i = self.results.currentRow()
        if 0 <= i < len(self.places):
            self.place = self.places[i]; self.accept()

    def done(self, result):
        # Bound by the 15-second HTTP timeout; never destroy a running QThread.
        if self.worker and self.worker.isRunning(): self.worker.wait()
        super().done(result)
