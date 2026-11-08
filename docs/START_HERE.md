# Start here

There are two separate jobs: get Ubuntu working on your Switch, then install Field Kit inside Ubuntu.

**Hekate or Ubuntu not installed yet?** Follow [Install Hekate and Switchroot Ubuntu first](INSTALL_HEKATE_UBUNTU.md). It starts with compatibility and backups, then walks through Hekate, SD space, Ubuntu and stock fallback. Return here when the Ubuntu desktop works.

## 1. Check where you are starting

| What you see when you turn it on | What to do |
| --- | --- |
| Ubuntu desktop already works | Continue to step 3. Do not repartition a working setup. |
| Hekate works, but Ubuntu is absent | Follow the [backups and Ubuntu preparation guide](INSTALL_HEKATE_UBUNTU.md#3-back-up-before-changing-the-card). |
| Only the normal Nintendo menu | Start with the [hardware compatibility check](INSTALL_HEKATE_UBUNTU.md#1-check-which-switch-you-have). Field Kit cannot make an incompatible stock console boot Linux. |

“Switch 1” includes different hardware revisions. Some original units support the documented payload route. Patched units and later models have different requirements. Switchroot’s [FAQ](https://wiki.switchroot.org/wiki/faq) explains support for chipped 2019, Lite and OLED units. Hardware work is a separate specialist task, not part of this installer.

## 2. Prepare Ubuntu and preserve your fallback

The [Hekate and Ubuntu walkthrough](INSTALL_HEKATE_UBUNTU.md) covers this stage in order, including what success should look like before moving on.

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

Keep this folder outside the extracted installer and the app's installation folder. Setup rejects those locations because replacing or removing app code must never delete your library.

## 4. Download and install

Use **0.1.3 or newer** for the startup and shortcut features in this guide. If the release page still shows an older version, use this [tested 0.1.3 source ZIP](https://github.com/majd-caseresolvetech/switch-field-kit/archive/8436b14e895d45db635be21269b41a4f697cc5a9.zip), then continue at step 3. It installs directly with the same command, without building anything.

1. In Ubuntu, open the [latest tested release](https://github.com/majd-caseresolvetech/switch-field-kit/releases/latest).
2. Under **Assets**, download `switch-field-kit-<version>.zip`. The version is part of the filename. Node, npm and Git are not needed to install it.
3. Open Downloads, right-click the ZIP and choose **Extract Here**.
4. Open the extracted folder. Right-click empty space and choose **Open in Terminal**.
5. Type `bash setup.sh` and press Enter.

If PDF tools are missing, the installer can run Ubuntu’s package manager. It asks first, and Ubuntu handles the password prompt. The reader itself installs into your account without administrator access.

Keep the charger connected during the first download. The installer downloads the complete original PDFs and turns each original sheet into a local image. It checks hashes so a changed or incomplete download is not silently accepted.

When it finishes, open **Switch Field Kit** in the Applications menu or its named desktop shortcut. There is no login to the app. Setup also makes it open automatically the next time you sign in to Ubuntu.

If a desktop shortcut says **Untrusted**, choose **Allow Launching** or **Trust and Launch**. Some desktops hide desktop icons. In that case, use the Applications menu, then right-click the running icon and choose **Keep in Launcher** or **Pin**. The Field Kit icon is a green terminal marked **FIELD KIT**.

Setup checks that the reader is running before reporting success. If only a content download fails, the reader remains installed and explains the retry command. If you skip the PDF tools, you can still open the reader, but must install those tools before downloading guides. Do not run the whole setup again just because one publisher was unavailable.

In **HELP**, use **COPY COMMAND**, open Ubuntu Terminal, paste and press Enter. A password prompt, if shown by Ubuntu, uses your Ubuntu account password. After a download finishes, choose **REFRESH LIBRARY**. The commands use the full launcher path so they also work before your next sign-in.

For Wikipedia, open **WIKIPEDIA + BOOKS** and follow the numbered steps. For maps, open **MAPS**, choose an area and copy its command. The map download shows the expected size and asks before fetching the tiles. The app ZIP contains the reader and catalogue, not preloaded Wikipedia or maps.

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

## 7. Open straight into Field Kit

The full startup chain has three parts:

| Stage | What to set | Who handles it |
| --- | --- | --- |
| Hekate → Ubuntu | Select your installed Ubuntu entry for autoboot in Hekate's **Options**, keep a 3-second boot wait, then save. | You, in Hekate. |
| Ubuntu → desktop | Enable **Automatic Login** for your account in Ubuntu's user/login settings if you want no sign-in screen. The location varies between Unity, GNOME and Kubuntu. | You, in Ubuntu. |
| Desktop → Field Kit | Enabled by normal Field Kit setup. | This installer. |

Start with a known working Ubuntu and stock entry. Do not replace `hekate_ipl.ini` with another console's file or choose a boot-entry number copied from a guide. [Hekate documents its autoboot settings](https://github.com/CTCaer/hekate#bootloader-configuration). For a USB-payload console, autoboot begins **after Hekate is loaded**. It does not remove the need to send a payload after a full power-off.

Automatic login removes the Ubuntu sign-in step for anyone holding the device. It does not remove your account password or change the password used by `sudo`. The installer does not edit Ubuntu's login configuration. [Ubuntu's automatic-login guide](https://help.ubuntu.com/stable/ubuntu-help/user-autologin.html.en).

To choose whether the Field Kit window opens at sign-in:

```bash
~/.local/bin/fieldkit autostart on
```

Replace `on` with `off` to open it manually. Your choice survives app updates. For a first install without automatic opening, use `bash setup.sh --no-autostart`. Advanced `--no-service` installations do not enable automatic opening.

## 8. Keep an older library, if you have one

New users can skip this step. Field Kit is the public app. The original prototype and its larger personal collection are not bundled.

If `Offline Library` is already installed, follow [Keep the original library](KEEP_ORIGINAL.md). The helper gives it a green stacked-books icon marked **OLD**, keeps Field Kit as the only startup window, and preserves the old files and services. You can use both without duplicating the large books and maps.

## 9. Test a complete reboot and stock fallback

Do this while you have the charger and your usual Hekate boot method available:

1. Use Ubuntu's normal **Restart** menu. Do not open Field Kit yourself. Check that Ubuntu signs in and Field Kit opens automatically.
2. Check a saved guide, an enlarged diagram, a book and a map. If you kept the older library, open its **OLD** shortcut and return using **Switch Field Kit**. Close the unused window to save memory.
3. Restart Ubuntu again and immediately hold **Volume Down** until Hekate's menu appears. Release it. Choose your existing stock entry. On the tested console this was **Launch → 100% STOCK OFW**. Your entry may have a different name. A CFW or emuMMC entry is not the stock-fallback test.
4. Confirm the normal Nintendo **HOME** menu appears. Seeing a stock option listed in Hekate is not enough.
5. In Nintendo's system, hold Power for about 3 seconds, choose **Power Options → Turn Off**, then start with your usual Hekate method. Let Ubuntu and Field Kit start automatically again.
6. Repeat the reading checks with Wi-Fi off. Confirm you can boot offline too, including sending a saved payload if your console needs one.

If you reach Hekate or a login screen instead of Field Kit, check the relevant stage in section 7. If Ubuntu opens but Field Kit does not, use [startup troubleshooting](TROUBLESHOOTING.md#ubuntu-opens-but-field-kit-does-not-open-automatically). Do not reformat the card to fix an app launcher.

The reboot, stock HOME screen, return to Field Kit and original-library access were checked on the owner's existing Switch. [Testing status](TESTING.md) distinguishes that device result from fresh-install and battery-life coverage.

## 10. Updates and removal

For app updates, download a new release and run `bash setup.sh --no-guides` in its extracted folder. Downloaded content stays in its separate folder. The immediately previous app copy is retained for manual recovery. Close and reopen the reader after an update, then repeat the startup check. Use `~/.local/bin/fieldkit guides all` separately if you want to add missing guides.

To remove the application:

```bash
~/.local/bin/fieldkit uninstall
```

This removes Field Kit's desktop and login shortcuts, and keeps your library data and configuration. An original-library shortcut created by the helper remains usable independently. It does not remove Ubuntu or change Hekate. Returning to stock uses your existing boot-menu entry. Restoring or repartitioning an SD card is a separate task.
