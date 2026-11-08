# Software, publications and map data have separate licences

The MIT licence applies to this project's original application code, navigation metadata and project documentation. It does not relicense any publisher’s PDF or upstream software.

## Original publications

`catalogues/guides.json` contains publisher URLs, authorship, edition dates, SHA-256 hashes, page counts and our section labels. The repository and release contain **no PDF books or rendered publisher pages**.

When the user chooses a guide download, their device fetches that original directly from the publisher over HTTPS. Its original wording, illustrations and credits are retained in the local PDF. The app creates display images locally for reading. Publisher terms govern those files. A public download link is not a claim that the publication is open source or that anyone may redistribute it under MIT.

Sources include Scouts UK, the American University of Beirut Nature Conservation Center, IFRC, WHO/WEDC, HSE, Ordnance Survey, Plantlife and the British Naturalists Association. Their individual download URLs and source pages are in the [content catalogue](docs/CONTENT.md). Review the source’s own terms before sharing a downloaded pack.

No commercial foraging book is bundled or downloaded from an unofficial mirror. The current identification references do not close the comprehensive-foraging gap.

## Optional downloaded software

| Component | Licence / source |
| --- | --- |
| Kiwix tools 3.8.2 | GPL-3.0-or-later, [upstream source and releases](https://github.com/kiwix/kiwix-tools/releases/tag/3.8.2) |
| go-pmtiles 1.31.2 | BSD-3-Clause, [upstream](https://github.com/protomaps/go-pmtiles/releases/tag/v1.31.2) |
| MapLibre GL JS 6.16.0 | BSD-3-Clause, [upstream](https://github.com/maplibre/maplibre-gl-js) |
| pmtiles JS 4.5.0 | BSD-3-Clause, [upstream](https://github.com/protomaps/PMTiles) |
| @protomaps/basemaps 5.7.2 | BSD-3-Clause, [upstream](https://github.com/protomaps/basemaps) |
| Basemap fonts and sprites | Individual upstream font/artwork terms, [basemap-assets](https://github.com/protomaps/basemaps-assets). The pinned commit and checksum are in `catalogues/tools.json`. Available licence files are retained during installation. |
| Poppler utilities | Provided by the user's Ubuntu package manager. See the installed package copyright and [upstream](https://poppler.freedesktop.org/). |

These binaries and bundles are fetched separately. They are not committed into the repository. Pinned download hashes establish which bytes were checked, not a warranty that upstream software has no vulnerabilities.

Kiwix runs as a separate local process. The app communicates with it over localhost HTTP. Users can replace it with a compatible upstream build in their configuration.

## Maps and Wikipedia

OpenStreetMap data is under the [Open Database Licence](https://www.openstreetmap.org/copyright), with attribution requirements. Other credited Protomaps inputs retain their terms. Keep map attribution when sharing extracts.

ZIM books retain the licensing and credits embedded in each archive. Wikipedia text and individual media can have different licences. Registering a ZIM does not grant new redistribution rights.

## Names

Nintendo Switch identifies the hardware this independent project was built around. Nintendo, Switchroot, Kiwix, the publishers and mapping projects do not sponsor or endorse this repository. No Nintendo firmware, game content, console keys, logos or Fallout artwork are included.
