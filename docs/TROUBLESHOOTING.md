# Troubleshooting

## `fieldkit: command not found`

Your terminal may not yet include `~/.local/bin` in its search path. Use the full command:

```bash
~/.local/bin/fieldkit doctor
```

Logging out of Ubuntu and back in often makes the short command available.

## The app opens but the guides are not installed

```bash
~/.local/bin/fieldkit guides all
```

This downloads only the checked editions and skips completed guides. Keep the charger connected. The first rendering can take several minutes. Refresh the app afterwards.

## A PDF download says its checksum changed

The publisher may have replaced the file. Field Kit refuses to silently install a different edition with old section labels. Check for a newer app release. Report the guide ID, not a copy of the book or your private files.

## A download was interrupted

Run the same command again. Downloads use a `.part` file and attempt HTTP resume. Some publisher servers do not support resume. If the error names that problem, delete only the named `.part` file and retry. Never erase the entire library to repair one download.

## PDF tools are missing

```bash
sudo apt install curl ca-certificates poppler-utils
```

Ubuntu asks for your Ubuntu password. Field Kit cannot recover that password. Do not paste it into an issue or support chat.

## The launcher does not open

```bash
~/.local/bin/fieldkit doctor
systemctl --user status switch-field-kit.service
journalctl --user -u switch-field-kit.service -n 40 --no-pager
```

For a foreground check:

```bash
systemctl --user stop switch-field-kit.service
~/.local/bin/fieldkit serve
```

Open the printed localhost address. Press Ctrl+C when finished, then run `~/.local/bin/fieldkit restart`.

Do not add `--no-sandbox` to the browser to hide a launch problem. Use a working browser from the supported Switchroot environment. The app can also be opened by typing its localhost address into Firefox or Chromium.

## A port is already in use

Field Kit defaults to 8095 and uses 8096 for its optional Kiwix child process. These differ from the private prototype’s ports. Change `port` and `kiwix_port` in `~/.config/switch-field-kit/config.json` to two unused ports above 1023, then restart. Do not stop an unrelated service just to free its port.

## A map is blank

Run `~/.local/bin/fieldkit map-tools`. Make sure the registered map file is still present and mounted. Use Protomaps v4 vector data. Check that Ubuntu’s browser can use WebGL. A guide PDF still works even if the graphics driver cannot display a map.

## A book disappeared

The book is registered by its full filename without copying it. If you moved it or unplugged its storage, mount it at the original location or add its new path. Then restart Field Kit. Add only finished `.zim` downloads. The first release does not assemble split `.zimaa` files.

## Storage is almost full

Do not remove Hekate, stock-system files or partitions from this app. Remove or move optional books and maps you understand, or choose a larger library location. Keep the original source and a backup before deleting anything important.

## Restore the previous app after an update

Stop `switch-field-kit.service`. The preceding app copy is kept at `~/.local/share/switch-field-kit/previous`. Rename the current `app` folder to `app.failed`, then rename `previous` to `app`, and restart the service. Keep your library data and configuration intact. There is no rollback of Ubuntu or firmware because Field Kit does not modify them.

## Reporting a problem

Include the app version, Switch model, Ubuntu version, failing command and guide/map ID. Read logs before sharing them. Remove usernames, local paths or other information you do not want public. Never upload passwords, SSH keys, serial numbers, NAND backups or account cookies.
