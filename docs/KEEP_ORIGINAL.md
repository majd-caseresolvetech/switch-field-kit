# Keep the original library

**Only for a device that already has the older Offline Library prototype. New users can skip this page.** The public Field Kit release does not contain that app, its custom walking-map controls, the owner's books or their split-file mounting setup.

The helper preserves an existing working prototype and makes it easy to switch between the two readers. It does not build or download the prototype.

## Make the two readers easy to find

Install or update Field Kit first. In Terminal, inside the extracted release folder, run:

```bash
python3 scripts/keep_original_library.py
~/.local/bin/fieldkit autostart on
```

The helper recognises the original `~/.local/bin/offline-library` launcher. It stops without changing anything if the launcher is absent or has an unfamiliar format. It backs up shortcut files before making these changes:

- **Switch Field Kit** remains the startup reader.
- **Offline Library (original fallback)** gets a green stacked-books icon marked **OLD**, plus an **Offline Library** desktop shortcut.
- The original browser gets its own window identity, so Ubuntu can distinguish it from Field Kit.
- The original browser's login shortcut is disabled. Its server and map services remain enabled as they were.
- On Unity, the two readers are placed together in the launcher. On another desktop, open them from Applications and pin their icons if wanted.

Close any original-library window that was already open, then launch it again. It should show **Field Library** in its title. Return using the **Switch Field Kit** icon. If desktop icons are hidden, use Applications. Close the window you are not using to save memory.

The books, maps, original browser profile and theme extension stay in place. No large files are copied. The original launcher remains independent of Field Kit, including after Field Kit is uninstalled.

## Reuse files without storing a second copy

Register completed `.zim` and compatible `.pmtiles` files using their existing paths. These commands register files without copying them:

```bash
~/.local/bin/fieldkit add-book "/absolute/path/to/existing-book.zim"
~/.local/bin/fieldkit add-map "/absolute/path/to/existing-map.pmtiles" --name "Existing map"
~/.local/bin/fieldkit restart
```

Replace the example paths with files on your device. See [Books and guide content](CONTENT.md) and [Map compatibility](MAPS.md). Install Kiwix and map viewer assets as those pages describe. The helper does not import the prototype's catalogue automatically.

### Only when books depend on the original library's mount service

Some older setups assemble a large Wikipedia archive from split files on FAT32. A registered virtual `.zim` can disappear until that mount is ready. If your working setup uses `switch-offline-library.service` to provide those files, run:

```bash
python3 scripts/keep_original_library.py --shared-books
```

This adds a Field Kit service dependency on the existing original-library service and waits up to 60 seconds for the registered books before starting the reader. It does not create a split-file mount. A missing book causes a clear startup error instead of silently starting without it. Keep that service and its storage available. Do not use this option for an ordinary fresh install.

The setting is in `~/.config/systemd/user/switch-field-kit.service.d/original-library.conf`. To stop using this dependency, remove only that file, then run `systemctl --user daemon-reload` and `~/.local/bin/fieldkit restart`. Preserve other service customisations.

## Recovery

The helper prints a dated backup folder under `~/.local/share/switch-field-kit/original-backups/`. Its `restore-paths.txt` maps each saved file to its previous location. Restore only the files you intend to revert. It never backs up or changes Hekate or the Nintendo system.

If you uninstall Field Kit and want the original reader to open at sign-in again, open Ubuntu's Startup Applications, add the executable `~/.local/bin/offline-library`, and enable it. Alternatively, edit the original `offline-library.desktop` in `~/.config/autostart`: set `Hidden=false` and `X-GNOME-Autostart-enabled=true`. This affects the browser window, not the original library service.

Finish with the [full reboot and stock-fallback check](START_HERE.md#9-test-a-complete-reboot-and-stock-fallback).
