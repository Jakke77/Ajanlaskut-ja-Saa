"""Information about the application instance that is currently running."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QFormLayout, QLabel,
    QLineEdit, QVBoxLayout)


class AboutDialog(QDialog):
    def __init__(self, version, installation_root, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Tietoa sovelluksesta')
        self.setModal(True)
        self.resize(580, 300)
        layout=QVBoxLayout(self);layout.setSpacing(14)
        self.name=QLabel('Ajanlaskut ja Sää');self.name.setObjectName('heading')
        self.name.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.name)
        self.version=QLabel('Versio '+version)
        self.version.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.version)
        description=QLabel('Ajanlaskut, kalenterit, sää ja työpöytäwidgetit samassa sovelluksessa.')
        description.setWordWrap(True);layout.addWidget(description)
        author=QLabel('Tekijä: Jakke77')
        author.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(author)
        form=QFormLayout()
        self.installation=QLineEdit(str(installation_root));self.installation.setReadOnly(True)
        self.installation.setAccessibleName('Asennuskansio')
        self.installation.setToolTip(str(installation_root))
        form.addRow('Asennuskansio',self.installation);layout.addLayout(form)
        link_color=self.palette().highlight().color().name()
        self.project=QLabel(f'<a href="https://github.com/Jakke77/Ajanlaskut-ja-Saa" style="color:{link_color}">GitHub: Jakke77/Ajanlaskut-ja-Saa</a>')
        self.project.setTextFormat(Qt.TextFormat.RichText)
        self.project.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.project.setOpenExternalLinks(True);self.project.setWordWrap(True)
        layout.addWidget(self.project)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText('Sulje')
        buttons.rejected.connect(self.reject);layout.addWidget(buttons)
