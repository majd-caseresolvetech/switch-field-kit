"""Keep an already installed prototype library. Does not download that prototype."""
import argparse
import ast
from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from fieldkit.common import atomic
from fieldkit.desktop import config_home, data_home, desktop_dir, desktop_text, write_shortcut
from fieldkit.install import unit_quote


def keep_original(shared_books=False):
    home = Path.home()
    launcher = home/'.local/bin/offline-library'
    if not launcher.is_file():
        raise RuntimeError('No original Offline Library is installed. New users should skip this step. It does not download an older app.')
    if not (home/'.local/bin/fieldkit').is_file():
        raise RuntimeError('Install Field Kit with bash setup.sh first.')
    code = launcher.read_text()
    known = ["subprocess.Popen(['chromium-browser',", 'switch-offline-browser',
             'switch-offline-library.service', '--app=http://127.0.0.1:8080/']
    if not all(part in code for part in known):
        raise RuntimeError('The existing launcher differs from the supported prototype. It was left unchanged. Keep using its current shortcut.')
    unit = config_home()/'systemd/user/switch-offline-library.service'
    if shared_books and not unit.is_file():
        raise RuntimeError('The original library user service is missing. Shared-book startup was not configured.')
    if '--class=OriginalOfflineLibrary' not in code:
        code = code.replace("subprocess.Popen(['chromium-browser',", "subprocess.Popen(['chromium-browser','--class=OriginalOfflineLibrary',", 1)
    compile(code, str(launcher), 'exec')
    applications = data_home()/'applications'
    original_desktop = applications/'offline-library.desktop'
    startup = config_home()/'autostart/offline-library.desktop'
    icon = data_home()/'icons/original-offline-library.svg'
    dependency = config_home()/'systemd/user/switch-field-kit.service.d/original-library.conf'
    desktop = desktop_dir()
    targets = [launcher, original_desktop, startup, icon]
    if desktop is not None:
        targets.append(desktop/'Offline Library.desktop')
    if shared_books:
        targets.append(dependency)
    backup = data_home()/'switch-field-kit/original-backups'/datetime.utcnow().strftime('%Y%m%dT%H%M%S%fZ')
    backup.mkdir(parents=True)
    # Store the path mapping privately on the device, never in a release.
    manifest = []
    for number, path in enumerate(targets):
        if path.exists():
            saved = backup/(str(number)+'-'+path.name)
            shutil.copy2(str(path), str(saved))
            manifest.append(str(path)+'\t'+saved.name)
    (backup/'restore-paths.txt').write_text('\n'.join(manifest)+'\n')
    atomic(launcher, code.encode('utf-8'))
    launcher.chmod(0o755)
    atomic(icon, (ROOT/'web/original-library-icon.svg').read_bytes())
    text = desktop_text(launcher, icon, name='Offline Library (original fallback)',
                        wm_class='OriginalOfflineLibrary', command='')
    write_shortcut(original_desktop, text)
    if desktop is not None:
        write_shortcut(desktop/'Offline Library.desktop', text, trusted=True)
    # Only the old browser window is disabled. Its server/mount service is kept.
    write_shortcut(startup, text+'Hidden=true\nX-GNOME-Autostart-enabled=false\n')
    if shared_books:
        atomic(dependency, ('[Unit]\nRequires=switch-offline-library.service\nAfter=switch-offline-library.service\n\n[Service]\nExecStartPre='+unit_quote(home/'.local/bin/fieldkit')+' wait-books\n').encode())
        subprocess.check_call(['systemctl', '--user', 'daemon-reload'])
        subprocess.check_call(['systemctl', '--user', 'restart', 'switch-field-kit.service'])
    if shutil.which('gsettings'):
        result = subprocess.run(['gsettings', 'get', 'com.canonical.Unity.Launcher', 'favorites'],
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True)
        if result.returncode == 0:
            try:
                favorites = ast.literal_eval(result.stdout)
                if not isinstance(favorites, list) or not all(isinstance(x, str) for x in favorites):
                    raise ValueError('Not a launcher list')
                (backup/'unity-favorites.txt').write_text(result.stdout)
                first = ['application://switch-field-kit.desktop', 'application://offline-library.desktop']
                subprocess.run(['gsettings', 'set', 'com.canonical.Unity.Launcher', 'favorites', repr(first+[x for x in favorites if x not in first])],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except (ValueError, SyntaxError):
                pass
    print('Original library kept. Look for the green OLD icon or Offline Library on the desktop.')
    print('Its content and server services are unchanged. Its browser will no longer open at sign-in.')
    print('Close any already open original-library window, then reopen its shortcut to use the separate icon.')
    print('Previous shortcut files: '+str(backup))
    return backup


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shared-books', action='store_true', help='Wait for registered books supplied by the original library service before starting Field Kit')
    args = parser.parse_args()
    try:
        keep_original(args.shared_books)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print('Field Kit: '+str(error), file=sys.stderr)
        sys.exit(1)
