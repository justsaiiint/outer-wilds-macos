# Development

Run the tests:

```sh
python3 -m unittest discover -s tests -v
```

For a separate installation, pass `--root` and `--app` to `prepare`. Use the same `--root` for subsequent commands. `--cache` accepts previously downloaded archives, which are still checked against `dependencies.json`.

The runtime was tested in gameplay on an M4 Pro with macOS 27.0. Fresh preparation and the automated tests passed on that machine. Steam sign-in, download, and gameplay have not been repeated through the packaged installer from start to finish.

Bug reports should include the Mac chip, macOS version, game version, and steps to reproduce. Review logs for personal information before sharing them.

## Runtime details

The engine needs `SikarugirAppWine11=1` and `WINEDLLPATH_DXMT`. Steam runs with `-no-cef-sandbox` and `-cef-disable-gpu`. The first disables Steam's Chromium sandbox inside Wine.

The default rendering cap and physics rate are 60. `VSyncCount=0` leaves frame limiting to DXMT. The optional `settings --fps 120` mode is experimental. See [Mobius Digital's settings documentation](https://www.mobiusdigitalgames.com/supportforum.html).

Keep the dependency hashes pinned. Upstream URLs can change, including Valve's Steam installer. Review replacement files before updating the manifest.
