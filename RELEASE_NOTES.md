# Switch Field Kit 0.1.1

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
