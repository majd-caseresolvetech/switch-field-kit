# Offline maps

Maps are optional. They are downloaded from Protomaps, which builds vector maps from OpenStreetMap and other credited data. The viewer, symbols and fonts are saved locally as well as the map tiles.

## Simple setup

In the reader, open **MAPS**, choose a named area and use **COPY COMMAND**. Paste it into Ubuntu Terminal. After it finishes, select **REFRESH LIBRARY**. Once a map is installed, **Add another area** offers the same choices.

```bash
~/.local/bin/fieldkit map-tools
~/.local/bin/fieldkit download-map lebanon
```

The second command finds a recent daily build, calculates the size, checks disk space and asks before downloading map tiles. It uses two download threads. An interrupted extraction is retried from the beginning. An existing finished map is kept until its replacement passes verification.

| Preset | Saved detail |
| --- | --- |
| `world` | World overview, maximum source zoom 6 |
| `uk` | UK bounding box, roads and places, zoom 13 |
| `lebanon` | Lebanon bounding box, roads and places, zoom 14 |
| `prague` | Prague city area, street/path detail, zoom 15 |
| `europe-levant` | Broad Europe-to-Levant overview, zoom 10 |

These are rectangular coverage areas, not exact national borders. File sizes change between builds. The European overview is not detailed walking coverage between every town.

To calculate a size without fetching the map tiles:

```bash
~/.local/bin/fieldkit download-map uk --plan
```

This still fetches the small archive directory needed to estimate the selected region and installs the extraction tool if absent. To select a particular available daily build, add `--date YYYYMMDD`, replacing that value with a date listed at [Protomaps builds](https://maps.protomaps.com/builds). Old builds can expire. The script checks recent dates and explains if none can be found.

The optional `--yes` flag accepts the calculated map download without a prompt. Use it only when you have chosen the region and space budget.

## Bring an existing map

```bash
~/.local/bin/fieldkit map-tools
~/.local/bin/fieldkit add-map "/path/to/my-map.pmtiles" --name "My area"
```

The app registers the file in place. It does not make another copy. Keep the storage mounted and do not rename the file afterwards.

This version accepts **PMTiles v3 containers with Protomaps v4 vector layers**. A `.pmtiles` filename alone does not guarantee compatibility. Raster, other vector schemas and arbitrary MBTiles files are not supported by this viewer.

For a custom area, use the upstream [PMTiles extraction tool](https://docs.protomaps.com/pmtiles/cli) to make a bounding-box or GeoJSON-region extract, then register it. [Protomaps’ getting-started guide](https://docs.protomaps.com/guide/getting-started) explains that workflow. The private prototype’s hand-selected walking bands are not shipped as a verified walking route.

## Read the map correctly

Select a saved area. Use + / − or touch gestures to zoom. The status line shows the source snapshot and the centre coordinates. Enter decimal **latitude, longitude** to jump to a point, for example `50.0755, 14.4378`.

The Switch does not supply a live GPS location. There is no offline route engine, address search, live border information or terrain/contour guarantee. A drawn line is not proof that a path exists, is public or is safe to travel. Zooming beyond an archive’s saved detail enlarges the same information.

The attribution stays visible. [OpenStreetMap’s ODbL and attribution requirements](https://www.openstreetmap.org/copyright) still apply if you redistribute an extract. Project code being MIT licensed does not change the data licence.
