"""Clock, daily weather and interactive month widgets share one glass surface."""
from datetime import date, datetime
from PyQt6.QtCore import Qt, QRectF, QPointF, QSize
from PyQt6.QtGui import QPainter, QFont, QFontMetricsF, QColor, QPen
from PyQt6.QtWidgets import QWidget, QToolButton, QMenu, QApplication
from .calendar import NAMES, MONTHS
from .theme import paint_panel
from .widget_themes import widget_theme
from .clock_display import clock_mode as resolved_clock_mode, clock_digit_scale, clock_digit_color
from .clock_config import SYSTEMS, PROFILE_KEYS, CLOCK_TITLES, clock_layout
from .windowing import DESKTOP_FLAGS, WidgetFrame, apply_layer

WIDGET_LABELS = {
    'combined': 'Ajanlaskut · vaihtuva kello',
    'shadow': 'Varjoaika · kello', 'star': 'Tähtiaika · kello', 'weather': 'Sää · tuntigraafi',
    'daily': 'Varjosää · kolme päivää', 'civil': 'Gregoriaaninen · kello',
    'blood': 'Veri Aika · Otava ja kello',
    'shadow_calendar': 'Varjoaika · kuukausiwidget', 'star_calendar': 'Tähtiaika · kuukausiwidget',
}

