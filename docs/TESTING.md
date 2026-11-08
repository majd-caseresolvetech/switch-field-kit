# Verification

## Version 0.1.2 native service fix

Checked on 8 November 2026 on an ARM64 Switch with Python 3.6.9 and systemd 237:

- All 17 automated tests passed on the device.
- A real systemd service exposed a startup bug missed by the isolated installer tests: systemd 237 treats quotes in `WorkingDirectory` as literal path characters. Version 0.1.2 uses an environment variable for Python's module path instead.
- The revised service started successfully with an app path and a configuration path containing spaces and percent signs. The test used the real user service manager and checked the HTTP health response before removing its temporary service.
- Normal installation and service startup passed. Diagnostics verified all 27 saved original PDFs and the presence of their page images.
- The reader registered the owner's 10 existing ZIM collections and six PMTiles archives without copying those large files. Its Kiwix endpoint responded, all books were present, and all six maps served valid byte-range responses.
- The Hekate configuration checksum stayed unchanged. The original library remained available.

This was an existing Ubuntu installation, not a fresh Noble installation or a test of every hardware variant. A complete reboot and long-duration battery life remain untested. Device-specific split-Wikipedia mounting is managed by the owner's existing setup, not by the public installer.

## Version 0.1.1 review

Reviewed on 8 November 2026:

- 17 automated tests passed locally. Added coverage for missing PDF tools, failed downloads, custom configuration outside the setup shell, startup failure, unsafe library locations and a missing Kiwix executable.
- The new-install interface was checked in a browser with no downloaded content. The map picker generates a concrete command for each named preset, while book setup explains how to replace its example filename.
- A populated local library still opens original pages, enlarges them, offers Continue Reading and loads its saved maps. The enlarged-page fit is centred.
- Browser regression checks cover the new empty states, clipboard content and narrow layout. The GitHub Actions result for the exact commit records their outcome.
- Release checks build the versioned ZIP and exclude personal files and downloaded publisher material. The new Hekate and Ubuntu guide is included.

The physical Switch was initially unreachable during this review. When it reconnected, a real service installation found the systemd 237 startup bug described above. Use 0.1.2 or later for that fix.

## Version 0.1.0 hardware and content checks

Release checks performed on 8 November 2026:

- Nine automated tests passed on Python 3.6.9 on a Switch running Ubuntu and Python 3.12 on macOS. These cover installation, repeat installation, removal without deleting content, configuration validation, book registration, map metadata, HTTP byte ranges and blocking paths outside the library.
- The installer ran in an isolated folder on the Switch's ARM64 hardware. It fetched the original Scouts shelter PDF, verified its checksum and rendered all nine pages. The installed reader served its health response and a page image.
- Kiwix 3.8.2 for Linux ARM64 downloaded, passed checksum verification and ran on that Switch.
- All 27 original PDFs passed local checksum checks. All 466 rendered page images decoded successfully.
- Chromium browser checks passed with outside requests blocked. They covered regional filters, search, page opening, contents shortcuts, enlargement, saved reading position, the other tabs and layouts at 1280 by 720 and 720 by 506.
- A real Prague PMTiles map rendered with local fonts, symbols and map data. No external requests or browser errors were recorded during that check.
- The release audit excluded publisher downloads, device keys, firmware, backups and private device settings. The package contains source code, a screenshot and download metadata.

The live ARM map-tool download encountered an upstream GitHub HTTP 504 timeout. Its binary is pinned by size and checksum, but that native download and extraction path was not fully verified in this release session. The map viewer and registering an existing compatible archive were tested separately. If a download fails, retry it when the upstream service is available.

The Switch test used a separate temporary app and data directory. It did not replace the owner's existing library. The existing library services remained active and the Hekate configuration checksum was unchanged.

This is an initial release. A clean Switchroot Noble installation, every Switch hardware variant, the desktop service across a full reboot, physical touch interactions and long-duration battery life have not been validated. No battery-runtime claim is made. Publisher accuracy and suitability for a particular emergency are not established by these software tests.

## Repeat the checks

```bash
python3 -m unittest discover -s tests -v
python3 scripts/audit_release.py
python3 -m fieldkit doctor
```

`doctor` checks the installed original PDFs and whether expected page images are present. It does not fact-check publications.

The GitHub Actions workflow runs tests on Ubuntu 24.04, renders project-owned PDF fixtures, tests the browser with external requests blocked and builds a ZIP. It does not redistribute publisher PDFs or test physical Switch hardware. Check the Actions result for the exact commit you download.
