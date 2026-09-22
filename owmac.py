#!/usr/bin/env python3
"""An isolated, source-only Outer Wilds launcher for Apple Silicon Macs."""

import argparse
import contextlib
import datetime
import getpass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import plistlib
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request


VERSION = "0.1.0"
DEFAULT_ROOT = Path.home() / "Library/Application Support/Outer Wilds macOS"
DEFAULT_APP = Path.home() / "Applications/Outer Wilds macOS.app"
MARKER = "outer-wilds-macos.json"
STEAM = r"C:\Program Files (x86)\Steam\Steam.exe"
APP_ID = "753640"


def atomic_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".owmac-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as output:
            output.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path, data):
    atomic_write(path, json.dumps(data, indent=2) + "\n")


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def download(entry, cache):
    cache.mkdir(parents=True, exist_ok=True)
    destination = cache / entry["filename"]
    if destination.exists():
        if digest(destination) != entry["sha256"]:
            raise RuntimeError(f"Checksum mismatch: {destination}. Move it aside and retry.")
        return destination
    fd, partial = tempfile.mkstemp(prefix=destination.name + ".", dir=cache)
    try:
        print(f"Downloading {entry['filename']}...", flush=True)
        request = urllib.request.Request(entry["url"], headers={"User-Agent": "outer-wilds-macos/" + VERSION})
        with os.fdopen(fd, "wb") as output, urllib.request.urlopen(request, timeout=60) as response:
            if not response.url.startswith("https://"):
                raise RuntimeError("Refusing a non-HTTPS redirect")
            shutil.copyfileobj(response, output)
        if digest(partial) != entry["sha256"]:
            raise RuntimeError("Download checksum changed. Nothing will run. Review the upstream release before updating the manifest.")
        os.replace(partial, destination)
    finally:
        if os.path.exists(partial):
            os.unlink(partial)
    return destination


def inside(path, root):
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def extract_selected(archive, destination, select):
    """Extract only mapped members, refusing traversal, special files, and hard links."""
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:xz") as bundle:
        for member in bundle:
            relative = select(member.name)
            if relative is None:
                continue
            relative = PurePosixPath(relative)
            if relative.is_absolute() or ".." in relative.parts:
                raise RuntimeError("Unsafe archive path")
            target = destination / str(relative)
            if not inside(target, destination):
                raise RuntimeError("Archive path escapes destination")
            target.parent.mkdir(parents=True, exist_ok=True)
            if member.isdir():
                target.mkdir(exist_ok=True)
            elif member.issym():
                link = Path(member.linkname)
                if link.is_absolute() or not inside(target.parent / link, destination):
                    raise RuntimeError("Unsafe archive symlink")
                target.symlink_to(member.linkname)
            elif member.isfile():
                if target.is_symlink():
                    raise RuntimeError("Refusing to write through a symlink")
                with bundle.extractfile(member) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
                target.chmod(member.mode & 0o777)
            else:
                raise RuntimeError("Unsupported archive member type")


def wine_member(name):
    prefix = "wswine.bundle/"
    return "Wine.app/Contents/" + name[len(prefix):] if name.startswith(prefix) else None


def template_member(name):
    prefix = "Template-1.0.18.app/Contents/Frameworks/"
    if not name.startswith(prefix):
        return None
    relative = name[len(prefix):]
    if relative.startswith("renderer/dxmt/"):
        return "dxmt/" + relative[len("renderer/dxmt/"):]
    if relative == "GStreamer.framework" or relative.startswith("GStreamer.framework/"):
        return "Frameworks/" + relative
    if "/" not in relative and relative.endswith(".dylib"):
        return "Frameworks/" + relative
    return None


