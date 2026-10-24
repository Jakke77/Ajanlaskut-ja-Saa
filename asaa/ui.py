"""Unified dashboard, calendars, forecasts, widget controls and appearance."""
import copy
from datetime import date, datetime, time
from zoneinfo import available_timezones
from PyQt6.QtCore import Qt, QTimer, QRectF, QTime, QUrl
from PyQt6.QtGui import QPainter, QFont, QDesktopServices
from PyQt6.QtWidgets import (QMainWindow, QWidget, QFrame, QLabel, QPushButton, QToolButton,
    QHBoxLayout, QVBoxLayout, QGridLayout, QStackedWidget, QScrollArea, QComboBox,
    QSpinBox, QFontComboBox, QCheckBox, QFormLayout, QTextEdit, QDialog, QDialogButtonBox,
    QTimeEdit, QMessageBox, QLineEdit, QSizePolicy, QButtonGroup, QSplitter)
from .calendar import NAMES, MONTHS, WEEKDAYS
from .models import shadow, star
from .theme import THEMES, THEME_LABELS, paint_panel, available_themes
from .state import DEFAULTS
from . import almanac
from . import VERSION
from .widgets import WIDGET_LABELS
from .widget_themes import widget_theme, widget_theme_choices, widget_theme_selection
from .color_control import ColorControl
from .weather.providers import NAMES as SOURCES, slots, aligned, common_scales
from .weather.windy_view import WindyView, WeatherWebView
from .platform_support import IS_WINDOWS

def label(value, name=None, wrap=False):
    item = QLabel(value)
    if name: item.setObjectName(name)
    item.setWordWrap(wrap)
    return item

def button(value, action, primary=False):
    item = QPushButton(value)
    if primary: item.setObjectName('primary')
    item.clicked.connect(action)
    return item

def card():
    frame = QFrame(); frame.setObjectName('card')
    layout = QVBoxLayout(frame); layout.setContentsMargins(22,18,22,18); layout.setSpacing(9)
    return frame, layout

