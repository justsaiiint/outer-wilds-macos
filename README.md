# Outer Wilds on macOS

Play the Windows Steam edition of Outer Wilds on an Apple Silicon Mac using Wine and DXMT. The launcher sets up borderless fullscreen and a 60 FPS target.

You need to own the game on Steam. Tested on an M4 Pro MacBook Pro with macOS 27.0. Support for other Macs is experimental.

## Requirements

- Apple Silicon Mac with Rosetta 2
- Python 3.9 or later
- A Steam account that owns Outer Wilds
- At least 20 GB of free disk space

## Install

Download this repository, open Terminal in its folder, and run:

```sh
python3 owmac.py prepare
python3 owmac.py install-steam
```

Complete the Windows Steam installer, sign in, and install Outer Wilds from your library. This creates a separate installation from native macOS Steam.

## Play

Open **Outer Wilds macOS.app** from your user Applications folder (`~/Applications`). You can drag it to the Dock for quick access.

Use this app to launch the game. Keep the game's Fullscreen checkbox off, as the launcher fills the display with borderless mode.

## Settings and help

Quit the game before changing settings. For example, to adjust the requested resolution:

```sh
python3 owmac.py settings --width 2560 --height 1600
```

For a status check or available commands:

```sh
python3 owmac.py doctor
python3 owmac.py --help
```

The installation, logs, and settings backups are in `~/Library/Application Support/Outer Wilds macOS`. Saves are under `prefix/drive_c/users/<user>/AppData/LocalLow/Mobius Digital/Outer Wilds/SteamSaves` inside that folder.

To uninstall, quit the game and its Windows Steam, back up your saves, then move the app and installation folder to Trash.

## Credits

Built on Wine, DXMT, and Sikarugir's runtime builds. [MIT license](LICENSE) for this project's code. Dependencies retain their [own licenses](THIRD_PARTY.md). Game files and runtime binaries are downloaded separately.

Unofficial project, not affiliated with the game's creators or Valve. See [development notes](DEVELOPMENT.md) to contribute.
