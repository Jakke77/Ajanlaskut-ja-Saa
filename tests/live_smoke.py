"""Run this application's own X11 window with real weather in temporary state."""
import argparse
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM','xcb')
from PyQt6.QtCore import QCoreApplication, Qt, QTimer
QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
from PyQt6.QtWidgets import QApplication
from asaa.app import Controller
from asaa.state import State

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--preview',type=Path,required=True)
    args=parser.parse_args();args.preview.parent.mkdir(parents=True,exist_ok=True)
    app=QApplication([]);app.setStyle('Fusion');app.setQuitOnLastWindowClosed(False)
    with TemporaryDirectory(prefix='ajanlaskut-live-') as directory:
        controller=Controller(app,State(Path(directory)/'state.json'),network=True)
        controller.open_page('overview')
        complete=False
        def finish():
            nonlocal complete
            if complete:return
            complete=True
            controller.tick_timer.stop()
            report={'platform':app.platformName(), 'window_visible':controller.window.isVisible(),
                'providers':{key:len(f.hours) if f else 0 for key,f in controller.weather.forecasts.items()},
                'weather_errors':controller.weather.errors, 'daily_lines':len(controller.daily.lines()),
                'daily_error':controller.daily.error, 'default_refresh_minutes':controller.options['refresh_minutes']}
            print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
            controller.window.grab().save(str(args.preview))
            controller.shutdown();app.quit()
        def check():
            if all(controller.weather.forecasts.values()) and controller.daily.lines():finish()
        poll=QTimer();poll.timeout.connect(check);poll.start(1000)
        QTimer.singleShot(45_000,finish)
        code=app.exec()
        controller.shutdown();controller.window.hide()
        return code

if __name__=='__main__':raise SystemExit(main())