class OrbitBanner(QFrame):
    def __init__(self, controller):
        super().__init__(); self.controller = controller
        self.setMinimumHeight(170)
        layout = QVBoxLayout(self); layout.setContentsMargins(28,20,28,20)
        layout.addWidget(label('YKSI HETKI · NELJÄ AJANLASKUA', 'eyebrow'))
        self.clock = label('', 'clock'); layout.addWidget(self.clock)
        self.subtitle = label('', 'muted'); layout.addWidget(self.subtitle)
        controller.clock_changed.connect(self.tick); self.tick()
    def tick(self):
        now = self.controller.calendars.now()
        self.clock.setText(now.strftime('%H:%M:%S' if self.controller.options['seconds'] else '%H:%M'))
        self.subtitle.setText(f'{now:%d.%m.%Y} · {self.controller.options["zone"]}  /  {self.controller.weather.place.name}')
    def paintEvent(self,event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        paint_panel(p,QRectF(self.rect()),THEMES[self.controller.options['theme']]);p.end()

class ForecastView(QWidget):
    def __init__(self, controller, count=12):
        super().__init__(); self.controller = controller; self.count = count
        self.setMinimumSize(550, 350)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        controller.weather.changed.connect(self.update)
        controller.settings_changed.connect(self.update)
    def drawing_size(self):
        width = max(1040 if self.count == 24 else 880, 460*self.width()/max(1,self.height()))
        return width, self.height()*width/max(1,self.width())
    def paintEvent(self,event):
        owner = self.controller.weather
        times = slots(owner.times[0], count=self.count)
        scales = common_scales(owner.forecasts.values(),times)
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        width,height = self.drawing_size()
        p.scale(self.width()/width, self.height()/height)
        owner.paint_content(p,width=width,height=height,times=times,scales=scales,expanded=True)
        p.end()
        self.setAccessibleName(owner.accessibleName())
    def mouseMoveEvent(self,event):
        owner = self.controller.weather
        width,_ = self.drawing_size()
        index = round((event.position().x()*width/self.width()-64)/((width-136)/(self.count-1)))
        times = slots(owner.times[0],count=self.count)
        hours = aligned(owner.forecast,times)
        if 0 <= index < len(hours) and hours[index]:
            item = hours[index]
            self.setToolTip(f'{item.time.astimezone(self.controller.calendars.zone):%d.%m. %H:%M %Z}\n'
                f'{item.temperature:.1f} °C · tuuli {item.wind:.1f} m/s\n'
                + (f'Sade {item.rain:.1f} mm' if item.rain is not None else 'Sademäärä puuttuu'))
        else: self.setToolTip('Tälle tunnille ei ole ennustetietoa.')

class OverviewPage(QWidget):
    def __init__(self, controller):
        super().__init__(); self.controller = controller
        layout = QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(16)
        layout.addWidget(OrbitBanner(controller))
        row=QHBoxLayout();self.date_labels={};self.note_labels={}
        for system in ('shadow','star','civil'):
            frame, content=card()
            content.addWidget(label(NAMES[system].upper(),'eyebrow'))
            value=label('','',True);value.setStyleSheet('font-size:20px;font-weight:bold;')
            detail=label('','muted',True)
            content.addWidget(value);content.addWidget(detail);content.addStretch(1)
            content.addWidget(button('Avaa kalenteri →',lambda _, s=system:controller.open_calendar(s)))
            self.date_labels[system]=value;self.note_labels[system]=detail
            row.addWidget(frame)
        layout.addLayout(row)
        frame, content=card()
        blood_row=QHBoxLayout();words=QVBoxLayout()
        words.addWidget(label('VERI AIKA · SEITSEMÄN TÄHTEÄ','eyebrow'))
        value=label('','',True);value.setStyleSheet('font-size:22px;font-weight:bold;')
        detail=label('','muted',True)
        words.addWidget(value);words.addWidget(detail)
        words.addWidget(button('Avaa Veri Aika →',lambda:controller.open_calendar('blood')))
        blood_row.addLayout(words,1)
        from .otava_ui import OtavaView
        self.otava=OtavaView(controller,compact=True)
        self.otava.setMaximumWidth(270)
        blood_row.addWidget(self.otava)
        content.addLayout(blood_row);layout.addWidget(frame)
        self.date_labels['blood']=value;self.note_labels['blood']=detail
        self.source_row=QHBoxLayout()
        self.source_row.addWidget(label('SÄÄ · SEURAAVAT 12 TUNTIA','eyebrow'));self.source_row.addStretch(1)
        self.source_row.addWidget(button('Avaa sää →',lambda:controller.open_page('weather')))
        layout.addLayout(self.source_row)
        self.forecast=ForecastView(controller);layout.addWidget(self.forecast,1)
        self.summary=label('','muted',True);layout.addWidget(self.summary)
        controller.clock_changed.connect(self.tick);controller.daily.changed.connect(self.tick)
        self.tick()
    def tick(self):
        now=self.controller.calendars.now()
        for system in self.date_labels:
            try:
                item=self.controller.calendars.at(system,now)
                self.date_labels[system].setText(item.label)
                if system=='blood':
                    from .blood_time import next_week
                    self.note_labels[system].setText('Alku 26.6.2026 klo 01:07:07 · Suomen aikaa\n'
                        f'Seuraava viikko {next_week(now):%d.%m. %H:%M:%S %Z}\nOtava näyttää Oulun taivaan todellisen asennon.')
                    continue
                from .astronomy import moon_at
                try:phase=moon_at(now).label
                except ValueError:phase=item.phase
                self.note_labels[system].setText(phase+('\n'+item.names.label if item.names else ''))
            except ValueError:
                self.date_labels[system].setText('Ennen ajanlaskun alkua');self.note_labels[system].setText('')
        lines=self.controller.daily.lines()
        self.summary.setText('KOLMEN PÄIVÄN ENNUSTE · wttr.in\n'+'\n'.join(lines) if lines else 'Kolmen päivän ennuste latautuu taustalla.')

class NoteDialog(QDialog):
    def __init__(self,controller,day,parent):
        super().__init__(parent);self.controller=controller;self.day=day
        self.setWindowTitle('Päivän merkintä');self.resize(530,410)
        layout=QVBoxLayout(self)
        layout.addWidget(label(f'{day:%d.%m.%Y}','heading'))
        for system in ('shadow','star'):
            try:layout.addWidget(label(controller.calendars.convert(system,day).label,'muted'))
            except ValueError:pass
        self.editor=QTextEdit();self.editor.setPlainText(controller.state.note(day));self.editor.setPlaceholderText('Kirjoita päivän tapahtumat tai muistiinpanot…')
        layout.addWidget(self.editor)
        self.remind=QCheckBox('Muistuta tästä päivästä');layout.addWidget(self.remind)
        self.at=QTimeEdit(QTime(18,0));self.at.setDisplayFormat('HH:mm');layout.addWidget(self.at)
        self.message=label('Sama merkintä näkyy kaikissa ajanlaskuissa.','muted',True);layout.addWidget(self.message)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText('Tallenna')
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('Peruuta')
        buttons.accepted.connect(self.save);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
    def save(self):
        try:
            if self.remind.isChecked():
                when=self.at.time()
                instant=datetime.combine(self.day,time(when.hour(),when.minute()),self.controller.calendars.zone)
                if instant.astimezone(__import__('datetime').timezone.utc).astimezone(self.controller.calendars.zone).replace(tzinfo=None) != instant.replace(tzinfo=None):
                    raise ValueError('Tätä kellonaikaa ei ole kesäaikaan siirtymisen vuoksi.')
                if instant <= self.controller.calendars.now():raise ValueError('Muistutuksen pitää olla tulevaisuudessa.')
                if not self.editor.toPlainText().strip():raise ValueError('Kirjoita muistutuksen teksti.')
            self.controller.state.save_note(self.day,self.editor.toPlainText(), instant if self.remind.isChecked() else None)
            self.controller.notes_changed.emit();self.accept()
        except (OSError,ValueError) as error:self.message.setText(str(error))

class CalendarPage(QWidget):
    def __init__(self,controller):
        super().__init__();self.controller=controller;self.system='shadow';self.selected=controller.calendars.now().date();self.month=None
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(14)
        layout.addWidget(label('KALENTERIT','eyebrow'))
        self.heading=label('','heading');layout.addWidget(self.heading)
        top=QHBoxLayout();self.selector=QComboBox()
        for key,title in NAMES.items():self.selector.addItem(title,key)
        self.selector.currentIndexChanged.connect(self.change_system);top.addWidget(self.selector)
        top.addStretch(1)
        top.addWidget(button('‹',lambda:self.step(-1)));top.addWidget(button('Tänään',self.today));top.addWidget(button('›',lambda:self.step(1)))
        self.year=QSpinBox();self.year.setRange(1,9998);self.year.setPrefix('Vuosi ');self.year.valueChanged.connect(self.change_year);top.addWidget(self.year)
        self.month_box=QComboBox();self.month_box.currentIndexChanged.connect(self.change_month);top.addWidget(self.month_box)
        layout.addLayout(top)
        extras_row=QHBoxLayout()
        self.extras_visible=QCheckBox('Näytä kuu-, aurinko- ja kuu–aurinkokalenterit')
        self.extras_visible.setChecked(controller.options['calendar_extras_visible'])
        self.extras_visible.toggled.connect(self.toggle_extras);extras_row.addWidget(self.extras_visible)
        extras_row.addStretch(1);extras_row.addWidget(button('Valitse lisäkalenterit…',self.configure_extras))
        layout.addLayout(extras_row)
        tools=QHBoxLayout()
        tools.addWidget(button('Oma nimesi ajanlaskuissa →',self.open_names))
        tools.addWidget(button('Suomalainen kuukalenteri →',self.open_folk_calendar))
        tools.addWidget(button('Kuu, valo ja aurinko →',self.open_sunmoon))
        layout.addLayout(tools)
        split=QHBoxLayout();frame,grid_content=card();self.grid=QGridLayout();self.grid.setSpacing(7);grid_content.addLayout(self.grid)
        split.addWidget(frame,3)
        detail,content=card();detail.setMinimumWidth(240);detail.setMaximumWidth(310)
        content.addWidget(label('VALITTU PÄIVÄ','eyebrow'));self.day_heading=label('','',True);self.day_heading.setStyleSheet('font-size:20px;font-weight:bold;');content.addWidget(self.day_heading)
        self.parallel=label('','muted',True);content.addWidget(self.parallel)
        self.extras=label('','muted',True);content.addWidget(self.extras)
        self.note=label('','',True);content.addWidget(self.note);content.addStretch(1)
        content.addWidget(button('Muokkaa merkintää',self.edit_note,True));split.addWidget(detail,1)
        self.cancel=button('Peru päivän muistutukset',self.cancel_reminders);content.addWidget(self.cancel)
        layout.addLayout(split,1)
        self.info=label('','muted',True);layout.addWidget(self.info)
        self.cell_info=label('','muted',True);layout.addWidget(self.cell_info)
        self.reminders=label('','muted',True);layout.addWidget(self.reminders)
        controller.notes_changed.connect(self.render);controller.settings_changed.connect(self.extras_changed);self.set_day('shadow',self.selected)
    def toggle_extras(self, checked):
        try:self.controller.configure({'calendar_extras_visible':checked})
        except (ValueError,OSError) as error:
            self.extras_changed();self.controller.storage_error(error)
    def open_folk_calendar(self):
        page=self.controller.window.page_widgets['names']
        page.show_folk(self.selected)
        self.controller.open_page('names')
    def open_names(self):
        page=self.controller.window.page_widgets['names']
        page.set_day(self.selected);page.tabs.setCurrentIndex(0)
        self.controller.open_page('names')
    def open_sunmoon(self):
        self.controller.window.page_widgets['sunmoon'].set_day(self.selected)
        self.controller.open_page('sunmoon')
    def configure_extras(self):
        from .almanac_ui import AlmanacDialog
        AlmanacDialog(self.controller,self).exec()
    def extras_changed(self):
        self.extras_visible.blockSignals(True);self.extras_visible.setChecked(self.controller.options['calendar_extras_visible']);self.extras_visible.blockSignals(False)
        scope='Tähtiajan kalenterissa' if self.controller.options['calendar_extras_scope']=='star' else 'kaikissa kalentereissa'
        self.extras_visible.setText('Näytä lisäkalenterit '+scope)
        self.render()
    def set_day(self,system,civil=None):
        civil=civil or self.controller.calendars.now().date()
        try:item=self.controller.calendars.convert(system,civil)
        except ValueError:
            civil=self.controller.calendars.civil_date(system,1,0,0);item=self.controller.calendars.convert(system,civil)
        self.system,self.selected,self.month=system,civil,(item.year,item.month)
        self.selector.blockSignals(True);self.selector.setCurrentIndex(self.selector.findData(system));self.selector.blockSignals(False)
        self.month_box.blockSignals(True);self.month_box.clear()
        self.month_box.addItems(shadow.MONTH_NAMES if system=='shadow' else star.MONTHS if system=='star' else MONTHS)
        self.month_box.blockSignals(False);self.render()
    def change_system(self):
        system=self.selector.currentData()
        if system=='blood':
            self.selector.blockSignals(True);self.selector.setCurrentIndex(self.selector.findData(self.system));self.selector.blockSignals(False)
            self.controller.open_calendar('blood',self.selected)
            return
        self.set_day(system,self.selected)
    def today(self):self.set_day(self.system)
    def step(self,delta):
        self.month=self.controller.calendars.step_month(self.system,*self.month,delta);self.render()
    def change_year(self,value):
        if self.month:self.month=(value,self.month[1]);self.render()
    def change_month(self,index):
        if self.month and index>=0:self.month=(self.month[0],index);self.render()
    def select(self,item):self.selected=item.civil;self.render_detail();self.render()
    def render(self):
        while self.grid.count():
            old=self.grid.takeAt(0)
            if old.widget():old.widget().hide();old.widget().deleteLater()
        self.month=self.controller.calendars.bound_month(self.system,*self.month)
        days=self.controller.calendars.month_days(self.system,*self.month)
        self.heading.setText(f'{days[0].month_name} · '+('kierto ' if self.system=='star' else 'vuosi ')+str(self.month[0]))
        self.year.blockSignals(True);self.year.setMaximum(self.controller.calendars.last_month(self.system)[0]);self.year.setValue(self.month[0]);self.year.blockSignals(False)
        self.month_box.blockSignals(True);self.month_box.setCurrentIndex(self.month[1]);self.month_box.blockSignals(False)
        names=shadow.WEEKDAY_SHORT_NAMES if self.system=='shadow' else star.SHORT_WEEKDAYS if self.system=='star' else ('Ma','Ti','Ke','To','Pe','La','Su')
        for row in range(7):self.grid.setRowStretch(row,0)
        for i,word in enumerate(names):
            heading=label(word,'muted');heading.setMaximumHeight(28)
            self.grid.addWidget(heading,0,i)
        today=self.controller.calendars.now().date();offset=days[0].weekday
        theme=THEMES[self.controller.options['theme']]
        self.day_buttons=[]
        for i,item in enumerate(days):
            number=str(item.day)
            if self.controller.state.note(item.civil):number+='  •'
            extra_key=self.controller.options['calendar_extra_cell']
            if almanac.visible(self.controller.options,self.system) and extra_key!='none':
                extra=almanac.convert(extra_key,item.civil)
                if extra.available:number+=f'\n{extra.day}.{extra.month}.'
            cell=button(number,lambda _, d=item:self.select(d));cell.setMinimumHeight(64)
            cell.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
            cell.setCheckable(True);cell.setChecked(item.civil==self.selected)
            cell.setToolTip(f'{item.label}\n{item.civil:%d.%m.%Y}\n{self.controller.state.note(item.civil)}')
            if item.names:cell.setToolTip(cell.toolTip()+'\n'+item.names.label)
            extra_lines=almanac.lines(self.controller.options,self.system,item.civil)
            if extra_lines:cell.setToolTip(cell.toolTip()+'\n\n'+'\n\n'.join(extra_lines))
            if item.civil==today and item.civil!=self.selected:cell.setStyleSheet(f'border:2px solid {theme.accent};font-weight:bold;')
            self.grid.addWidget(cell,1+(i+offset)//7,(i+offset)%7);self.day_buttons.append(cell)
            self.grid.setRowStretch(1+(i+offset)//7,1)
        self.info.setText({'shadow':'Varjoaika · 13 × 30 = 390 päivää. Alkupäivä 28.9.2026. Päivät 0–29.',
            'star':f'Tähtiaika · 17 × 30 = 510 päivää. Alkupäivä {self.controller.options["star_epoch"]}. Päivät 0–29.',
            'civil':'Tavallinen gregoriaaninen kalenteri. Kuukaudet ja karkauspäivät noudattavat normaalia ajanlaskua.'}[self.system])
        cell_key=self.controller.options['calendar_extra_cell']
        has_cell=almanac.visible(self.controller.options,self.system) and cell_key!='none'
        self.cell_info.setText('Ruutujen lisäpäiväys: '+almanac.SPECS[cell_key].title+' · päivä.kuukausi. Koko päiväys näkyy päivän tiedoissa ja osoittamalla ruutua.' if has_cell else '')
        self.cell_info.setVisible(has_cell)
        self.render_detail()
    def render_detail(self):
        item=self.controller.calendars.convert(self.system,self.selected)
        self.day_heading.setText(item.label)
        lines=[f'{self.selected:%d.%m.%Y}',item.phase+f'\nKlo 12 · {self.controller.options["zone"]}']
        if item.names:lines.append('NIMIPARI\n'+item.names.label)
        for system in ('shadow','star'):
            if system!=self.system:
                try:lines.append(self.controller.calendars.convert(system,self.selected).label)
                except ValueError:pass
        self.parallel.setText('\n\n'.join(lines))
        extra_lines=almanac.lines(self.controller.options,self.system,self.selected)
        self.extras.setText('RINNAKKAISKALENTERIT\n\n'+'\n\n'.join(extra_lines) if extra_lines else '')
        self.extras.setVisible(bool(extra_lines))
        self.note.setText(self.controller.state.note(self.selected) or 'Ei merkintää tälle päivälle.')
        upcoming=[r for r in self.controller.state.data['reminders'] if not r['delivered']]
        self.day_reminders=[r['id'] for r in upcoming if datetime.fromisoformat(r['due']).astimezone(self.controller.calendars.zone).date()==self.selected]
        self.cancel.setVisible(bool(self.day_reminders))
        self.reminders.setText('SEURAAVAT MUISTUTUKSET\n'+'\n'.join(f'{datetime.fromisoformat(r["due"]).astimezone(self.controller.calendars.zone):%d.%m. %H:%M} · {r["title"][:70]}' for r in sorted(upcoming,key=lambda r:r['due'])[:3]) if upcoming else 'Ei odottavia muistutuksia.')
    def edit_note(self):NoteDialog(self.controller,self.selected,self).exec()
    def cancel_reminders(self):
        answer=QMessageBox.question(self,'Peru muistutukset',f'Perutaanko päivän {self.selected:%d.%m.%Y} {len(self.day_reminders)} muistutusta?',
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
        if answer!=QMessageBox.StandardButton.Yes:return
        try:self.controller.state.cancel_reminders(self.day_reminders);self.controller.notes_changed.emit()
        except OSError as error:self.controller.storage_error(error)

class WeatherPage(QWidget):
    def __init__(self,controller):
        super().__init__();self.controller=controller;self.windy=None;self.weather_web=None
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(12)
        layout.addWidget(label('ENNUSTE JA SÄÄKARTTA','eyebrow'))
        self.title=label('Sää','heading');layout.addWidget(self.title)
        top=QHBoxLayout();self.provider=QComboBox()
        for key,value in SOURCES.items():self.provider.addItem(value,key)
        self.provider.addItem('WINDY','windy');self.provider.setAccessibleName('Sääpalvelu');top.addWidget(self.provider)
        top.addWidget(label('Näkymä'))
        self.view=QComboBox();self.view.setAccessibleName('Sään näkymä');top.addWidget(self.view)
        self.count=QComboBox();self.count.addItem('24 tuntia',24);self.count.addItem('12 tuntia',12);top.addWidget(self.count)
        top.addStretch(1)
        top.addWidget(button('Hae paikka',controller.weather.open_place));top.addWidget(button('◎ Sijainti',controller.weather.locate));top.addWidget(button('Päivitä',controller.weather.refresh))
        layout.addLayout(top)
        extras=QHBoxLayout();extras.addStretch(1)
        extras.addWidget(button('Muita sadekarttoja · RainViewer ↗',lambda:QDesktopServices.openUrl(QUrl('https://www.rainviewer.com/weather-radar-map-live.html'))))
        layout.addLayout(extras)
        self.stack=QStackedWidget();self.forecast=ForecastView(controller,24);self.stack.addWidget(self.forecast);layout.addWidget(self.stack,1)
        self.summary=label('','muted',True);layout.addWidget(self.summary)
        self.provider.currentIndexChanged.connect(self.select_provider)
        self.view.currentIndexChanged.connect(self.select_view)
        self.count.currentIndexChanged.connect(self.change_count)
        controller.weather.changed.connect(self.sync);controller.daily.changed.connect(self.sync)
        controller.weather.web_reload_requested.connect(self.reload_web)
        self.sync()
    def select_provider(self):
        try:self.controller.weather.select_provider(self.provider.currentData())
        except (OSError,ValueError) as error:self.controller.storage_error(error)
        self.sync()
    def select_view(self):
        if self.view.currentData() is not None:
            try:self.controller.weather.set_view_mode(self.view.currentData())
            except (OSError,ValueError) as error:self.controller.storage_error(error)
            self.sync()
    def change_count(self):self.forecast.count=self.count.currentData();self.forecast.update()
    def sync(self):
        owner=self.controller.weather
        self.title.setText(owner.place.name)
        self.provider.blockSignals(True);self.provider.setCurrentIndex(self.provider.findData(owner.selected));self.provider.blockSignals(False)
        self.view.blockSignals(True);self.view.clear()
        for mode in owner.available_view_modes:
            title=('Tuntiennuste' if owner.selected=='windy' else 'Ennustegraafi') if mode=='graph' else ('Sääkartta' if owner.selected=='windy' else 'Sadekartta')
            self.view.addItem(title,mode)
        self.view.setCurrentIndex(self.view.findData(owner.view_mode));self.view.setEnabled(self.view.count()>1);self.view.blockSignals(False)
        self.count.setEnabled(not owner.uses_web_view)
        self.count.setVisible(not owner.uses_web_view)
        if owner.uses_web_view and self.isVisible():
            self.show_web()
        else:self.stack.setCurrentWidget(self.forecast)
        if owner.uses_web_view:
            if owner.selected=='fmi':
                detail='Ilmatieteen laitos · Suomen sadekartta, havainnot ja sade-ennuste'
            elif owner.selected=='foreca':
                detail='Foreca · sadetutka ja sade-ennuste'
            elif owner.view_mode=='graph':
                detail='Windyn tuntiennuste · lämpötila, tuuli, sääsymbolit ja sade'
            else:
                detail='Windy · sääkartta'
            self.summary.setText(detail)
        else:
            self.summary.setText('Varjosää · wttr.in\n'+'\n'.join(self.controller.daily.lines())+'\n\nHaetaan '+str(self.controller.options['refresh_minutes'])+' minuutin välein. Lämpö on ennuste; sade on tunnin kertymä.')
    def show_windy(self,*,force=False):
        owner=self.controller.weather
        if owner.selected!='windy' or owner.view_mode!='map' or not self.isVisible():return
        if self.windy is None:
            self.windy=WindyView(network=owner.network_enabled);self.stack.addWidget(self.windy)
        self.stack.setCurrentWidget(self.windy)
        self.windy.load(owner.place,owner.options['windy_zoom'],owner.options['windy_layer'],force=force)
    def show_web(self,*,force=False):
        owner=self.controller.weather
        if not owner.uses_web_view or not self.isVisible():return
        if owner.selected=='windy' and owner.view_mode=='map':
            self.show_windy(force=force);return
        if self.weather_web is None:
            self.weather_web=WeatherWebView(network=owner.network_enabled);self.stack.addWidget(self.weather_web)
        self.stack.setCurrentWidget(self.weather_web)
        self.weather_web.load_source(owner.selected,owner.view_mode,owner.place,
            owner.options['windy_zoom'],owner.options['windy_layer'],owner.foreca_source_url,force=force)
    def reload_web(self):self.show_web(force=True)
    def reload_windy(self):self.show_windy(force=True)
    def stop_web_views(self):
        for view in (self.windy,self.weather_web):
            if view is not None:view.stop()
    def showEvent(self,event):super().showEvent(event);self.sync()

class WidgetsPage(QWidget):
    def __init__(self,controller):
        super().__init__();self.controller=controller;self.checks={};self.themes={};self.text_colors={}
        self.theme_drafts={};self.edited_themes=set();self.loading=True
        self.text_color_drafts={};self.edited_text_colors=set()
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(12)
        layout.addWidget(label('TYÖPÖYDÄN NÄKYMÄT','eyebrow'));layout.addWidget(label('Valitse omat widgetisi','heading'))
        layout.addWidget(label('Näkyvyys vaihtuu heti. Valitse jokaiselle widgetille oma teema ja tekstiväri. Tallenna ulkoasuvalinnat, kun ne ovat sopivat. Fontti ja sääpaikka ovat yhteiset.','muted',True))
        layout.addWidget(button('Vaihtuva kello · ajanlaskut ja sisältö',lambda:controller.open_page('clocks')))
        layout.addWidget(button('Näytä valitut widgetit',controller.restore_widgets,True))
        layout.addWidget(button('Vaihda työpöydän tai lukitusnäytön taustakuvaa',lambda:controller.open_page('wallpapers')))
        for key,title in WIDGET_LABELS.items():
            frame,content=card();row=QHBoxLayout();row.addWidget(label(title));row.addStretch(1)
            check=QCheckBox('Näytä työpöydällä');check.setChecked(controller.options['widgets'][key])
            check.toggled.connect(lambda checked,k=key:controller.set_widget(k,checked));row.addWidget(check)
            content.addLayout(row)
            theme=QComboBox();theme.setAccessibleName(title+' · Teema')
            for name,token in widget_theme_choices(key):theme.addItem(name,token)
            color=ColorControl(title=title+' · Valitse tekstiväri')
            color.changed.connect(lambda k=key:self.change_text_color(k))
            form=QFormLayout();form.addRow('Teema',theme);form.addRow('Tekstiväri',color);content.addLayout(form)
            theme.currentIndexChanged.connect(lambda _,k=key:self.change_theme(k))
            layout.addWidget(frame);self.checks[key]=check;self.themes[key]=theme;self.text_colors[key]=color
        self.status=label('Ulkoasuvalinnat otetaan käyttöön tallentamalla.','muted',True);layout.addWidget(self.status)
        layout.addWidget(button('Tallenna widgettien ulkoasu',self.save,True))
        layout.addStretch(1)
        layout.addWidget(button('Palauta widgetien paikat',controller.reset_positions))
        controller.settings_changed.connect(self.sync)
        controller.clock_changed.connect(self.refresh_color_inheritance)
        self.loading=False;self.sync()

    def change_theme(self,key):
        if self.loading:return
        self.theme_drafts[key]=self.themes[key].currentData();self.edited_themes.add(key)
        self.text_colors[key].set_inherited_color(self.base_text_color(key))
        self.status.setText('Ulkoasua muutettu — tallenna, kun valinnat ovat sopivat.')

    def base_text_color(self,key,options=None):
        options=self.controller.options if options is None else options
        system=self.controller.time_rotation.current if key=='combined' else key.split('_')[0]
        return widget_theme({**options,'widget_text_colors':{}},key,system,selection=self.theme_drafts[key]).text

    def refresh_color_inheritance(self):
        if self.loading:return
        options=self.controller.options
        for key,color in self.text_colors.items():color.set_inherited_color(self.base_text_color(key,options))

    def change_text_color(self,key):
        if self.loading:return
        self.text_color_drafts[key]=self.text_colors[key].value;self.edited_text_colors.add(key)
        self.status.setText('Ulkoasua muutettu — tallenna, kun valinnat ovat sopivat.')

    def save(self):
        if not (self.edited_themes or self.edited_text_colors):
            self.status.setText('Ei uusia ulkoasuvalintoja tallennettavana.');return
        options=self.controller.options;changes={}
        if self.edited_themes:
            selections=copy.deepcopy(options.get('widget_themes',{}))
            for key in self.edited_themes:selections[key]=self.theme_drafts[key]
            changes['widget_themes']=selections
        if self.edited_text_colors:
            colors=copy.deepcopy(options.get('widget_text_colors',{}))
            for key in self.edited_text_colors:
                if self.text_color_drafts[key] is None:colors.pop(key,None)
                else:colors[key]=self.text_color_drafts[key]
            changes['widget_text_colors']=colors
        try:
            self.controller.configure(changes)
            self.edited_themes.clear();self.edited_text_colors.clear();self.sync()
            self.status.setText('Tallennettu — widgettien omat teemat ja tekstivärit on otettu käyttöön.')
        except (OSError,ValueError,KeyError) as error:self.status.setText(str(error))

    def sync(self):
        self.loading=True;options=self.controller.options
        for key,check in self.checks.items():
            check.blockSignals(True);check.setChecked(options['widgets'][key]);check.blockSignals(False)
            if key not in self.edited_themes:self.theme_drafts[key]=widget_theme_selection(options,key)
            self.themes[key].setCurrentIndex(self.themes[key].findData(self.theme_drafts[key]))
            if key not in self.edited_text_colors:self.text_color_drafts[key]=options.get('widget_text_colors',{}).get(key)
            self.text_colors[key].load(self.text_color_drafts[key],self.base_text_color(key,options))
        self.loading=False

    def showEvent(self,event):
        super().showEvent(event);self.sync()

class SettingsPage(QWidget):
    def __init__(self,controller):
        super().__init__();self.controller=controller
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(14)
        layout.addWidget(label('YHTEISET ASETUKSET','eyebrow'))
        heading=QHBoxLayout();heading.addWidget(label('Yksi ilme, kaikki näkymät','heading'));heading.addStretch(1)
        heading.addWidget(button('Tallenna',self.save,True));layout.addLayout(heading)
        appearance,form_box=card();form_box.addWidget(label('Ulkoasu ja työpöytä','eyebrow'));form=QFormLayout();form.setSpacing(12)
        self.theme=QComboBox()
        for key in available_themes():self.theme.addItem(THEME_LABELS[key],key)
        self.all_widgets_theme=QCheckBox('Käytä valittua teemaa kaikissa widgeteissä')
        self.all_widgets_theme.setToolTip('Tallennettaessa widgettien omat teemavalinnat korvataan yhteisellä teemalla.')
        from .wallpaper_options import ThemeWallpaperOptions,IconThemeActions
        if IS_WINDOWS:
            from .windows_ui import WindowsThemeOptions
            self.wallpaper_options=WindowsThemeOptions(controller)
        else:self.wallpaper_options=ThemeWallpaperOptions(controller)
        self.font=QFontComboBox();self.scale=QSpinBox();self.scale.setRange(60,150);self.scale.setSuffix(' %')
        self.scale.setToolTip('Oletuskoko widgeteille, joille ei ole vedetty omaa kokoa. Palauta yksittäisen widgetin oletuskoko sen oikean painikkeen valikosta.')
        self.text_scale=QSpinBox();self.text_scale.setRange(80,160);self.text_scale.setSuffix(' %')
        self.text_scale.setAccessibleName('Widgettien tekstikoko')
        self.text_scale.setToolTip('Päiväykset, säätekstit, otsikot ja kuukausien päivät. Ei muuta widgetin kokoa.')
        self.clock_scale=QSpinBox();self.clock_scale.setRange(80,140);self.clock_scale.setSuffix(' %')
        self.clock_scale.setAccessibleName('Yhteinen kellon numerokoko')
        self.clock_scale.setToolTip('Oletuskoko digikelloille, jotka käyttävät yhteistä numerokokoa, ja analogisen kellotaulun numeroille. Kellon oman digikoon ja näyttötavan voi valita Ajanlaskuwidgetit-sivulla.')
        self.opacity=QSpinBox();self.opacity.setRange(0,100);self.opacity.setSuffix(' %')
        for word,item in [('Teema',self.theme),('Fontti',self.font),('Widgettien tekstikoko',self.text_scale),('Yhteinen kellon numerokoko',self.clock_scale),('Widgetien koko',self.scale),('Taustan peittävyys',self.opacity)]:form.addRow(word,item)
        form.addRow('',button('Kellon oma numerokoko ja näyttötapa →',lambda:controller.open_page('clocks')))
        form.addRow('',self.all_widgets_theme)
        form.addRow(self.wallpaper_options)
        form.addRow('',label('Tekstikoko ei muuta widgetin kokoa. Pitkät tekstit sovitetaan käytettävissä olevaan tilaan.','muted',True))
        self.seconds=QCheckBox('Näytä sekunnit');self.locked=QCheckBox('Lukitse widgetien paikat');self.top=QCheckBox('Pidä widgetit muiden ikkunoiden päällä')
        self.locked.setToolTip('Estää widgetin siirtämisen. Kokoa voi silti muuttaa reunoista ja kulmista.')
        self.top.setToolTip('Koskee muita sovelluksia. Oman sovelluksen pääikkuna ja valintaikkunat näytetään aina widgettien edessä.')
        self.clock_weather=QCheckBox('Näytä kolmen päivän sää Varjoaika-kellossa')
        self.sound=QCheckBox('Soita huhuilu muistutuksen yhteydessä');self.autostart=QCheckBox('Avaa valitut widgetit kirjautuessa')
        for item in [self.seconds,self.locked,self.top,self.clock_weather,self.sound,self.autostart]:form.addRow('',item)
        form_box.addLayout(form);layout.addWidget(appearance)
        if not IS_WINDOWS:
            icons,icon_box=card();self.icon_actions=IconThemeActions(controller)
            icon_box.addWidget(self.icon_actions);layout.addWidget(icons)
        layout.addWidget(button('Windowsin ulkoasu' if IS_WINDOWS else 'Taustakuvat · työpöytä ja lukitusnäyttö',lambda:controller.open_page('wallpapers')))
        layout.addWidget(button('Ajanlaskut ja kellojen näkyvä sisältö',lambda:controller.open_page('clocks')))
        layout.addWidget(button('Widgettien omat teemavalinnat',lambda:controller.open_page('widgets')))
        weather,box=card();box.addWidget(label('Aika ja sää','eyebrow'));form=QFormLayout();form.setSpacing(12)
        self.zone=QComboBox();self.zone.setEditable(True);self.zone.addItems(sorted(available_timezones()))
        self.refresh=QSpinBox();self.refresh.setRange(15,180);self.refresh.setSuffix(' minuuttia')
        self.side=QComboBox();self.side.addItem('Asteroidit · varjo vasemmalla','left');self.side.addItem('Revontulet · varjo oikealla','right');self.side.addItem('Kuukauden mukaan','month')
        self.layer=QComboBox()
        for key,name in [('temp','Lämpötila'),('wind','Tuuli'),('rain','Sade'),('clouds','Pilvet')]:self.layer.addItem(name,key)
        self.zoom=QSpinBox();self.zoom.setRange(3,12)
        self.place=label('','muted',True)
        for word,item in [('Aikavyöhyke',self.zone),('Sään hakuväli',self.refresh),('Tähtiajan päivänimet',self.side),('Windyn kerros',self.layer),('Windyn zoomaus',self.zoom),('Yhteinen sääpaikka',self.place)]:form.addRow(word,item)
        box.addLayout(form);box.addWidget(button('Vaihda sääpaikkaa',controller.weather.open_place));layout.addWidget(weather)
        if IS_WINDOWS:
            from .windows_ui import add_time_settings
            add_time_settings(box)
        self.status=label('','muted',True);layout.addWidget(self.status)
        row=QHBoxLayout();row.addWidget(button('Palauta ulkoasun oletukset',self.reset));row.addStretch(1)
        row.addWidget(button('Tallenna asetukset',self.save,True));layout.addLayout(row)
        layout.addWidget(label('Varjoaika, Tähtiaika ja Veri Aika ovat sovelluksen omia ajanlaskuja. Kuunvaihe ja Otavan asento lasketaan todellisesta ajasta. Otavakellon tähtikuvio toimii symbolisena sekuntiviisarina. Merkinnät ja asetukset tallentuvat tälle koneelle.','muted',True))
        self.about_button=button('Tietoa sovelluksesta',controller.show_about)
        layout.addWidget(self.about_button)
        self.load()
    def load(self):
        options=self.controller.options
        self.wallpaper_options.load()
        for item,key in [(self.theme,'theme'),(self.side,'star_side'),(self.layer,'windy_layer')]:item.setCurrentIndex(item.findData(options[key]))
        self.font.setCurrentFont(QFont(options['font']));self.scale.setValue(options['scale']);self.opacity.setValue(options['opacity'])
        self.text_scale.setValue(options['widget_text_scale']);self.clock_scale.setValue(options['widget_clock_scale'])
        self.zone.setCurrentText(options['zone']);self.refresh.setValue(options['refresh_minutes']);self.zoom.setValue(options['windy_zoom'])
        for item,key in [(self.seconds,'seconds'),(self.locked,'locked'),(self.top,'on_top'),(self.clock_weather,'clock_weather'),(self.sound,'sound'),(self.autostart,'autostart')]:item.setChecked(options[key])
        self.place.setText(options['place']['name'])
    def reset(self):
        self.theme.setCurrentIndex(self.theme.findData(DEFAULTS['theme']));self.font.setCurrentFont(QFont(DEFAULTS['font']));self.scale.setValue(77);self.opacity.setValue(77)
        self.text_scale.setValue(DEFAULTS['widget_text_scale']);self.clock_scale.setValue(DEFAULTS['widget_clock_scale'])
        self.seconds.setChecked(True);self.locked.setChecked(False);self.top.setChecked(False)
        self.all_widgets_theme.setChecked(False)
        self.wallpaper_options.reset()
    def save(self):
        changes={'theme':self.theme.currentData(),'font':self.font.currentFont().family(),'scale':self.scale.value(),'opacity':self.opacity.value(),
            'widget_text_scale':self.text_scale.value(),'widget_clock_scale':self.clock_scale.value(),
            'zone':self.zone.currentText(),'refresh_minutes':self.refresh.value(),'windy_zoom':self.zoom.value(),'windy_layer':self.layer.currentData(),'star_side':self.side.currentData()}
        changes.update({key:item.isChecked() for item,key in [(self.seconds,'seconds'),(self.locked,'locked'),(self.top,'on_top'),(self.clock_weather,'clock_weather'),(self.sound,'sound'),(self.autostart,'autostart')]})
        changes.update(self.wallpaper_options.changes())
        use_for_all=self.all_widgets_theme.isChecked()
        if use_for_all:changes.update({'widget_themes':{},'time_theme':'shared'})
        try:
            self.controller.configure(changes);self.all_widgets_theme.setChecked(False)
            self.status.setText('Tallennettu — valittu teema on käytössä kaikissa widgeteissä.' if use_for_all else
                                'Tallennettu — yhteiset asetukset on otettu käyttöön. Widgettien omat teemat säilyvät.')
        except (OSError,ValueError,KeyError) as error:self.status.setText(str(error))
    def showEvent(self,event):
        super().showEvent(event);self.place.setText(self.controller.options['place']['name'])
        self.clock_weather.setChecked(self.controller.options['clock_weather'])
        self.wallpaper_options.load()

class MainWindow(QMainWindow):
    def __init__(self,controller):
        super().__init__();self.controller=controller
        self.setWindowTitle('Ajanlaskut ja Sää '+VERSION);self.setWindowIcon(controller.icon)
        self.resize(1280,960);self.setMinimumSize(1020,720)
        self.menuBar().setNativeMenuBar(False)
        self.help_menu=self.menuBar().addMenu('Ohje')
        self.about_action=self.help_menu.addAction('Tietoa sovelluksesta',controller.show_about)
        root=QWidget();self.setCentralWidget(root);outer=QHBoxLayout(root);outer.setContentsMargins(0,0,0,0);outer.setSpacing(0)
        sidebar=QFrame();sidebar.setObjectName('sidebar');sidebar.setFixedWidth(218)
        side=QVBoxLayout(sidebar);side.setContentsMargins(18,24,18,20);side.setSpacing(5)
        side.addWidget(label('AJANLASKUT\nJA SÄÄ','eyebrow'));side.addWidget(label('Oma hetki. Omat kalenterit.','muted',True));side.addSpacing(22)
        self.navigation={};group=QButtonGroup(self);group.setExclusive(True)
        for key,title in [('overview','◉  Yleiskatsaus'),('calendar','▦  Kalenterit'),('blood','✧  Veri Aika'),('sunmoon','☼  Valo ja aurinko'),('names','✧  Nimikalenterit'),('clocks','◷  Ajanlaskuwidgetit'),('weather','☁  Sää'),('widgets','◫  Työpöytäwidgetit'),('wallpapers','▧  Taustakuvat'),('settings','⚙  Asetukset')]:
            if IS_WINDOWS and key=='wallpapers':title='▧  Windowsin ulkoasu'
            item=button(title,lambda _,k=key:self.show_page(k));item.setObjectName('nav');item.setCheckable(True);group.addButton(item);side.addWidget(item);self.navigation[key]=item
        side.addStretch(1);self.theme_title=label('','eyebrow',True);side.addWidget(self.theme_title)
        controller.settings_changed.connect(self.sync_theme);self.sync_theme()
        side.addWidget(label('Varjoaika · Tähtiaika · Veri Aika\nYr · Foreca · FMI · Windy','muted',True))
        side.addWidget(button('Lopeta sovellus',controller.quit));outer.addWidget(sidebar)
        content=QWidget();body=QVBoxLayout(content);body.setContentsMargins(26,24,26,18);body.setSpacing(16)
        self.pages=QStackedWidget();self.page_widgets={};self.page_indices={}
        if IS_WINDOWS:
            from .windows_ui import WindowsAppearancePage as WallpapersPage
        else:from .wallpaper_ui import WallpapersPage
        from .clock_ui import ClocksPage
        from .celestial_ui import CelestialPage, NamesPage
        from .blood_ui import VeriPage
        for key,page in [('overview',OverviewPage(controller)),('calendar',CalendarPage(controller)),('blood',VeriPage(controller)),('sunmoon',CelestialPage(controller)),('names',NamesPage(controller)),('clocks',ClocksPage(controller)),('weather',WeatherPage(controller)),('widgets',WidgetsPage(controller)),('wallpapers',WallpapersPage(controller)),('settings',SettingsPage(controller))]:
            self.page_widgets[key]=page
            scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(page)
            self.page_indices[key]=self.pages.addWidget(scroll)
        body.addWidget(self.pages,1);self.footer=label('','muted');body.addWidget(self.footer);outer.addWidget(content,1)
        self.show_page('overview');controller.clock_changed.connect(self.tick);self.tick()
        geometry=controller.state.geometry('main')
        if geometry and len(geometry)==4:self.resize(geometry[2],geometry[3]);self.move(geometry[0],geometry[1])
    def show_page(self,key):
        self.pages.setCurrentIndex(self.page_indices[key]);self.navigation[key].setChecked(True)
        if key=='weather':self.page_widgets[key].sync()
    def tick(self):
        self.footer.setText(f'Ajanlaskut ja Sää {VERSION} · {self.controller.calendars.now():%d.%m.%Y %H:%M} · hakuväli {self.controller.options["refresh_minutes"]} min')
    def sync_theme(self):
        self.theme_title.setText(THEME_LABELS[self.controller.options['theme']].upper())
    def closeEvent(self,event):
        if self.controller.stopping:event.accept();return
        try:self.controller.state.geometry('main',(self.x(),self.y(),self.width(),self.height()))
        except OSError as error:self.controller.storage_error(error);event.ignore();return
        if self.controller.visible_widgets() or self.controller.tray is not None:
            self.hide();event.ignore()
        else:event.accept();self.controller.quit()
