"""Offline celestial calendar, daylight month table and original name finder."""
from calendar import monthrange
from datetime import date, datetime, timedelta
import math
from zoneinfo import ZoneInfo

from PyQt6.QtCore import QDate, QThread, Qt, pyqtSignal, pyqtSlot, QRectF, QPointF
from PyQt6.QtGui import QColor, QDesktopServices, QPainter, QPainterPath, QPen
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout,
    QDateEdit, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView)

from .astronomy import (moon_at, moon_on, solar_day, lunar_day, phase_events,
                        event_label, duration_label)
from . import finnish_calendar as folk
from .namedays import names_for_day, names_at, cycle_position
from . import blood_time, blood_names
from .models import shadow, star
from .theme import THEMES
from .ui import button, card, label


def date_edit(day):
    edit = QDateEdit(QDate(day.year, day.month, day.day))
    edit.setDisplayFormat('dd.MM.yyyy'); edit.setCalendarPopup(True)
    edit.setDateRange(QDate(1, 1, 1), QDate(9999, 12, 31))
    edit.setAccessibleName('Valittu päivämäärä')
    return edit


def as_date(edit):
    value = edit.date()
    return date(value.year(), value.month(), value.day())


class MoonDisk(QWidget):
    def __init__(self, controller):
        super().__init__(); self.controller = controller; self.info = None
        self.setMinimumSize(100, 100); self.setMaximumSize(150, 150)

    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        radius = min(self.width(), self.height()) * .43
        painter.translate(self.width()/2, self.height()/2)
        theme = THEMES[self.controller.options['theme']]
        painter.setPen(QPen(QColor(theme.muted), 1)); painter.setBrush(QColor(theme.border))
        painter.drawEllipse(QPointF(0, 0), radius, radius)
        if self.info:
            sign = 1 if self.info.angle < 180 else -1
            cosine = math.cos(math.radians(self.info.angle))
            path = QPainterPath()
            for i in range(101):
                y = -radius + 2*radius*i/100
                x = sign * math.sqrt(max(0, radius*radius-y*y))
                if i == 0: path.moveTo(x, y)
                else: path.lineTo(x, y)
            for i in range(100, -1, -1):
                y = -radius + 2*radius*i/100
                x = sign*cosine*math.sqrt(max(0, radius*radius-y*y))
                path.lineTo(x, y)
            path.closeSubpath(); painter.fillPath(path, QColor('#f5efda'))
        painter.end()


class LightBar(QWidget):
    def __init__(self, controller):
        super().__init__(); self.controller=controller; self.data=None
        self.setMinimumHeight(83)

    def paintEvent(self, event):
        if not self.data: return
        painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        theme=THEMES[self.controller.options['theme']]
        left, width = 12, max(1, self.width()-24)
        painter.fillRect(QRectF(left, 26, width, 22), QColor(theme.border))
        start,end=self.data.start.timestamp(),self.data.end.timestamp()
        for horizon, color in [(self.data.astronomical,'#494a75'),
                               (self.data.nautical,'#787ca3'),
                               (self.data.civil,'#bb9676'),(self.data.sun,theme.accent)]:
            for a,b in horizon.segments:
                x=left+width*(a.timestamp()-start)/(end-start)
                painter.fillRect(QRectF(x,26,width*(b.timestamp()-a.timestamp())/(end-start),22),QColor(color))
        painter.setPen(QColor(theme.muted))
        for i in range(5):
            moment=datetime.fromtimestamp(start+(end-start)*i/4,ZoneInfo(self.data.zone))
            x=left+width*i/4
            painter.drawLine(QPointF(x,23),QPointF(x,51))
            text_x=max(left,min(x-25,left+width-50))
            painter.drawText(QRectF(text_x,55,50,23),Qt.AlignmentFlag.AlignCenter,moment.strftime('%H:%M'))
        painter.drawText(QRectF(left,0,width,23),'Pimeä · tähtitieteellinen hämärä · merihämärä · siviilihämärä · päivä')
        painter.end()