def wine_env(root):
    contents = root / "runtime/Wine.app/Contents"
    frameworks = root / "runtime/Frameworks"
    env = os.environ.copy()
    # A caller's Wine/DXMT overrides must not select another prefix or renderer.
    for key in list(env):
        if key.startswith(("WINE", "DXMT_", "DXVK_", "GST_", "DYLD_")):
            del env[key]
    env.update({
        "WINEPREFIX": str(root / "prefix"),
        "WINELOADER": str(contents / "bin/wine"),
        "WINESERVER": str(contents / "bin/wineserver"),
        "SikarugirAppWine11": "1",
        "WINEDLLPATH_DXMT": str(root / "runtime/dxmt/wine"),
        "WINEDLLPATH_PREPEND": str(root / "runtime/dxmt/wine"),
        "WINEDLLOVERRIDES": "winemenubuilder.exe=d",
        "WINEDEBUG": "-all",
        "DYLD_FALLBACK_LIBRARY_PATH": f"{frameworks}:{frameworks}/GStreamer.framework/Versions/1.0/lib:/usr/lib",
        "GST_PLUGIN_SYSTEM_PATH_1_0": f"{frameworks}/GStreamer.framework/Versions/1.0/lib/gstreamer-1.0",
        "GST_PLUGIN_SCANNER_1_0": f"{frameworks}/GStreamer.framework/Versions/1.0/libexec/gstreamer-1.0/gst-plugin-scanner",
        "GST_REGISTRY": str(root / "prefix/gstreamer-registry.bin"),
        "DXMT_CONFIG_FILE": "Z:" + str(root / "dxmt.conf"),
        "DXMT_LOG_PATH": "Z:" + str(root / "logs"),
        "PATH": str(contents / "bin") + ":" + env.get("PATH", "/usr/bin:/bin"),
    })
    return env


def wine(root, args, wait=True, timeout=120):
    env = wine_env(root)
    with (root / "logs/runtime.log").open("ab") as log:
        command = [env["WINELOADER"], *args]
        if wait:
            return subprocess.run(command, env=env, stdout=log, stderr=log, check=True, timeout=timeout)
        return subprocess.Popen(command, env=env, stdout=log, stderr=log, start_new_session=True)


def game_running():
    result = subprocess.run(["/usr/bin/pgrep", "-f", r"[O]uterWilds\.exe"], capture_output=True)
    if result.returncode not in (0, 1):
        raise RuntimeError("Could not check whether the game is running")
    return result.returncode == 0


def require_game_closed():
    if game_running():
        raise RuntimeError("Outer Wilds is already running. Quit through its menu before changing settings or launching another copy.")


def require_install(root):
    marker = root / MARKER
    if not marker.is_file() or json.loads(marker.read_text()).get("project") != "outer-wilds-macos":
        raise RuntimeError("This directory is not an outer-wilds-macos installation")
    return json.loads(marker.read_text())


@contextlib.contextmanager
def locked(root):
    import fcntl
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".settings.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Another installer or launcher operation is in progress")
        yield


def backup(root, path):
    if path.is_file():
        if not inside(path, root) or not inside(root / "backups", root):
            raise RuntimeError("Refusing a backup outside the installation")
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        destination = root / "backups" / stamp / path.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)


def replace_setting(text, key, value):
    pattern = re.compile(r"^\s*" + re.escape(key) + r"\s*=.*$", re.MULTILINE)
    replacement = f"{key}={value}"
    if pattern.search(text):
        return pattern.sub(replacement, text)
    return text.rstrip() + "\n" + replacement + "\n"


def configure(root, fps, width, height):
    require_game_closed()
    config = root / "dxmt.conf"
    if not inside(config, root) or not inside(root / "backups", root):
        raise RuntimeError("Settings paths must stay inside the installation")
    dxmt = f"d3d11.preferredMaxFrameRate = {fps}\ndxgi.handleAltTab = True\n"
    if not config.exists() or config.read_text() != dxmt:
        backup(root, config)
        atomic_write(config, dxmt)
    users = root / "prefix/drive_c/users"
    bases = list(users.glob("*/AppData/LocalLow/Mobius Digital/Outer Wilds"))
    if not bases:
        bases = [users / getpass.getuser() / "AppData/LocalLow/Mobius Digital/Outer Wilds"]
    for base in bases:
        if not inside(base, root / "prefix"):
            raise RuntimeError("Refusing to change settings outside the isolated prefix")
        secret = base / "secretsettings.txt"
        if not inside(secret, root / "prefix"):
            raise RuntimeError("Refusing a settings file outside the isolated prefix")
        text = secret.read_text() if secret.exists() else ""
        updated = replace_setting(replace_setting(text, "PhysicsRate", fps), "VSyncCount", 0)
        if updated != text:
            backup(root, secret)
            atomic_write(secret, updated)
        for graphic in (base / "SteamSaves").glob("*/graphics.owsett"):
            if not inside(graphic, root / "prefix"):
                raise RuntimeError("Refusing to follow a profile outside the isolated prefix")
            data = json.loads(graphic.read_text())
            updated_data = dict(data, fullScreen=False, displayResWidth=width, displayResHeight=height)
            if updated_data != data:
                backup(root, graphic)
                write_json(graphic, updated_data)


