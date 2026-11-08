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
    return '[Unit]\nDescription=Switch Field Kit offline library\n\n[Service]\nType=simple\nWorkingDirectory='+unit_quote(app)+'\nExecStart='+unit_quote(sys.executable)+' -m fieldkit serve\nRestart=on-failure\nRestartSec=5\n\n[Install]\nWantedBy=default.target\n'

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
    print('Switch Field Kit 0.1.0\nInstalls in your Ubuntu home folder. Stock boot and SD partitions are not changed.\n')
    missing = [x for x in ('pdfinfo', 'pdftoppm', 'pdftotext') if not shutil.which(x)]
    if missing and not args.no_system:
        print('Missing tools: '+', '.join(missing))
        if ask('Install curl, certificate support and PDF tools using Ubuntu?'):
            subprocess.check_call(['sudo', 'apt-get', 'update'])
            subprocess.check_call(['sudo', 'apt-get', 'install', '-y', 'curl', 'ca-certificates', 'poppler-utils'])
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
    launcher = '#!/bin/sh\ncd '+shlex.quote(str(target))+' || exit 1\nexec '+shlex.quote(sys.executable)+' -m fieldkit "$@"\n'
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
    wanted = args.guides
    if wanted is None:
        wanted = ask('Download the 27 original guides now? About 128 MB download, allow 1 GB free for rendering.', True)
    if wanted:
        from .content import install_guides
        install_guides('all')
    print('\nInstalled. Open “Switch Field Kit” from your Applications menu.')
    print('Commands: '+str(bindir/'fieldkit')+' help')
    print('Guides and maps stay in '+settings['data'])

def open_library():
    settings = config()
    if platform.system() == 'Linux' and shutil.which('systemctl'):
        subprocess.run(['systemctl', '--user', 'start', 'switch-field-kit.service'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import urllib.request
    url = 'http://127.0.0.1:'+str(settings['port'])+'/'
    for attempt in range(40):
        try:
            with urllib.request.urlopen(url+'api/health', timeout=1) as response:
                if json.load(response).get('app') == 'Switch Field Kit':
                    break
        except Exception:
            pass
        time.sleep(.25)
    else:
        raise RuntimeError('The reader is not running. Run fieldkit doctor, then fieldkit restart.')
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
    report = {'version':'0.1.0', 'system':platform.system(), 'machine':platform.machine(),
              'python':platform.python_version(), 'data':settings['data'],
              'free_bytes':shutil.disk_usage(str(data_dir())).free,
              'tools':{n:bool(shutil.which(n)) for n in ('curl', 'pdfinfo', 'pdftoppm', 'pdftotext')},
              'content':verify_content()}
    print(json.dumps(report, indent=2))
    if report['content']['issues']:
        raise RuntimeError('Some saved files need repair. Re-run the affected guide download.')
