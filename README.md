# Outer Wilds on macOS

A small, experimental, unofficial installer and launcher for the Windows Steam edition of Outer Wilds on Apple Silicon Macs. It assembles a pinned Wine + DXMT runtime, uses borderless fullscreen, and defaults to a 60 FPS cap with 60 Hz physics.

You need to own Outer Wilds on Steam. This repository contains scripts and documentation only. Steam, game files, saves, account information, and runtime binaries are not included.

## What has been tested

The underlying setup was played on an M4 Pro MacBook Pro with 24 GB of memory, a 20-core GPU, and macOS 27.0. The player reported stable 60 FPS, working audio and controls, and immediate input recovery after repeated Cmd+Tab returns in borderless fullscreen.

That is one machine and a player-reported result, not a benchmark across the game or a promise for other Macs. The tested game was Steam build 20230391, version 1.1.16.1372. The desktop was scaled, so the 3024 × 1964 launch request should not be read as a verified internal rendering resolution.

The game's own Fullscreen mode lost focus after switching away or minimizing. Borderless mode avoids the tested failure during Cmd+Tab. Manually minimizing the borderless window and restoring it from the Dock has not been verified.

A 120 FPS configuration produced a reported 40-75 FPS on the test machine. It remains an experiment, not the default. See [validation](VALIDATION.md) for the installer checks and their limits.

## Requirements

- An Apple Silicon Mac with Rosetta 2 installed.
- Python 3.9 or later, available as `python3`. Apple's Command Line Tools or an existing Python installation can provide it.
- A Steam account that owns the Windows edition of Outer Wilds.
- Internet access and enough disk space for a separate Windows Steam installation and the game. Allow at least 20 GB free as working headroom.

Only macOS 27.0 has been tested with these exact binaries. Other macOS releases are unverified. The installer does not install Rosetta, change system security settings, or request administrator access.

## Install

Download this repository and open Terminal in its folder. Read `owmac.py` and `dependencies.json` before running them.

```sh
python3 owmac.py prepare
python3 owmac.py install-steam
```

The first command downloads and verifies the pinned upstream files, prepares a fresh Wine environment, and creates `~/Applications/Outer Wilds macOS.app`. The second opens Valve's Windows Steam installer. Complete it yourself, sign in, and install Outer Wilds from your library.

The installation lives in `~/Library/Application Support/Outer Wilds macOS`. It is separate from native macOS Steam. The installer refuses to overwrite an existing installation or app. If preparation fails, inspect `logs/runtime.log` in that new installation folder before retrying with a new path or moving the failed installation aside.

After Steam finishes installing the game, launch **Outer Wilds macOS.app**. You can also use:

```sh
python3 owmac.py launch
```

Use this launcher when starting the game. Steam's own Play button or a Steam-created desktop shortcut can omit the borderless options. Leave the game's Fullscreen checkbox off. The launcher supplies fullscreen coverage and restores that setting before each launch.

On a first launch, create or select your profile normally. If Steam Cloud restores different display settings during initial setup, quit the game normally and launch through this app again. The launcher will then adjust the restored graphics settings.

## Settings

Quit the game through its menu before changing these settings. The default keeps graphics-quality options as the game or your profile sets them. It changes display mode, requested resolution, the rendering cap, and physics rate.

```sh
# Default target
python3 owmac.py settings --fps 60

# Experimental, adds physics work and may run worse
python3 owmac.py settings --fps 120

# Override the requested display dimensions
python3 owmac.py settings --width 2560 --height 1600
```

The main display's native pixel dimensions are detected during preparation. Multi-monitor setups and display changes after installation are not validated. Supply `--width` and `--height` to `prepare` if automatic detection fails.

Game VSync is overridden to zero so DXMT supplies the frame cap. The [developer's high-refresh notes](https://www.mobiusdigitalgames.com/supportforum.html) explain `PhysicsRate`, `VSyncCount`, and `-popupwindow`.

## Troubleshooting and rollback

```sh
python3 owmac.py doctor
python3 owmac.py steam
```

`doctor` prints a small local status report without account identifiers or save contents. `steam` opens this installation's Windows Steam without starting the game. Runtime and launcher output is kept under the installation's `logs` directory. Logs can contain usernames and paths, so review them before sharing.

Windows Steam uses `-no-cef-sandbox` and `-cef-disable-gpu`, matching the tested recipe. The first disables the Steam client's Chromium sandbox inside Wine. These options do not change macOS security settings, and their individual necessity has not been tested.

Changed settings are copied into timestamped folders under `backups` before replacement. To undo a configuration change, quit normally, restore the matching settings files, and set the launcher's FPS/resolution values accordingly. Use `settings --fps 60` to leave the 120 FPS experiment. Do not restore an old save over current progress.

The launcher refuses to modify settings while any Outer Wilds process is running. If a launch appears to do nothing, check `logs/launcher.log` and whether another instance is still open.

Downloads fail closed if a checksum changes. Valve's Steam installer URL is mutable, so a future installer update may require a reviewed change to `dependencies.json`. Do not bypass the check.

For a separate test installation, supply `--root` and `--app` to `prepare`, and the same `--root` to later commands. `--cache` can point to already-downloaded archives, which are still verified.

## Saves and removal

Save data lives inside the installation at `prefix/drive_c/users/<Windows user>/AppData/LocalLow/Mobius Digital/Outer Wilds/SteamSaves`. Settings updates preserve gameplay save files. Local installation folders are separate, but signing into the same Steam account uses the same game's Steam Cloud data. If Steam reports a conflict, review the save timestamps before choosing a copy. Steam Cloud is not a substitute for your own backup.

To remove the installation, quit its game and Windows Steam normally, copy any saves you want to keep, then move its app and support folder to Trash. Native macOS Steam is separate.

## Credits and license

Our original scripts and documentation use the [MIT license](LICENSE). The compatibility work is provided by Wine, DXMT, and the Sikarugir engine and dependency builds. Their licenses remain separate. See [third-party notices](THIRD_PARTY.md).

Outer Wilds belongs to its respective creators and rights holders. This project is not affiliated with or endorsed by Mobius Digital, Annapurna Interactive, Valve, Wine, CodeWeavers, or Sikarugir.

## Development

```sh
python3 -m unittest discover -s tests -v
python3 owmac.py --help
```

Contributions should include the Mac chip, memory, macOS version, game version, requested resolution, and a clear description of what was tested. Distinguish menu FPS from gameplay and Cmd+Tab from manual Dock minimization. Never submit Steam credentials, account files, game binaries, or saves.