def default_resolution():
    try:
        result = subprocess.run(["/usr/sbin/system_profiler", "SPDisplaysDataType", "-json"], capture_output=True, text=True, check=True, timeout=20)
        for gpu in json.loads(result.stdout)["SPDisplaysDataType"]:
            for display in gpu.get("spdisplays_ndrvs", []):
                if display.get("spdisplays_main") == "spdisplays_yes":
                    match = re.search(r"(\d+)\s*x\s*(\d+)", display.get("spdisplays_pixelresolution", ""))
                    if match:
                        return tuple(map(int, match.groups()))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        pass
    raise RuntimeError("Could not detect the main display. Supply --width and --height.")


def create_app(root, app):
    if app.exists():
        raise RuntimeError(f"Refusing to replace an existing app: {app}")
    contents = app / "Contents"
    (contents / "MacOS").mkdir(parents=True)
    info = {"CFBundleExecutable": "Launch", "CFBundleIdentifier": "io.github.outer-wilds-macos.launcher",
            "CFBundleName": "Outer Wilds macOS", "CFBundleDisplayName": "Outer Wilds macOS",
            "CFBundlePackageType": "APPL", "CFBundleVersion": VERSION,
            "CFBundleShortVersionString": VERSION, "NSHighResolutionCapable": True}
    (contents / "Info.plist").write_bytes(plistlib.dumps(info))
    launcher = contents / "MacOS/Launch"
    command = [str(root / "launcher/owmac.py"), "launch", "--root", str(root)]
    candidates = list(dict.fromkeys([sys.executable, "/opt/homebrew/bin/python3", "/usr/local/bin/python3", "/usr/bin/python3"]))
    script = "#!/bin/bash\nset -euo pipefail\nexec >> " + shlex.quote(str(root / "logs/launcher.log")) + " 2>&1\n"
    script += "for candidate in " + shlex.join(candidates) + "; do\n"
    script += '  if [[ -x "$candidate" ]] && "$candidate" -c "import sys; sys.exit(sys.version_info < (3, 9))"; then\n'
    script += '    exec "$candidate" ' + shlex.join(command) + "\n  fi\ndone\n"
    script += "echo 'Python 3.9 or later is required. Restore Python, then open this app again.' >&2\nexit 1\n"
    launcher.write_text(script)
    launcher.chmod(0o755)


def check_host():
    if platform.system() != "Darwin":
        raise RuntimeError("This installer requires macOS")
    arm = subprocess.run(["/usr/sbin/sysctl", "-n", "hw.optional.arm64"], capture_output=True, text=True)
    if arm.stdout.strip() != "1":
        raise RuntimeError("This release targets Apple Silicon Macs only")
    if subprocess.run(["/usr/bin/arch", "-x86_64", "/usr/bin/true"], capture_output=True).returncode:
        raise RuntimeError("Rosetta 2 is required. Install it through Apple's prompt, then retry.")


def prepare(args):
    check_host()
    require_game_closed()
    root = args.root
    if root.exists():
        raise RuntimeError(f"Refusing to install over an existing directory: {root}. Choose a new --root.")
    app = args.app
    if app.exists():
        raise RuntimeError(f"Refusing to replace {app}. Choose a new --app.")
    if bool(args.width) != bool(args.height):
        raise RuntimeError("Supply both --width and --height")
    width, height = (args.width, args.height) if args.width else default_resolution()
    manifest = json.loads(Path(__file__).with_name("dependencies.json").read_text())
    # Download and verify every input before creating the installation.
    files = {key: download(value, args.cache) for key, value in manifest.items()}
    with locked(root):
        for name in ["logs", "backups", "downloads", "launcher"]:
            (root / name).mkdir(exist_ok=True)
        print("Extracting the pinned runtime...", flush=True)
        extract_selected(files["wine"], root / "runtime", wine_member)
        extract_selected(files["template"], root / "runtime", template_member)
        contents = root / "runtime/Wine.app/Contents"
        (contents / "MacOS").mkdir(exist_ok=True)
        (contents / "MacOS/wine").symlink_to("../bin/wine")
        info = {"CFBundleExecutable": "wine", "CFBundleIdentifier": "org.winehq.wine",
                "CFBundleName": "Outer Wilds Runtime", "CFBundleDisplayName": "Outer Wilds Runtime",
                "CFBundlePackageType": "APPL", "CFBundleVersion": "11.0.1",
                "CFBundleShortVersionString": "11.0.1", "NSHighResolutionCapable": True,
                "NSPrincipalClass": "NSApplication"}
        (contents / "Info.plist").write_bytes(plistlib.dumps(info))
        shutil.copy2(files["steam"], root / "downloads/SteamSetup.exe")
        shutil.copy2(Path(__file__), root / "launcher/owmac.py")
        shutil.copy2(Path(__file__).with_name("dependencies.json"), root / "launcher/dependencies.json")
        print("Creating an isolated Windows environment...", flush=True)
        wine(root, ["wineboot", "--init"])
        overrides = root / "overrides.reg"
        overrides.write_text('REGEDIT4\n\n[HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\OuterWilds.exe\\DllOverrides]\n"d3d10core"="builtin"\n"d3d11"="builtin"\n"dxgi"="builtin"\n"winemetal"="builtin"\n"gameoverlayrenderer64"=""\n')
        wine(root, ["regedit", "/S", str(overrides)])
        configure(root, 60, width, height)
        write_json(root / MARKER, {"project": "outer-wilds-macos", "version": VERSION,
                   "fps": 60, "width": width, "height": height, "app": str(app), "dependencies": manifest})
        create_app(root, app)
    print(f"Prepared: {root}\nLauncher: {app}\nNext: python3 owmac.py install-steam --root {shlex.quote(str(root))}")


