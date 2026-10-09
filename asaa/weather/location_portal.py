"""One-shot location, invoked only after the widget's explicit consent dialog."""
import uuid
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot, QMetaType
from PyQt6.QtDBus import (QDBusConnection, QDBusMessage, QDBusObjectPath,
    QDBusPendingCallWatcher, QDBusPendingReply, QDBusVariant, QDBusArgument)

SERVICE = 'org.freedesktop.portal.Desktop'
PATH = '/org/freedesktop/portal/desktop'
INTERFACE = 'org.freedesktop.portal.Location'


class LocationPortal(QObject):
    located = pyqtSignal(float, float)
    failed = pyqtSignal(str)

    def __init__(self, parent=None, bus=None):
        super().__init__(parent)
        self.bus = bus or QDBusConnection.sessionBus()
        self.session = ''
        self.request = ''
        self.active = False
        self.watchers = []
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(lambda: self.fail('Sijaintia ei saatu. Tarkista Ubuntun sijaintiasetus tai hae paikka nimellä.'))

    def call(self, path, interface, method, args, callback):
        message = QDBusMessage.createMethodCall(SERVICE,path,interface,method)
        message.setArguments(args)
        watcher = QDBusPendingCallWatcher(self.bus.asyncCall(message,5000),self)
        self.watchers.append(watcher)
        def finished(w):
            reply = QDBusPendingReply(w)
            self.watchers.remove(w)
            w.deleteLater()
            if not self.active:
                # Closing before CreateSession returns must still release its session.
                if method == 'CreateSession' and not reply.isError():
                    handle = reply.value()
                    self.close_path(handle.path() if hasattr(handle,'path') else str(handle))
                return
            if reply.isError():
                self.fail('Ubuntu ei antanut sijaintia. Voit hakea paikan nimellä.')
            else:
                callback(reply.value())
        watcher.finished.connect(finished)

    def start(self, parent_window=''):
        if self.active:
            return
        self.active = True
        self.timer.start(60_000)
        self.bus.connect(SERVICE,PATH,INTERFACE,'LocationUpdated',self.updated)
        token = 'weather_' + uuid.uuid4().hex
        accuracy = QDBusVariant(QDBusArgument(3,QMetaType.Type.UInt.value))
        self.call(PATH,INTERFACE,'CreateSession', [{'session_handle_token':token,'accuracy':accuracy}],
                  lambda handle: self.created(handle,parent_window))

    def created(self, handle, parent_window):
        self.session = handle.path() if hasattr(handle,'path') else str(handle)
        token = 'weather_' + uuid.uuid4().hex
        sender = self.bus.baseService().lstrip(':').replace('.','_')
        self.request = f'/org/freedesktop/portal/desktop/request/{sender}/{token}'
        self.bus.connect(SERVICE,self.request,'org.freedesktop.portal.Request','Response',self.response)
        self.bus.connect(SERVICE,self.session,'org.freedesktop.portal.Session','Closed',self.closed)
        self.call(PATH,INTERFACE,'Start',[QDBusObjectPath(self.session),parent_window,{'handle_token':token}],lambda result: None)

    @pyqtSlot('uint','QVariantMap')
    def response(self, code, results):
        if self.active and code:
            self.fail('Sijainnin käyttöä ei sallittu. Voit hakea paikan nimellä.')

    @pyqtSlot(QDBusObjectPath,'QVariantMap')
    def updated(self, session, location):
        if not self.active or session.path() != self.session:
            return
        try:
            lat, lon = float(location['Latitude']),float(location['Longitude'])
            if not -90 <= lat <= 90 or not -180 <= lon <= 180:
                raise ValueError()
        except (KeyError,TypeError,ValueError):
            return
        self.stop()
        self.located.emit(lat,lon)

    @pyqtSlot('QVariantMap')
    def closed(self, details):
        if self.active:
            self.fail('Ubuntu sulki sijaintihaun. Voit hakea paikan nimellä.')

    def close_path(self, path):
        if path:
            message = QDBusMessage.createMethodCall(SERVICE,path,'org.freedesktop.portal.Session','Close')
            self.bus.asyncCall(message)

    def stop(self):
        self.active = False
        self.timer.stop()
        self.close_path(self.session)
        if self.request:
            message = QDBusMessage.createMethodCall(SERVICE,self.request,'org.freedesktop.portal.Request','Close')
            self.bus.asyncCall(message)
            self.bus.disconnect(SERVICE,self.request,'org.freedesktop.portal.Request','Response',self.response)
        if self.session:
            self.bus.disconnect(SERVICE,self.session,'org.freedesktop.portal.Session','Closed',self.closed)
        self.bus.disconnect(SERVICE,PATH,INTERFACE,'LocationUpdated',self.updated)
        self.session = self.request = ''

    def fail(self, message):
        self.stop()
        self.failed.emit(message)
