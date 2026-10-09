"""One launcher and one autostart entry for the unified application."""
from pathlib import Path
import os
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]

def launcher_root():
    """Managed releases keep autostart aimed at the stable current link."""
    base=ROOT.parent.parent
    current=base/'current'
    if (ROOT.parent.name=='releases' and (base/'installation.json').is_file()
        and current.is_symlink() and current.resolve().parent==ROOT.parent):
        return current
    return ROOT

def quote(value):return '"'+str(value).replace('\\','\\\\').replace('"','\\"').replace('%','%%').replace('$','\\$').replace('`','\\`')+'"'

def entry(widgets_only=False):
    root=launcher_root()
    return ('[Desktop Entry]\nType=Application\nName=Ajanlaskut ja Sää\n'
        'Comment=Kalenterit, ajanlaskut ja sää samassa sovelluksessa\n'
        f'Exec={quote(sys.executable)} {quote(root/"main.py")}'+(' --widgets-only' if widgets_only else '')+'\n'
        f'Icon={root/"assets/icon.svg"}\nTerminal=false\nCategories=Office;Calendar;\n'
        'StartupNotify=true\nX-GNOME-Autostart-enabled=true\n')

def write_atomic(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    descriptor,name=tempfile.mkstemp(prefix='.launcher-',dir=path.parent)
    try:
        with os.fdopen(descriptor,'w',encoding='utf-8') as stream:stream.write(text)
        os.replace(name,path)
    finally:Path(name).unlink(missing_ok=True)

def set_autostart(enabled):
    config=Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))
    path=config/'autostart/ajanlaskut-ja-saa.desktop'
    text=entry(True)
    if not enabled:text=text.replace('X-GNOME-Autostart-enabled=true','X-GNOME-Autostart-enabled=false')
    write_atomic(path,text)

def install_launcher():
    data=Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))
    path=data/'applications/ajanlaskut-ja-saa.desktop'
    write_atomic(path,entry());return path