class EphemerisWorker(QThread):
    daily_ready=pyqtSignal(object)
    month_ready=pyqtSignal(object)
    failed=pyqtSignal(object)

    def __init__(self, day, place, parent):
        super().__init__(parent);self.day=day;self.place=place
        self.key=(day,place.latitude,place.longitude,place.timezone)

    def run(self):
        try:
            p=self.place;args=(p.latitude,p.longitude,p.timezone)
            sun=solar_day(self.day,*args)
            moon=lunar_day(self.day,*args)
            info=moon_on(self.day,p.timezone)
            phases=[(instant,title) for instant,title in phase_events(self.day)
                    if instant >= sun.start][:4]
            if self.isInterruptionRequested():return
            self.daily_ready.emit((self.key,(sun,moon,info,phases)))
            rows=[]
            for number in range(1,monthrange(self.day.year,self.day.month)[1]+1):
                if self.isInterruptionRequested():return
                day=self.day.replace(day=number)
                rows.append((day,solar_day(day,*args).sun,moon_on(day,p.timezone)))
            if not self.isInterruptionRequested():self.month_ready.emit((self.key,rows))
        except (ValueError,OverflowError) as error:
            if not self.isInterruptionRequested():self.failed.emit((self.key,str(error)))


class CelestialPage(QWidget):
    def __init__(self, controller):
        super().__init__();self.controller=controller;self._key=None;self._workers=[];self._stopped=False
        self._last_day=controller.calendars.now().astimezone(ZoneInfo(controller.weather.place.timezone)).date()
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(14)
        layout.addWidget(label('VALO JA AURINKO','eyebrow'))
        layout.addWidget(label('Kuu ja päivän valo','heading'))
        top=QHBoxLayout();self.date=date_edit(self._last_day);top.addWidget(self.date)
        top.addWidget(button('Tänään',self.today));top.addStretch(1)
        top.addWidget(button('Hae paikka',controller.weather.open_place));layout.addLayout(top)
        self.place_label=label('','muted',True);layout.addWidget(self.place_label)
        row=QHBoxLayout();moon_frame,content=card();moon_row=QHBoxLayout()
        self.disk=MoonDisk(controller);moon_row.addWidget(self.disk)
        self.moon_text=label('','',True);self.moon_text.setStyleSheet('font-size:18px;');moon_row.addWidget(self.moon_text,1)
        content.addLayout(moon_row);self.moon_times=label('','muted',True);content.addWidget(self.moon_times);row.addWidget(moon_frame,1)
        sun_frame,content=card();content.addWidget(label('AURINKO','eyebrow'))
        self.sun_text=label('','',True);self.sun_text.setStyleSheet('font-size:18px;');content.addWidget(self.sun_text)
        self.twilight=label('','muted',True);content.addWidget(self.twilight);row.addWidget(sun_frame,1)
        layout.addLayout(row)
        self.bar=LightBar(controller);layout.addWidget(self.bar)
        self.phases=label('','muted',True);layout.addWidget(self.phases)
        self.status=label('Valitse päivä ja paikka.','muted',True);layout.addWidget(self.status)
        self.table=QTableWidget(0,5);self.table.setHorizontalHeaderLabels(['Päivä','Nousu','Lasku','Päivän pituus','Kuunvaihe klo 12'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setMinimumHeight(260);self.table.setAccessibleName('Kuukauden valoajat')
        self.table.cellClicked.connect(self.choose_row);layout.addWidget(self.table)
        layout.addWidget(label('Nousu- ja laskuajat ovat laskennallisia arvioita tasaiselle horisontille. '
            'Maasto ja sää voivat muuttaa havaittuja aikoja. Auringon nousu käyttää −0,833° ja hämärärajat −6°, −12°, −18°. '
            'Tiedot lasketaan paikallisesti vuosille 1900–2100. Paikka on yhteinen sääsivun kanssa.','muted',True))
        self.date.dateChanged.connect(self.refresh)
        controller.settings_changed.connect(self.refresh)
        controller.weather.changed.connect(self.refresh)
        controller.clock_changed.connect(self.tick)

    def showEvent(self,event):
        super().showEvent(event);self.refresh()

    def today(self):
        p=self.controller.weather.place
        value=self.controller.calendars.now().astimezone(ZoneInfo(p.timezone)).date()
        self.date.setDate(QDate(value.year,value.month,value.day))

    def set_day(self,day):self.date.setDate(QDate(day.year,day.month,day.day))

    def tick(self):
        if not self.isVisible() or self._stopped:return
        day=self.controller.calendars.now().astimezone(ZoneInfo(self.controller.weather.place.timezone)).date()
        if day != self._last_day:
            if as_date(self.date)==self._last_day:self.today()
            self._last_day=day
        self.update_moon()

    def update_moon(self, info=None):
        try:
            place=self.controller.weather.place
            now=self.controller.calendars.now().astimezone(ZoneInfo(place.timezone))
            live=as_date(self.date)==now.date()
            info=moon_at(now) if live else info or moon_on(as_date(self.date),place.timezone)
            self.disk.info=info;self.disk.update()
            self.moon_text.setText(info.label+f'\nKuun ikä {info.age:.1f} vrk\n'+('Tämänhetkinen vaihe' if live else 'Vaihe paikan paikallisaikana klo 12'))
            self.disk.setAccessibleName(info.label)
        except ValueError:pass

    def refresh(self,*_):
        if self._stopped or not self.isVisible():return
        p=self.controller.weather.place;day=as_date(self.date)
        key=(day,p.latitude,p.longitude,p.timezone)
        if key==self._key:return
        self._key=key
        for worker in self._workers:worker.requestInterruption()
        self.place_label.setText(f'{p.name} · {p.latitude:.4f}, {p.longitude:.4f} · paikallisaika {p.timezone}')
        self.status.setText('Lasketaan nousuajat ja kuukauden valoajat…')
        self.table.setRowCount(0);self.sun_text.clear();self.moon_times.clear();self.twilight.clear();self.phases.clear()
        self.moon_text.clear();self.disk.info=None;self.disk.update();self.bar.data=None;self.bar.update()
        worker=EphemerisWorker(day,p,self);self._workers.append(worker)
        # Bound QObject slots also disconnect queued notifications when the
        # receiving page is destroyed; lambdas would outlive its Qt object.
        worker.daily_ready.connect(self.receive_daily)
        worker.month_ready.connect(self.receive_month)
        worker.failed.connect(self.receive_failure)
        worker.finished.connect(self.finished);worker.start()

    @pyqtSlot(object)
    def receive_daily(self,event):self.daily_received(*event)

    @pyqtSlot(object)
    def receive_month(self,event):self.month_received(*event)

    @pyqtSlot(object)
    def receive_failure(self,event):self.failed(*event)

    def daily_received(self,key,data):
        if key!=self._key or self._stopped:return
        sun,moon,info,phases=data
        self.update_moon(info)
        self.moon_times.setText('Kuun nousu '+event_label(moon.rises,'ei nousua tänä päivänä')+
            '\nKuun lasku '+event_label(moon.sets,'ei laskua tänä päivänä')+
            ('\nKuu on koko päivän horisontin yläpuolella.' if moon.state=='always_above' else
             '\nKuu on koko päivän horisontin alapuolella.' if moon.state=='always_below' else ''))
        state={'always_above':'Yötön yö','always_below':'Aurinko ei nouse tänä päivänä'}.get(sun.sun.state,'')
        self.sun_text.setText('Nousu '+event_label(sun.sun.rises,'—')+' · Lasku '+event_label(sun.sun.sets,'—')+
            '\nPäivän pituus '+duration_label(sun.sun.duration)+('\n'+state if state else ''))
        lines=[]
        for title,horizon in [('Siviilihämärä',sun.civil),('Merihämärä',sun.nautical),('Tähtitieteellinen hämärä',sun.astronomical)]:
            lines.append(title+': '+event_label(horizon.rises,'ei aamurajaa')+' – '+event_label(horizon.sets,'ei iltarajaa'))
        self.twilight.setText('\n'.join(lines))
        self.bar.data=sun;self.bar.update()
        self.phases.setText('SEURAAVAT KUUNVAIHEET\n'+' · '.join(
            f'{title} {(instant+timedelta(seconds=30)).astimezone(ZoneInfo(sun.zone)):%d.%m. %H:%M}' for instant,title in phases))

    def month_received(self,key,rows):
        if key!=self._key or self._stopped:return
        self.table.setRowCount(len(rows))
        for row,(day,sun,info) in enumerate(rows):
            values=[f'{day:%d.%m.}',event_label(sun.rises,'—'),event_label(sun.sets,'—'),duration_label(sun.duration),info.label]
            for col,text in enumerate(values):
                item=QTableWidgetItem(text);item.setToolTip(text)
                item.setData(Qt.ItemDataRole.UserRole,day);self.table.setItem(row,col,item)
            if day==as_date(self.date):self.table.selectRow(row)
        self.status.setText('Kuukauden valoajat · valitse päivä taulukosta. Ajat ovat paikan paikallisaikaa.')

    def failed(self,key,message):
        if key==self._key and not self._stopped:self.status.setText(message)

    def choose_row(self,row,_column):
        item=self.table.item(row,0)
        if item:
            day=item.data(Qt.ItemDataRole.UserRole);self.date.setDate(QDate(day.year,day.month,day.day))

    @pyqtSlot()
    def finished(self):
        if self._stopped:return
        worker=self.sender()
        if worker is None:return
        if worker in self._workers:self._workers.remove(worker)
        worker.deleteLater()

    def stop(self):
        if self._stopped:return
        self._stopped=True
        for worker in self._workers:worker.requestInterruption()
        for worker in self._workers:worker.wait()


class NamesPage(QWidget):
    def __init__(self,controller):
        super().__init__();self.controller=controller;self.folk_period=None
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(14)
        layout.addWidget(label('NIMIKALENTERIT','eyebrow'))
        self.heading=label('Mikä on nimesi ajanlaskuissa?','heading');layout.addWidget(self.heading)
        row=QHBoxLayout();row.addWidget(label('Syntymäpäivä tai muu päivä'))
        self.date=date_edit(controller.calendars.now().date());row.addWidget(self.date)
        row.addWidget(button('Tänään',self.today));row.addStretch(1);layout.addLayout(row)
        self.tabs=QTabWidget();layout.addWidget(self.tabs)
        names=QWidget();name_layout=QVBoxLayout(names);self.name_labels={};self.position_labels={}
        for key,title in [('shadow','Varjoaika'),('star','Tähtiaika'),('blood','Veri Aika'),('finnish','Suomalainen kuukalenteri')]:
            frame,content=card();content.addWidget(label(title.upper(),'eyebrow'))
            pair=label('','',True);pair.setStyleSheet('font-size:20px;');content.addWidget(pair)
            position=label('','muted',True);content.addWidget(position)
            self.name_labels[key]=pair;self.position_labels[key]=position;name_layout.addWidget(frame)
        name_layout.addWidget(label('Nimet on keksitty tätä sovellusta varten. Ne eivät ole virallisia tai historiallisia nimipäiviä. '
            'Varjoajan 390, Tähtiajan 510 ja Veri Ajan 777 päivän nimikierto jatkuu syntymäpäivähaussa myös taaksepäin ennen ajanlaskun alkua. '
            'Veri Ajan nimet saavat vaikutteita veren, elämänkierron ja biologian sanastosta. '
            'Sama nimipari palaa aina saman ajanlaskun vuoden päivän kohdalle.','muted',True))
        self.tabs.addTab(names,'Oma nimi')
        traditional=QWidget();content=QVBoxLayout(traditional)
        navigation=QHBoxLayout();navigation.addWidget(button('‹ Edellinen kuu',lambda:self.step(-1)))
        navigation.addStretch(1);navigation.addWidget(button('Seuraava kuu ›',lambda:self.step(1)));content.addLayout(navigation)
        content.addWidget(label('SOVELLUKSEN LASKENNALLINEN TULKINTA · HELSINGIN PÄIVÄMÄÄRÄT','eyebrow',True))
        self.folk_heading=label('','heading',True);content.addWidget(self.folk_heading)
        self.folk_info=label('','muted',True);content.addWidget(self.folk_info)
        self.folk_grid=QGridLayout();content.addLayout(self.folk_grid)
        self.folk_names=label('','',True);content.addWidget(self.folk_names)
        self.folk_note=label('','muted',True);content.addWidget(self.folk_note)
        content.addWidget(button('Muokkaa päivän merkintää',self.edit_note))
        self.folk_rules=label('Sovelluksen laskennallinen tulkinta: joulukuu sisältää talvipäivänseisauksen. '
            'Peräkkäisten joulukuiden väliin jää 12 tai 13 kuunkiertoa; 13 kuukauden vuodessa Vaahtokuu seuraa helmikuuta. '
            'Kuukausi alkaa tähtitieteellisen uudenkuun Helsingin päivämääränä, ja siinä on 29 tai 30 päivää. '
            'Katajalan sivu ei määritä tätä tarkkaa laskentasääntöä. Kyseessä ei ole varmaksi rekonstruoitu historiallinen ajanlasku.','muted',True)
        content.addWidget(self.folk_rules)
        content.addWidget(button('Lähde: Katajala · Suomalainen kalenteri ↗',lambda:QDesktopServices.openUrl(QUrl(folk.SOURCE))))
        self.tabs.addTab(traditional,'Suomalainen kuukalenteri')
        self.tabs.currentChanged.connect(self.sync_title)
        self.date.dateChanged.connect(self.render);controller.settings_changed.connect(self.render)
        controller.notes_changed.connect(self.render)
        self.render()

    def today(self):
        day=self.controller.calendars.now().date();self.date.setDate(QDate(day.year,day.month,day.day))

    def sync_title(self,index):
        self.heading.setText('Suomalainen kuukalenteri' if index==1 else 'Mikä on nimesi ajanlaskuissa?')

    def render(self,*_):
        day=as_date(self.date);epoch=date.fromisoformat(self.controller.options['star_epoch'])
        self.folk_note.setText(self.controller.state.note(day) or 'Ei merkintää tälle päivälle.')
        for system in ('shadow','star'):
            pair=names_for_day(system,day,epoch);month,number=cycle_position(system,day,epoch)
            title=(shadow.MONTH_NAMES if system=='shadow' else star.MONTHS)[month]
            self.name_labels[system].setText(f'Miehen nimi: {pair.male}\nNaisen nimi: {pair.female}')
            self.position_labels[system].setText(f'{number}. {title} · nimikierron kohta')
        blood = blood_time.from_date(day)
        pair = blood_names.names_for_day(day)
        self.name_labels['blood'].setText(f'Miehen nimi: {pair.male}\nNaisen nimi: {pair.female}')
        position = f'777 päivän nimikierto · kohta {blood.day_of_year}/777'
        self.position_labels['blood'].setText(position + (' · ennen ajanlaskun alkua' if blood.ordinal < 0 else
                                                       f' · vuosi {blood.year:04d}, viikko {blood.week_of_year}/111'))
        while self.folk_grid.count():
            item=self.folk_grid.takeAt(0)
            if item.widget():item.widget().hide();item.widget().deleteLater()
        try:
            item=folk.convert(day);self.folk_period=item.period
            self.name_labels['finnish'].setText(f'Miehen nimi: {item.names.male}\nNaisen nimi: {item.names.female}')
            self.position_labels['finnish'].setText(item.label+' · sovelluksen tulkinta')
            self.folk_heading.setText(item.label)
            self.folk_info.setText(folk.DESCRIPTIONS[item.period.month]+f'\n{item.period.start:%d.%m.%Y}–{item.period.end-timedelta(days=1):%d.%m.%Y} · '
                f'{item.period.length} päivää · '+('13 kuukauden vuosi: Vaahtokuu mukana' if item.period.intercalary_year else '12 kuukauden vuosi')+
                '\nKekri: sadonkorjuun päättymisen juhla, jonka ajankohta on perinteessä vaihdellut; ei kiinteää historiallista päivää.')
            self.folk_names.setText('VALITUN PÄIVÄN NIMIPARI\n'+item.names.label)
            for col,title in enumerate(('Ma','Ti','Ke','To','Pe','La','Su')):self.folk_grid.addWidget(label(title,'muted'),0,col)
            for offset in range(item.period.length):
                civil=item.period.start+timedelta(days=offset)
                action=button(f'{offset+1}\n{civil:%d.%m.}',lambda _,d=civil:self.set_day(d))
                action.setMinimumHeight(58);action.setCheckable(True);action.setChecked(civil==day)
                pair=names_at('finnish',item.period.month,offset);action.setToolTip(pair.label)
                action.setEnabled(1900<=civil.year<=2100)
                position=item.period.start.weekday()+offset
                self.folk_grid.addWidget(action,1+position//7,position%7)
        except ValueError as error:
            self.folk_period=None;self.name_labels['finnish'].setText(str(error));self.position_labels['finnish'].clear()
            self.folk_heading.setText('Päivä ei ole laskenta-alueella');self.folk_info.setText(str(error));self.folk_names.clear()

    def set_day(self,day):self.date.setDate(QDate(day.year,day.month,day.day))

    def step(self,direction):
        if self.folk_period:
            day=self.folk_period.start-timedelta(days=1) if direction<0 else self.folk_period.end
            if 1900<=day.year<=2100:self.set_day(day)

    def show_folk(self,day):
        self.set_day(day);self.tabs.setCurrentIndex(1)

    def edit_note(self):
        from .ui import NoteDialog
        dialog=NoteDialog(self.controller,as_date(self.date),self)
        dialog.exec()
