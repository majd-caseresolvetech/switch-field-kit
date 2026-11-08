# Architecture

The application is a local HTTP reader with optional content tools. The reading path uses Python's standard library, static HTML, CSS and JavaScript. Node is only a development dependency for browser checks.

| Location | Purpose |
| --- | --- |
| `fieldkit/` | Installer, publisher downloader, PDF renderer, loopback server and optional book/map tools |
| `web/` | Touch interface, one-sheet reader, image zoom, map viewer and Kiwix theme |
| `catalogues/guides.json` | Metadata and verified hashes for 27 publisher originals |
| `catalogues/tools.json` | Pinned upstream tool and asset downloads |
| `~/SwitchFieldKit` | Default user content and optional downloaded tools |
| `~/.local/share/switch-field-kit/app` | Installed app code |
| `~/.config/switch-field-kit/config.json` | Data folder and ports |
| `~/.config/systemd/user/switch-field-kit.service` | User service, not a root service |
| `~/.config/autostart/switch-field-kit.desktop` | Opens the browser after desktop sign-in |
| `fieldkit/desktop.py` | Desktop files, distinct window identity and startup preference |
| `scripts/keep_original_library.py` | Optional adapter for an already installed prototype |

The app binds to loopback port 8095. Optional Kiwix binds to 8096, starts as a child and exits with the app. A local reverse proxy keeps book navigation under the app origin. Original PDFs remain byte-for-byte unchanged. Display pages are generated locally with Poppler.

The server has no content mutation endpoints. Downloads are explicit CLI operations. A writer lock prevents concurrent catalogue/import mutations. Atomic file replacement protects completed content. Downloads leave at least 512 MB free, and map extraction checks space while running.

Maps use local PMTiles range requests, local JavaScript bundles, local glyphs and local sprites. The map iframe is destroyed on leaving the tab. The reader has no animation loop, timed PDF prefetch or service-worker cloud cache.

Environment overrides for development: `FIELDKIT_DATA`, `FIELDKIT_CONFIG`, `XDG_DATA_HOME`, `XDG_CONFIG_HOME`. Use temporary folders for tests. Never point a test at someone’s active content directory.

The installer intentionally has no partition, Hekate, boot-ROM, modchip or firmware code. Hardware preparation belongs to the upstream Switchroot documentation.

Starting the local service and opening its browser window are separate steps. Normal setup enables both. `autostart off` disables only the window. The browser uses its own profile and the `SwitchFieldKit` window class. The optional original-library adapter uses `OriginalOfflineLibrary`, backs up old shortcuts and leaves the old launcher independent of this app. Its optional service dependency waits for existing registered books, but does not implement a split-file mount.
