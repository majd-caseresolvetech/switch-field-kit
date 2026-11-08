# Switch Field Kit 0.1.3

Makes the tested startup and library-shortcut setup repeatable from the public download.

- Field Kit opens automatically after Ubuntu sign-in on a normal first installation. Use `fieldkit autostart off` or `on` to choose. Updates preserve that choice.
- Applications and desktop shortcuts use a clear green Field Kit icon and a distinct window identity.
- Desktop launchers also work with spaces and percent signs in their paths on older Ubuntu installations.
- An optional helper preserves an already installed original Offline Library, gives it a separate **OLD** icon, and disables only its automatic browser window. Its books, maps and services stay in place.
- Existing shared-book setups can make Field Kit wait for the original mount service. No large files are copied and no split-file mount is created by this release.
- The guide now covers the complete Hekate → Ubuntu sign-in → Field Kit chain, stock fallback, returning to Ubuntu, and the exact checks to repeat on your own console.
- Uninstall removes Field Kit's login and desktop shortcuts while keeping content and the independently working original library.

**Update:** extract this release, open Terminal in its folder and run `bash setup.sh --no-guides`. Close and reopen Field Kit afterwards. For a new installation, use `bash setup.sh` and follow [Start here](docs/START_HERE.md). Original-library users should also follow [Keep the original library](docs/KEEP_ORIGINAL.md).

All 26 automated tests passed on the Switch's Python 3.6.9. The packaged 0.1.3 code also passed an isolated real-service and desktop-launch test on systemd 237, including paths with spaces and percent signs. The full reboot, stock HOME screen, return to Field Kit and original-reader access passed using 0.1.2 with the local changes now included here. This does not claim a tested clean Noble installation or measured battery runtime. [Verification details](docs/TESTING.md).

The original prototype and the owner's full collection are not bundled. Fresh installs download the guide catalogue and add chosen Wikipedia books and maps separately. Hekate, partitions and stock boot are not modified by the installer.

## Version 0.1.2

Fixes startup on older Switchroot Ubuntu installations using systemd 237. That version interprets the quoted working-directory path in 0.1.1 literally and refuses to start the reader. The service now uses a quoted Python module path instead.

Verified on an ARM64 Switch running Python 3.6.9, including a real service launched from paths containing spaces and percent signs. All 17 tests passed, and the installed reader served 27 original guides, 10 existing book collections and six existing map archives. These collections are the owner's test library and are not bundled with the release.

If 0.1.1 reports an `Exec format error`, extract this release and run `bash setup.sh --no-guides` as your usual Ubuntu user. It replaces the app and service while retaining the separate library. No SD formatting or Ubuntu reinstall is needed.

## Version 0.1.1

This update makes a fresh installation easier to finish and recover when optional downloads fail.

- Copyable commands work before the next Ubuntu sign-in. Empty library screens explain where to paste them and when to refresh.
- Maps offer UK, Lebanon, Prague, world and Europe-to-Levant choices. The downloader still checks size and asks before downloading tiles.
- Wikipedia setup is split into numbered steps. A missing Kiwix program no longer stops guides and maps from opening.
- The installer checks the running reader, explains missing PDF tools and incomplete guide downloads, and preserves a custom configuration for the launcher and login service.
- Libraries cannot be placed inside app folders that an update or uninstall may remove.
- Continue Reading returns to the last guide. Enlarged pages are centred when they fit the screen.
- The release includes the Hekate and Switchroot Ubuntu preparation guide.

To update, extract this release and run `bash setup.sh` as your usual Ubuntu user. Existing content stays in its separate library folder. Hekate, SD partitions and stock boot are not changed.

The app ZIP does not contain Wikipedia books or maps. Download them from the reader's setup instructions after installation. See [verification and limits](docs/TESTING.md).

## Version 0.1.0

First public prototype of an offline reference reader for a compatible Switch running Switchroot Ubuntu.

- Beginner setup, user service, Applications launcher, diagnostics and uninstall.
- Download catalogue for 27 complete publisher publications, 466 original PDF sheets.
- Region/topic filters, method shortcuts, text/section search, image zoom and saved reading position.
- Optional Kiwix book import and offline full-text search.
- Optional regional Protomaps downloads and offline map rendering.
- English, Arabic and Czech communication phrases with an SOS reference.
- MIT-licensed application code. Publisher content and upstream assets are downloaded separately under their own terms.

Start with README.md and docs/START_HERE.md. The ZIP is the app source and installer, not a ready-to-flash SD image. It requires an already working Switchroot Ubuntu setup. No firmware, personal configuration or downloaded books are included.

See docs/TESTING.md for the tested environments and current limitations. Complete regional foraging identification is not included.