def main(argv=None):
    if sys.version_info < (3, 9):
        raise RuntimeError("Python 3.9 or later is required")
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ["prepare", "install-steam", "steam", "launch", "settings", "doctor"]:
        item = sub.add_parser(command)
        item.add_argument("--root", type=lambda p: Path(p).expanduser().resolve(), default=DEFAULT_ROOT)
        if command == "prepare":
            item.add_argument("--cache", type=lambda p: Path(p).expanduser().resolve(), default=Path.home() / "Library/Caches/outer-wilds-macos")
            item.add_argument("--app", type=lambda p: Path(p).expanduser().resolve(), default=DEFAULT_APP)
        if command in ("prepare", "settings"):
            item.add_argument("--width", type=int)
            item.add_argument("--height", type=int)
        if command == "settings":
            item.add_argument("--fps", type=int, choices=[60, 120])
    args = parser.parse_args(argv)
    if args.command in ("prepare", "settings"):
        if any(value is not None and not 640 <= value <= 16384 for value in (args.width, args.height)):
            parser.error("Display dimensions must be between 640 and 16384")
    if args.command == "prepare":
        prepare(args)
        return
    root = args.root
    config = require_install(root)
    if not inside(root / "logs", root):
        raise RuntimeError("Log files must stay inside the installation")
    if args.command == "doctor":
        print(json.dumps({"version": config["version"], "fps_target": config["fps"],
                         "resolution_request": [config["width"], config["height"]],
                         "game_running": game_running(),
                         "steam_installed": (root / "prefix/drive_c/Program Files (x86)/Steam/Steam.exe").is_file(),
                         "dxmt_installed": (root / "runtime/dxmt/wine/x86_64-windows/d3d11.dll").is_file()}, indent=2))
        return
    with locked(root):
        require_game_closed()
        if args.command == "settings":
            if bool(args.width) != bool(args.height):
                parser.error("Supply both --width and --height")
            config["fps"] = args.fps or config["fps"]
            config["width"] = args.width or config["width"]
            config["height"] = args.height or config["height"]
            configure(root, config["fps"], config["width"], config["height"])
            write_json(root / MARKER, config)
            print("Settings saved. They apply at the next launch.")
        elif args.command == "install-steam":
            if (root / "prefix/drive_c/Program Files (x86)/Steam/Steam.exe").exists():
                raise RuntimeError("Steam is already installed. Use the steam command.")
            wine(root, [str(root / "downloads/SteamSetup.exe")], wait=False)
            print("Steam's installer is open. Complete it, then sign in yourself.")
        else:
            if not (root / "prefix/drive_c/Program Files (x86)/Steam/Steam.exe").is_file():
                raise RuntimeError("Install Windows Steam first with install-steam")
            flags = [STEAM, "-no-cef-sandbox", "-cef-disable-gpu"]
            if args.command == "launch":
                configure(root, config["fps"], config["width"], config["height"])
                flags += ["-applaunch", APP_ID, "-popupwindow", "-screen-width", str(config["width"]),
                          "-screen-height", str(config["height"]), "-screen-fullscreen", "0"]
            wine(root, flags, wait=False)
            print("Launch request sent to Windows Steam.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, subprocess.SubprocessError, tarfile.TarError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