class DesktopSurface(QWidget):
    def __init__(self, controller, key, *, preview=False, parent=None):
        super().__init__(parent, Qt.WindowType.Widget if preview else DESKTOP_FLAGS)
        self.controller, self.key = controller, key
        self.preview = preview
        self.profile_override = self.system_override = self.theme_override = None
        self.appearance_key_override = None
        self.clock_display_override = None
        self.button_theme = None
        self.month = None
        self.browsing = False
        self.offset = None
        self.cells = []
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle('Ajanlaskut ja Sää · ' + WIDGET_LABELS[key])
        self.buttons = []
        if key.endswith('_calendar'):
            self.button('‹', 'Edellinen kuukausi', lambda: self.step(-1))
            self.button('◎', 'Tämä kuukausi', self.today)
            self.button('›', 'Seuraava kuukausi', lambda: self.step(1))
        else:
            if key == 'combined':
                self.button('‹', 'Edellinen ajanlasku', lambda: controller.step_time(-1))
                self.button('›', 'Seuraava ajanlasku', lambda: controller.step_time(1))
            self.button('▦', 'Avaa kalenteri', self.open_calendar)
        self.button('▧', 'Taustakuvat · työpöytä ja lukitusnäyttö', lambda: controller.open_page('wallpapers'))
        self.button('⚙', 'Ajanlaskut ja kellon sisältö' if key in PROFILE_KEYS else 'Yhteiset asetukset',
                    lambda: controller.open_clock(key) if key in PROFILE_KEYS else controller.open_page('settings'))
        self.button('×', 'Piilota widget', lambda: controller.set_widget(key, False))
        self.frame=None if preview else WidgetFrame(self,controller,key)
        self.apply_options()
        controller.clock_changed.connect(self.clock_tick)
        controller.settings_changed.connect(self.apply_options)
        controller.notes_changed.connect(self.update)
        controller.daily.changed.connect(self.update)
        if not preview: self.restore_position()

    def button(self, text, name, action):
        button = QToolButton(self)
        button.setText(text); button.setToolTip(name); button.setAccessibleName(name)
        button.clicked.connect(action)
        self.buttons.append(button)

    @property
    def options(self): return self.controller.state.settings

    @property
    def system(self):
        return self.system_override or (self.controller.time_rotation.current if self.key == 'combined' else self.key.split('_')[0])

    @property
    def profile(self):
        return self.profile_override if self.profile_override is not None else self.options['clock_profiles'][self.key]

    @property
    def theme(self):
        return widget_theme(self.options, self.appearance_key_override or self.key,
                            self.system, selection=self.theme_override)

    @property
    def analog_clock(self):
        return self.clock_mode in ('analog', 'both', 'otava', 'otava_both')

    @property
    def digital_clock(self):
        return self.clock_mode in ('digital', 'both', 'otava_both')

    @property
    def clock_mode(self):
        if self.key not in PROFILE_KEYS:return None
        return resolved_clock_mode(self.options,self.key,self.theme,selection=self.clock_display_override)

    def clock_tick(self):
        self.style_buttons()
        self.update()

    def style_buttons(self):
        theme = self.theme
        signature = (theme, self.options['font'])
        if signature == self.button_theme: return
        self.button_theme = signature
        for button in self.buttons:
            button.setStyleSheet(f'QToolButton {{color:{theme.accent}; background:transparent; border:0; padding:0; font:16px "{self.options["font"]}";}} QToolButton:hover {{background:{theme.border};border-radius:5px;}} QToolButton:focus {{border:1px solid {theme.accent};}}')

    def apply_options(self):
        options = self.options
        self.base_height = 414 if self.key.endswith('_calendar') else 330
        if self.key in PROFILE_KEYS: _, self.base_height = clock_layout(self.profile, analog=self.analog_clock)
        visible, position = self.isVisible(), self.pos()
        if not self.preview:
            apply_layer(self,self.controller.layers.on_top())
        scale = options['scale'] / 100
        default=QSize(round(430*scale),round(self.base_height*scale))
        if self.preview:self.setFixedSize(default)
        else:
            self.setMinimumSize(258,round(self.base_height*.6));self.resize(self.frame.size(default))
        self.layout_controls()
        self.style_buttons()
        if visible and not self.preview: self.show(); self.move(position); self.clamp()
        self.update()

    def layout_controls(self):
        if not hasattr(self,'base_height'):return
        scale=min(self.width()/430,self.height()/self.base_height)
        self.draw_scale=scale;self.logical_width=self.width()/scale;self.logical_height=self.height()/scale
        for i, button in enumerate(self.buttons):
            pitch = 32 if self.key == 'combined' else 40
            button.setGeometry(round((self.logical_width - pitch*len(self.buttons) - 8+i*pitch)*scale), round(10*scale), round((pitch-6)*scale), round(30*scale))
            button.setEnabled(not self.preview)
    def resizeEvent(self,event):
        self.layout_controls();super().resizeEvent(event)

    def restore_position(self):
        screen = QApplication.primaryScreen()
        if not screen: return
        area = screen.availableGeometry()
        preset = {
            'combined': (area.right()-self.width()-18, area.top()+30),
            'star': (area.left()+55, area.bottom()-self.height()-24),
            'shadow': (area.right()-self.width()-round(720*self.options['scale']/100)-38, area.bottom()-self.height()-24),
            'civil': (area.left()+55, area.top()+65),
            'daily': (area.right()-self.width()-28, area.top()+60),
        }
        position = self.controller.state.geometry(self.key) or preset.get(self.key, (area.left()+130, area.top()+110))
        self.move(*position[:2]); self.clamp()
        self.frame.remember_position()

    def clamp(self):
        if self.preview: return
        if not QApplication.screens(): return
        if any(s.availableGeometry().contains(self.geometry()) for s in QApplication.screens()): return
        area = (QApplication.screenAt(self.geometry().center()) or QApplication.primaryScreen()).availableGeometry()
        self.move(max(area.left(), min(self.x(), area.right()-self.width()+1)), max(area.top(), min(self.y(), area.bottom()-self.height()+1)))

    def showEvent(self, event): self.clamp(); super().showEvent(event)

    def open_calendar(self):
        self.controller.open_calendar(self.system if self.system != 'daily' else 'civil')

    def text(self, painter, value, y, size, color=None, bold=False, x=22, width=None, center=False, height=None, clock=False, fit=False):
        factor=(clock_digit_scale(self.options,self.key,selection=self.clock_display_override)
                if clock else self.options['widget_text_scale'])/100
        pixels=round(size*factor)
        width=self.logical_width-x*2 if width is None else width
        height=height or max(20,pixels*1.65)
        font = QFont(self.options['font']);font.setBold(bold);font.setPixelSize(pixels)
        metrics=QFontMetricsF(font)
        while pixels>6 and (metrics.height()>height or ((clock or fit) and metrics.horizontalAdvance(value)>width)):
            pixels-=1;font.setPixelSize(pixels);metrics=QFontMetricsF(font)
        default_color = (clock_digit_color(self.options, self.key, self.theme,
                         selection=self.clock_display_override) if clock else self.theme.text)
        painter.setFont(font); painter.setPen(QColor(color or default_color))
        rect = QRectF(x, y, width, height)
        shown=metrics.elidedText(value,Qt.TextElideMode.ElideRight,width)
        # Explicit single-line bounds prevent the next field from being covered.
        flags=(Qt.AlignmentFlag.AlignHCenter if center else Qt.AlignmentFlag.AlignLeft)|Qt.AlignmentFlag.AlignTop|Qt.TextFlag.TextSingleLine
        painter.drawText(rect,flags,shown)
        self.text_layout.append((value,rect,font.pixelSize(),metrics.height(),metrics.horizontalAdvance(shown)))

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.scale(self.draw_scale,self.draw_scale)
        theme = self.theme
        self.text_layout=[]
        paint_panel(p, QRectF(0,0,self.logical_width,self.logical_height), theme, self.options['opacity']/100)
        title = CLOCK_TITLES[self.system] if self.key in PROFILE_KEYS else NAMES.get(self.system, '')
        pitch = 32 if self.key == 'combined' else 40
        self.text(p, 'VARJOSÄÄ' if self.key == 'daily' else title.upper(), 14, 12, theme.accent, True, width=self.logical_width-pitch*len(self.buttons)-42, height=25)
        now = self.controller.calendars.now()
        if self.key.endswith('_calendar'):
            self.paint_calendar(p, now.date(), theme)
        elif self.key == 'daily':
            self.text(p, 'Seuraavat kolme päivää', 65, 22, theme.accent, True,height=42)
            self.paint_daily(p, 141, theme)
        else: self.paint_clock(p, now, theme)
        footer = 'AJANLASKUT JA SÄÄ'
        if self.key == 'combined' and not self.preview and self.controller.time_rotation.mode != 'fixed':
            footer = ('SATUNNAINEN' if self.controller.time_rotation.mode == 'random' else 'VAIHTUVA') + f' · {self.controller.time_rotation.remaining()} s'
        self.text(p, footer, self.logical_height-24, 9, theme.muted, center=True,height=20)
        p.end()

    def paint_clock(self, p, now, theme):
        item = None
        try:
            item = self.controller.calendars.at(self.system, now)
            date_label = item.label
            weekday = self.controller.calendars.day_words(item, self.options['star_side'])
            from .astronomy import moon_at
            try: phase = moon_at(now).label
            except ValueError: phase = item.phase
        except ValueError:
            date_label, weekday, phase = 'Ajanlasku ei ole vielä alkanut', '', ''
        tip = []
        for field, y, height in clock_layout(self.profile, analog=self.analog_clock)[0]:
            if field == 'clock':
                value = now.strftime('%H:%M:%S' if self.options['seconds'] else '%H:%M')
                if self.analog_clock:
                    from .ubuntu_clock import paint_clock
                    rect = paint_clock(p, QRectF(22, y+8, self.logical_width-44, height-16), now,
                                       theme, self.options['font'], self.options['opacity']/100,
                                       self.options['seconds'], self.options['widget_clock_scale']/100,
                                       style='otava' if self.clock_mode in ('otava','otava_both') else 'standard')
                    if self.digital_clock:
                        self.text(p, value, rect.y(), 24, bold=True, x=rect.x(), width=rect.width(),
                                  center=True, height=rect.height(), clock=True)
                elif self.digital_clock:
                    self.text(p, value, y+5, 53, bold=True, center=True, height=85, clock=True)
            elif field in ('date', 'weekday', 'phase'):
                value = {'date':date_label, 'weekday':weekday, 'phase':phase}[field]
                self.text(p, value, y+3, 19 if field=='date' else 14, theme.accent if field=='date' else theme.muted, center=True, height=height-8, fit=field=='date')
            elif field == 'nameday':
                pair = item.names if item is not None else None
                if pair:
                    self.text(p,'Mies: '+pair.male,y+3,14,theme.text,center=True,height=26,fit=True)
                    self.text(p,'Nainen: '+pair.female,y+33,14,theme.text,center=True,height=26,fit=True)
                    value = 'Nimipari · '+pair.label
                else:
                    value = 'Ei nimiparia tässä ajanlaskussa.'
                    self.text(p,value,y+3,12,theme.muted,center=True,height=26,fit=True)
            elif field == 'reference':
                value = ' · '.join(([f'{now:%d.%m.%Y}'] if self.profile['civil_date'] else []) + ([self.options['zone']] if self.profile['zone'] else []))
                self.text(p, value, y+2, 12, theme.muted, center=True, height=28)
            elif field == 'otava':
                from .otava_ui import paint_otava
                from .otava import sampled_sky, tail_description
                from .blood_time import ZONE
                try:
                    snapshot = sampled_sky(self.controller, now)
                    paint_otava(p,QRectF(self.logical_width/2-60,y,120,108),snapshot.moment,theme,stars=snapshot.stars)
                    value=f'Otava · Oulu · ○ {tail_description(snapshot.stars)} · {snapshot.moment.astimezone(ZONE):%H:%M %Z}'
                    tip.append(f'Tarkistettu {snapshot.moment.astimezone(ZONE):%d.%m.%Y %H:%M:%S %Z}')
                    tip.append(tail_description(snapshot.stars))
                    tip.append(f'Seuraava tarkistus {snapshot.next_update.astimezone(ZONE):%H:%M %Z} · 26 min välein')
                except (ValueError,OverflowError):
                    value='Otavan laskenta: vuodet 1900–2100'
                self.text(p,value,y+111,11,theme.muted,center=True,height=23,fit=True)
            elif field == 'weather':
                lines = self.controller.daily.lines()
                self.text(p, self.controller.weather.place.name, y, 12, theme.accent, height=25)
                for i, line in enumerate(lines[:3] or [self.controller.daily.error or 'Haetaan ennustetta…']):
                    parts = line.split(' · ')
                    if len(parts) >= 3:
                        self.text(p, parts[0]+' · sade '+parts[-1], y+29+i*48, 12, height=23)
                        self.text(p, ' · '.join(parts[1:-1]), y+53+i*48, 12, theme.muted, height=23)
                    else: self.text(p, line, y+29+i*48, 12, height=23)
                stamp = self.controller.daily.saved
                value = 'wttr.in · '+(f'haettu {stamp.astimezone(self.controller.calendars.zone):%H:%M}' if stamp else 'ennuste puuttuu') + (' · välimuisti' if self.controller.daily.error else '')
                self.text(p, value, y+178, 10, theme.muted, height=23)
                tip.extend(lines)
            elif field == 'note':
                self.text(p, 'PÄIVÄN MERKINTÄ', y, 11, theme.accent, height=23)
                value = self.controller.state.note(item.civil if self.system=='blood' and item is not None else now.date()) or 'Ei merkintää tälle päivälle.'
                self.text(p, value.splitlines()[0], y+27, 14, height=31)
            elif field == 'reminder':
                self.text(p, 'SEURAAVA MUISTUTUS', y, 11, theme.accent, height=23)
                upcoming = sorted((r for r in self.controller.state.data['reminders'] if not r['delivered'] and datetime.fromisoformat(r['due'])>=now), key=lambda r:datetime.fromisoformat(r['due']))
                value = (f'{datetime.fromisoformat(upcoming[0]["due"]).astimezone(self.controller.calendars.zone):%d.%m. %H:%M} · '+upcoming[0]['title']) if upcoming else 'Ei odottavia muistutuksia.'
                self.text(p, value.splitlines()[0], y+27, 14, height=31)
            tip.append(value)
        if item is not None and item.names and not self.profile['nameday']:
            tip.append('Nimipari · '+item.names.label)
        if self.clock_mode in ('otava','otava_both'):
            tip.append('Otavakello: tähtikuvio on symbolinen sekuntiviisari, yksi kierros minuutissa.')
        if self.profile['otava']:
            tip.append('Otavan erillinen taivaskuva tarkistetaan 26 minuutin välein Ouluun: zeniitti ylös, itä oikealle, länsi vasemmalle. Ympyröity tähti on Alkaid.')
        self.setToolTip('\n'.join(tip))
        self.setAccessibleName(CLOCK_TITLES[self.system]+'\n'+'\n'.join(tip))

    def paint_daily(self, p, start, theme):
        lines = self.controller.daily.lines()
        self.text(p, self.controller.weather.place.name, start-24, 12, theme.accent,height=23)
        for i, value in enumerate(lines or [self.controller.daily.error or 'Haetaan kolmen päivän ennustetta…']):
            parts=value.split(' · ')
            if len(parts)>=3:
                self.text(p,parts[0]+' · sade '+parts[-1],start+i*40,12,height=19)
                self.text(p,' · '.join(parts[1:-1]),start+i*40+19,12,theme.muted,height=19)
            else:self.text(p,value,start+i*40,12,height=19)
        stamp = self.controller.daily.saved
        self.text(p, 'wttr.in · ' + (f'haettu {stamp.astimezone(self.controller.calendars.zone):%H:%M}' if stamp else 'ennuste puuttuu') + (' · välimuisti' if self.controller.daily.error else ''), self.logical_height-46, 10, theme.muted,height=18)

    def paint_calendar(self, p, today, theme):
        if self.month is None or not self.browsing:
            item = self.controller.calendars.convert(self.system, max(today, self.controller.calendars.civil_date(self.system,1,0,0)))
            self.month = (item.year, item.month)
        days = self.controller.calendars.month_days(self.system, *self.month)
        self.text(p, f'{days[0].month_name} · {days[0].year:04d}', 64, 23, theme.accent, True, center=True,height=38)
        self.cells = []
        rows=(len(days)+5)//6
        pitch_x=65+(self.logical_width-430)/6
        pitch_y=52+(self.logical_height-self.base_height)/rows
        for i, day in enumerate(days):
            rect = QRectF(22+(i%6)*pitch_x,111+(i//6)*pitch_y,pitch_x-7,pitch_y-8)
            fill = QColor(theme.accent if day.civil == today else theme.surface)
            fill.setAlphaF(.8)
            p.setPen(QPen(QColor(theme.border),1)); p.setBrush(fill); p.drawRoundedRect(rect,8,8)
            self.text(p,str(day.day),rect.center().y()-14,16,theme.background if day.civil==today else theme.text,x=rect.x(),width=rect.width(),center=True,height=28)
            if self.controller.state.note(day.civil):
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(theme.accent)); p.drawEllipse(QPointF(rect.right()-7, rect.top()+7), 2,2)
            self.cells.append((rect, day))

    def step(self, delta):
        if self.month:
            self.month = self.controller.calendars.step_month(self.system, *self.month, delta)
            self.browsing = True
        self.update()

    def today(self):
        self.browsing=False;self.month=None;self.update()

    def mousePressEvent(self, event):
        if self.preview: return
        if event.button() == Qt.MouseButton.LeftButton:
            point = event.position() * (self.logical_width/self.width())
            for rect, day in self.cells:
                if rect.contains(point): self.controller.open_calendar(self.system, day.civil); return
            if not self.options['locked']: self.offset = event.globalPosition().toPoint()-self.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint()-self.offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.offset is not None:
            self.offset = None; self.clamp()
            saved=self.controller.state.geometry(self.key)
            try:self.controller.state.geometry(self.key, [self.x(),self.y()]+(saved[2:] if saved else []))
            except OSError as error:self.controller.storage_error(error)
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event): self.open_calendar()

    def contextMenuEvent(self, event):
        if self.preview: return
        menu = QMenu(self)
        if self.key == 'combined':
            for system in SYSTEMS:
                action = menu.addAction(CLOCK_TITLES[system], lambda checked=False,s=system:self.controller.select_time(s))
                action.setCheckable(True);action.setChecked(system==self.system)
            menu.addAction('Seuraava ajanlasku', self.controller.step_time)
            menu.addAction('Pidä tämä ajanlasku', lambda:self.controller.select_time(self.system))
            menu.addSeparator()
        menu.addAction('Avaa sovellus', lambda: self.controller.open_page('overview'))
        menu.addAction('Avaa kalenteri', self.open_calendar)
        if self.system in ('shadow', 'star'):
            menu.addAction('Näytä kuukausi työpöydällä', lambda: self.controller.set_widget(self.system+'_calendar', True))
        menu.addAction('Yhteiset asetukset', lambda: self.controller.open_page('settings'))
        menu.addAction('Widgetin teema…', lambda: self.controller.open_page('widgets'))
        if self.key in PROFILE_KEYS: menu.addAction('Ajanlaskut ja kellon sisältö', lambda:self.controller.open_clock(self.key))
        menu.addAction('Taustakuvat · työpöytä ja lukitusnäyttö', lambda: self.controller.open_page('wallpapers'))
        menu.addAction('Piilota widget', lambda: self.controller.set_widget(self.key, False))
        menu.addAction('Palauta tämän widgetin oletuskoko',self.frame.reset)
        menu.exec(event.globalPos())

    def closeEvent(self, event):
        if self.preview: event.accept();return
        if self.controller.stopping:event.accept();return
        self.controller.set_widget(self.key, False)
        event.ignore()
