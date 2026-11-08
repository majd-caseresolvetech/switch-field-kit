#!/usr/bin/env bash
set -eu
cd -- "$(dirname -- "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python 3 is missing. On Ubuntu run: sudo apt install python3'
  exit 1
fi
python3 -c 'import sys; assert sys.version_info >= (3, 6), "Python 3.6 or newer is required"'
exec python3 -m fieldkit install "$@"
