import argparse
import json
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(description='Switch Field Kit: original guides, books and maps offline.')
    sub = parser.add_subparsers(dest='command')
    setup = sub.add_parser('install', help='Install the user app, launcher and service')
    setup.add_argument('--data', help='Library folder. Default: ~/SwitchFieldKit')
    setup.add_argument('--port', type=int)
    setup.add_argument('--no-system', action='store_true', help='Do not offer apt installation')
    setup.add_argument('--no-service', action='store_true', help='Copy app only, without enabling systemd')
    choice = setup.add_mutually_exclusive_group()
    choice.add_argument('--guides', dest='guides', action='store_true')
    choice.add_argument('--no-guides', dest='guides', action='store_false')
    setup.set_defaults(guides=None)
    serve = sub.add_parser('serve', help='Run locally in this terminal')
    serve.add_argument('--port', type=int)
    serve.add_argument('--kiwix-port', type=int)
    guides = sub.add_parser('guides', help='Download checked publisher originals')
    guides.add_argument('selection', nargs='?', default='all', help='all or comma-separated guide IDs')
    sub.add_parser('list', help='List available original guides')
    sub.add_parser('doctor', help='Check dependencies, space and saved PDFs')
    sub.add_parser('open', help='Open the offline library')
    sub.add_parser('restart', help='Restart the user service after importing books')
    sub.add_parser('kiwix', help='Download pinned upstream Kiwix tools')
    book = sub.add_parser('add-book', help='Register a local ZIM file without copying it')
    book.add_argument('path')
    book.add_argument('--title')
    sub.add_parser('map-tools', help='Download pinned offline map viewer assets')
    amap = sub.add_parser('add-map', help='Register a Protomaps v4 PMTiles map')
    amap.add_argument('path')
    amap.add_argument('--name', required=True)
    download = sub.add_parser('download-map', help='Estimate and download a regional Protomaps map')
    download.add_argument('preset', choices=['world','uk','lebanon','prague','europe-levant'])
    download.add_argument('--date', help='Optional Protomaps build date YYYYMMDD')
    download.add_argument('--plan', action='store_true', help='Show size without downloading map tiles')
    download.add_argument('--yes', action='store_true', help='Accept the calculated download size')
    sub.add_parser('uninstall', help='Remove the app while preserving your content')
    sub.add_parser('help', help='Show commands')
    args = parser.parse_args()
    try:
        if args.command == 'install':
            from .install import install
            install(args)
        elif args.command == 'serve':
            from .server import serve
            serve(args.port, args.kiwix_port)
        elif args.command == 'guides':
            from .content import install_guides
            install_guides(args.selection)
        elif args.command == 'list':
            from .common import catalogue
            for d in catalogue():
                print('%-18s %s (%s, %s)' % (d['id'], d['title'], d['region'], d['language']))
        elif args.command == 'doctor':
            from .install import doctor
            doctor()
        elif args.command == 'open':
            from .install import open_library
            open_library()
        elif args.command == 'restart':
            subprocess.check_call(['systemctl', '--user', 'restart', 'switch-field-kit.service'])
        elif args.command == 'kiwix':
            from .books import install_kiwix
            install_kiwix()
        elif args.command == 'add-book':
            from .books import add_book
            add_book(args.path, args.title)
        elif args.command == 'map-tools':
            from .maps import install_map_tools
            install_map_tools()
        elif args.command == 'add-map':
            from .maps import add_map
            add_map(args.path, args.name)
        elif args.command == 'download-map':
            from .maps import download_map
            download_map(args.preset, args.date, args.yes, args.plan)
        elif args.command == 'uninstall':
            from .install import uninstall
            uninstall()
        else:
            parser.print_help()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as e:
        print('\nField Kit: '+str(e), file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
