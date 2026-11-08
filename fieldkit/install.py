"""Install only this user's app, launcher and service. Never touch boot media."""
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

from .common import APP, atomic, config, config_path, data_dir, enough_space, read_json, write_json
from . import __version__

def app_home():
    return Path(os.environ.get('XDG_DATA_HOME', str(Path.home()/'.local/share')))/'switch-field-kit'

def user_config():
    return Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config')))

def unit_quote(value):
    value = str(value)
    if '\n' in value or '\r' in value:
        raise ValueError('Paths cannot contain a line break.')
    return '"'+value.replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%')+'"'

def service_text(app):
    # systemd 237 treats quotes in WorkingDirectory as literal path characters.
    # The app uses absolute paths, so a quoted environment value avoids that
    # parser difference while also supporting spaces and percent signs.
    return '[Unit]\nDescription=Switch Field Kit offline library\n\n[Service]\nType=simple\nEnvironment='+unit_quote('PYTHONPATH='+str(app))+'\nEnvironment='+unit_quote('FIELDKIT_CONFIG='+str(config_path().resolve()))+'\nExecStart='+unit_quote(sys.executable)+' -m fieldkit serve\nRestart=on-failure\nRestartSec=5\n\n[Install]\nWantedBy=default.target\n'

def check_library_location(path, source=True):
    """Updates and removal must never delete a library nested in managed code."""
    path = Path(path).resolve()
    roots = [app_home().resolve()]
    if source:
        roots.append(APP.resolve())
    if any(path == root or root in path.parents for root in roots):
        raise ValueError('Keep the library outside the app and extracted installer folders. Choose ~/SwitchFieldKit or a separate mounted folder.')

def reader_ready(settings, timeout=10):
    import urllib.request
    url = 'http://127.0.0.1:'+str(settings['port'])+'/api/health'
    deadline = time.monotonic()+timeout
    while True:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                health = json.load(response)
                if health.get('app') == 'Switch Field Kit' and health.get('version') == __version__:
                    return True
        except (OSError, ValueError):
            pass
        if time.monotonic() >= deadline:
            return False
        time.sleep(.25)

def ask(message, default=False):
    if not sys.stdin.isatty():
        return default
    answer = input(message+(' [Y/n] ' if default else ' [y/N] ')).strip().lower()
    return default if not answer else answer in ('y', 'yes')

