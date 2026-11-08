# Start here

There are two separate jobs: get Ubuntu working on your Switch, then install Field Kit inside Ubuntu.

## 1. Check where you are starting

| What you see when you turn it on | What to do |
| --- | --- |
| Ubuntu desktop already works | Continue to step 3. Do not repartition a working setup. |
| Hekate works, but Ubuntu is absent | Read the current Switchroot installation guide, back up first and prepare Ubuntu. |
| Only the normal Nintendo menu | Check hardware compatibility first. Field Kit cannot make an incompatible stock console boot Linux. |

“Switch 1” includes different hardware revisions. Some original units support the documented payload route. Patched units and later models have different requirements. Switchroot’s [FAQ](https://wiki.switchroot.org/wiki/faq) explains support for chipped 2019, Lite and OLED units. Hardware work is a separate specialist task, not part of this installer.

## 2. Prepare Ubuntu and preserve your fallback

Use the [official Switchroot Linux page](https://wiki.switchroot.org/wiki/linux) to choose a supported image. The [Noble 24.04 guide](https://wiki.switchroot.org/wiki/linux/l4t-ubuntu-noble-installation-guide) is the upstream reference for a fresh Noble installation. Follow that page’s current prerequisites and steps, rather than an old copied tutorial.

Its partitioning stage can erase the SD card. Back up before that stage, including any separate emuMMC partition you want to retain. Keep backups off the card being changed. This project does not perform that stage for you.

Before continuing, check that Ubuntu starts, the touchscreen and Wi-Fi work, and your existing stock boot option still works. Do not run a general Ubuntu distribution upgrade to move between Switchroot releases. [Switchroot documents that limitation](https://wiki.switchroot.org/wiki/faq).

Create your Ubuntu account with a password you know. `sudo` asks for that Ubuntu password. Automatic sign-in does not mean the account has no password. Do not send passwords to a maintainer or put them in an issue.

## 3. Decide where the library lives

The default is a folder named `SwitchFieldKit` inside your Ubuntu home folder. It is separate from the app code. Start there if you are unsure.

- Leave at least 1 GB free before installing the starter guides. Rendering takes time on the Switch.
- Add Wikipedia and maps after the basic reader works. Check their download sizes first.
- Keep at least 512 MB free. The downloader reserves this minimum.
- FAT32 cannot hold a single file over 4 GB. Large Wikipedia books need the Linux partition or another suitable mounted filesystem.
- The installer does not resize a nearly full Ubuntu partition. It will stop and explain the lack of space.

Advanced users can choose another mounted library folder:

```bash
bash setup.sh --data "/path/to/mounted/library-folder"
```

Mount that storage before opening the library each time. Its files must remain at that path.

## 4. Download and install

1. In Ubuntu, open the [repository](https://github.com/majd-caseresolvetech/switch-field-kit).
2. Choose **Code → Download ZIP**, or download a packaged release.
3. Open Downloads, right-click the ZIP and choose **Extract Here**.
4. Open the extracted folder. Right-click empty space and choose **Open in Terminal**.
5. Type `bash setup.sh` and press Enter.

If PDF tools are missing, the installer can run Ubuntu’s package manager. It asks first, and Ubuntu handles the password prompt. The reader itself installs into your account without administrator access.

Keep the charger connected during the first download. The installer downloads the complete original PDFs and turns each original sheet into a local image. It checks hashes so a changed or incomplete download is not silently accepted.

When it finishes, open **Switch Field Kit** in the Applications menu. There is no login to the app.

## 5. Learn the controls

- **Expert Guides:** filter by region or topic. Only downloaded guides have an Open button.
- **Contents + Find:** jump straight to a method. Search looks inside the saved publication, where its text permits.
- **Enlarge:** tap the page or the button, then use + / −, drag or pinch.
- **Sheet number:** counts PDF sheets, including covers and two-page spreads. Your place is remembered.
- **Wikipedia + Books:** opens your registered ZIM archives and their search.
- **Maps:** opens only installed maps. Closing Maps frees its map renderer.
- **Help:** basic instructions remain on the device.

## 6. Check it without Wi-Fi

Turn Wi-Fi off after downloading. Open a guide, change pages and enlarge a diagram. Search a downloaded book. Inspect your installed maps at the places and zoom levels you need.

No account or internet service is needed for those saved files. A publisher-source link still needs internet, and a guide that was never downloaded will remain unavailable.

## 7. Updates, removal and stock boot

For app updates, download a new release and run its `setup.sh`. Downloaded content stays in its separate folder. The immediately previous app copy is retained for manual recovery.

To remove the application:

```bash
~/.local/bin/fieldkit uninstall
```

This keeps your library data and configuration. It does not remove Ubuntu or change Hekate. Returning to stock uses your existing boot-menu entry. Restoring or repartitioning an SD card is a separate task.
