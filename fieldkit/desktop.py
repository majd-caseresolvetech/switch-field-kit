"""Desktop shortcuts and login startup, without changing the display manager."""
import os
from pathlib import Path
import shlex
import shutil
import subprocess

from .common import atomic, config, config_path, write_json


def config_home():
    return Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config')))


def data_home():
    return Path(os.environ.get('XDG_DATA_HOME', str(Path.home()/'.local/share')))


def desktop_dir():
    """Respect a translated/relocated Desktop, including a disabled one."""
    path = Path.home()/'Desktop'
    dirs = config_home()/'user-dirs.dirs'
    if dirs.is_file():
        for line in dirs.read_text().splitlines():
            if line.startswith('XDG_DESKTOP_DIR='):
                values = shlex.split(line.split('=', 1)[1], comments=True)
                if len(values) == 1:
                    path = Path(values[0].replace('${HOME}', str(Path.home())).replace('$HOME', str(Path.home())))
    if not path.is_absolute() or path == Path.home():
        return None
    return path


def desktop_quote(value):
    # Desktop strings are unescaped once before Exec arguments are parsed.
    value = str(value)
    if any(c in value for c in ('\n', '\r', '\x00')):
        raise ValueError('A desktop path cannot contain a line break or NUL.')
    return '"'+value.replace('\\', '\\\\\\\\').replace('"', '\\\\"').replace('$', '\\\\$').replace('`', '\\\\`').replace('%', '%%')+'"'


def desktop_text(launcher, icon, name='Switch Field Kit', wm_class='SwitchFieldKit', command='open'):
    # GLib 2.56 checks the executable before expanding %% in Exec. Keep its
    # executable path fixed and pass the user path as an argument to env.
    return ('[Desktop Entry]\nType=Application\nName='+name+
            '\nComment=Original guides, Wikipedia and maps without internet\nExec=/usr/bin/env '+desktop_quote(launcher)+
            (' '+command if command else '')+'\nIcon='+str(icon)+'\nTerminal=false\nCategories=Education;Utility;\nStartupWMClass='+wm_class+'\n')


def write_shortcut(path, text, trusted=False):
    atomic(path, text.encode('utf-8'))
    if trusted:
        path.chmod(0o755)
        if shutil.which('gio'):
            try:
                subprocess.run(['gio', 'set', str(path), 'metadata::trusted', 'true'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except OSError:
                pass  # Desktop trust metadata is optional on some environments.


def install_shortcuts(app, autostart):
    text = desktop_text(Path.home()/'.local/bin/fieldkit', app/'web/fieldkit-icon.svg')
    write_shortcut(data_home()/'applications/switch-field-kit.desktop', text)
    directory = desktop_dir()
    if directory is not None:
        write_shortcut(directory/'Switch Field Kit.desktop', text, trusted=True)
    startup = config_home()/'autostart/switch-field-kit.desktop'
    write_shortcut(startup, text+'X-GNOME-Autostart-enabled='+str(autostart).lower()+'\nHidden='+str(not autostart).lower()+'\n')


def set_autostart(enabled):
    app = data_home()/'switch-field-kit/app'
    if not (app/'fieldkit').is_dir():
        raise RuntimeError('Install Field Kit first with bash setup.sh.')
    install_shortcuts(app, enabled)
    settings = config()
    settings['autostart'] = enabled
    write_json(config_path(), settings)
    print('Field Kit will '+('open automatically after Ubuntu sign-in.' if enabled else 'open only when you choose its launcher.'))


def remove_shortcuts():
    paths = [data_home()/'applications/switch-field-kit.desktop', config_home()/'autostart/switch-field-kit.desktop']
    directory = desktop_dir()
    if directory is not None:
        paths.append(directory/'Switch Field Kit.desktop')
    for path in paths:
        if path.exists():
            path.unlink()