def install(args):
    if platform.system() != 'Linux':
        raise RuntimeError('Setup installs on Linux. For a local preview, use: python3 -m fieldkit serve')
    if os.geteuid() == 0:
        raise RuntimeError('Run setup as your normal Ubuntu user, without sudo. It installs into your home folder.')
    print('Switch Field Kit '+__version__+'\nInstalls in your Ubuntu home folder. Stock boot and SD partitions are not changed.\n')
    missing = [x for x in ('pdfinfo', 'pdftoppm', 'pdftotext') if not shutil.which(x)]
    if missing and not args.no_system:
        print('Missing tools: '+', '.join(missing))
        if ask('Install curl, certificate support and PDF tools using Ubuntu?'):
            subprocess.check_call(['sudo', 'apt-get', 'update'])
            subprocess.check_call(['sudo', 'apt-get', 'install', '-y', 'curl', 'ca-certificates', 'poppler-utils'])
    missing = [x for x in ('pdfinfo', 'pdftoppm', 'pdftotext') if not shutil.which(x)]
    if missing and args.guides is True:
        from .content import pdf_tools
        pdf_tools()
    if not args.no_service:
        if not shutil.which('systemctl') or subprocess.call(['systemctl', '--user', 'show-environment'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL):
            raise RuntimeError('The Ubuntu login service is unavailable. Run setup from Terminal in your Ubuntu desktop as your normal user. For a manual installation, use --no-service --no-guides.')
    settings = config()
    if args.data:
        settings['data'] = str(Path(args.data).expanduser().resolve())
    if args.port:
        settings['port'] = args.port
    for key in ('port', 'kiwix_port'):
        if not isinstance(settings[key], int) or not 1024 <= settings[key] <= 65535:
            raise ValueError('Choose ports from 1024 to 65535.')
    if settings['port'] == settings['kiwix_port']:
        raise ValueError('The reader and Kiwix need different ports.')
    check_library_location(settings['data'])
    Path(settings['data']).mkdir(parents=True, exist_ok=True)
    enough_space(settings['data'], 20*1024*1024)
    destination = app_home()
    destination.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(dir=str(destination), prefix='.install-'))
    previous = destination/'previous'
    target = destination/'app'
    try:
        for name in ('fieldkit', 'web', 'catalogues', 'docs'):
            shutil.copytree(str(APP/name), str(stage/name), ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for name in ('LICENSE', 'THIRD_PARTY.md', 'README.md', 'setup.sh'):
            shutil.copy2(str(APP/name), str(stage/name))
        if previous.exists():
            shutil.rmtree(str(previous))
        if target.exists():
            target.rename(previous)
        stage.rename(target)
    except BaseException:
        if not target.exists() and previous.exists():
            previous.rename(target)
        raise
    finally:
        if stage.exists():
            shutil.rmtree(str(stage))
    write_json(config_path(), settings)
    bindir = Path.home()/'.local/bin'
    bindir.mkdir(parents=True, exist_ok=True)
    launcher = '#!/bin/sh\nexport FIELDKIT_CONFIG='+shlex.quote(str(config_path().resolve()))+'\ncd '+shlex.quote(str(target))+' || exit 1\nexec '+shlex.quote(sys.executable)+' -m fieldkit "$@"\n'
    atomic(bindir/'fieldkit', launcher.encode())
    (bindir/'fieldkit').chmod(0o755)
    units = user_config()/'systemd/user'
    units.mkdir(parents=True, exist_ok=True)
    atomic(units/'switch-field-kit.service', service_text(target).encode())
    desktop = '[Desktop Entry]\nType=Application\nName=Switch Field Kit\nComment=Original guides, Wikipedia and maps without internet\nExec='+unit_quote(bindir/'fieldkit')+' open\nIcon=accessories-dictionary\nTerminal=false\nCategories=Education;Utility;\n'
    applications = Path(os.environ.get('XDG_DATA_HOME', str(Path.home()/'.local/share')))/'applications'
    atomic(applications/'switch-field-kit.desktop', desktop.encode())
    if not args.no_service:
        subprocess.check_call(['systemctl', '--user', 'daemon-reload'])
        subprocess.check_call(['systemctl', '--user', 'enable', '--now', 'switch-field-kit.service'])
        subprocess.check_call(['systemctl', '--user', 'restart', 'switch-field-kit.service'])
        if not reader_ready(settings) or subprocess.call(['systemctl', '--user', 'is-active', '--quiet', 'switch-field-kit.service']):
            raise RuntimeError('App files are installed, but the reader did not start correctly. Open Terminal and run: journalctl --user -u switch-field-kit.service -n 40 --no-pager. Check for a port conflict before retrying ~/.local/bin/fieldkit restart.')
    wanted = args.guides
    if missing:
        wanted = False
        print('\nReader installed without PDF tools. To add guides later, run:\nsudo apt install poppler-utils\n~/.local/bin/fieldkit guides all')
    elif wanted is None:
        wanted = ask('Download the 27 original guides now? About 128 MB download, allow 1 GB free for rendering.', True)
    download_error = None
    if wanted:
        from .content import install_guides
        try:
            install_guides('all')
        except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as e:
            download_error = e
    if args.no_service:
        print('\nApp files installed. Start the manual reader with: ~/.local/bin/fieldkit serve')
    else:
        print('\nReader is running. Open “Switch Field Kit” from your Applications menu.')
    print('Browser address: http://127.0.0.1:'+str(settings['port'])+'/')
    print('Use HELP in the reader for adding guides, books and maps. Refresh after each download.')
    print('Commands: '+str(bindir/'fieldkit')+' help')
    print('Guides and maps stay in '+settings['data'])
    if download_error:
        raise RuntimeError('The reader is installed, but guide downloads are incomplete. '+str(download_error)+'\nYou can retry all missing guides with ~/.local/bin/fieldkit guides all. No reinstall is needed.')

def open_library():
    settings = config()
    if platform.system() == 'Linux' and shutil.which('systemctl'):
        subprocess.run(['systemctl', '--user', 'start', 'switch-field-kit.service'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = 'http://127.0.0.1:'+str(settings['port'])+'/'
    if not reader_ready(settings):
        raise RuntimeError('The reader is not running. Run ~/.local/bin/fieldkit doctor, then ~/.local/bin/fieldkit restart.')
    for name in ('chromium-browser', 'chromium', 'google-chrome'):
        binary = shutil.which(name)
        if binary:
            profile = app_home()/'browser'
            subprocess.Popen([binary, '--user-data-dir='+str(profile), '--no-first-run', '--no-default-browser-check',
                              '--disable-sync', '--disable-background-networking', '--password-store=basic',
                              '--start-maximized', '--app='+url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
    import webbrowser
    if not webbrowser.open(url):
        print('Open this address in your browser: '+url)

def uninstall():
    if platform.system() != 'Linux' or os.geteuid() == 0:
        raise RuntimeError('Uninstall as the normal Linux account used for setup.')
    check_library_location(config()['data'], source=False)
    print('Removes the app and login service. Keeps downloaded books, guides, maps and your configuration.')
    if not ask('Uninstall Switch Field Kit?'):
        return
    subprocess.run(['systemctl', '--user', 'disable', '--now', 'switch-field-kit.service'])
    paths = [user_config()/'systemd/user/switch-field-kit.service', Path.home()/'.local/bin/fieldkit',
             Path(os.environ.get('XDG_DATA_HOME', str(Path.home()/'.local/share')))/'applications/switch-field-kit.desktop']
    for p in paths:
        if p.exists():
            p.unlink()
    for p in (app_home()/'app', app_home()/'previous'):
        if p.is_dir():
            shutil.rmtree(str(p))
    subprocess.run(['systemctl', '--user', 'daemon-reload'])
    print('App removed. Your library remains at '+config()['data'])

def doctor():
    import socket
    from .content import verify_content
    settings = config()
    report = {'version':__version__, 'system':platform.system(), 'machine':platform.machine(),
              'python':platform.python_version(), 'data':settings['data'],
              'free_bytes':shutil.disk_usage(str(data_dir())).free,
              'tools':{n:bool(shutil.which(n)) for n in ('curl', 'pdfinfo', 'pdftoppm', 'pdftotext')},
              'content':verify_content()}
    print(json.dumps(report, indent=2))
    if report['content']['issues']:
        raise RuntimeError('Some saved files need repair. Re-run the affected guide download.')
