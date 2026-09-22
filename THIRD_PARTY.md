# Third-party components

The installer downloads the archives pinned in [dependencies.json](dependencies.json). This repository includes no runtime binaries. Its MIT license covers only the original scripts and documentation.

| Component | Source | License |
| --- | --- | --- |
| Wine Sikarugir 11.0 revision 1 | [Engine releases](https://github.com/Sikarugir-App/Engines/releases/tag/v1.0), [downstream source](https://github.com/Sikarugir-App/wine) | Upstream Wine is [LGPL-2.1-or-later](https://github.com/wine-mirror/wine/blob/wine-11.0/LICENSE). |
| DXMT v0.80-244-g7c8dee1 | [Template archive](https://github.com/Sikarugir-App/Template/releases/tag/v1.0), [upstream commit](https://github.com/3Shain/dxmt/tree/7c8dee1c2d73415301ceb7d1fa810861cef4cd67) | [LGPL-2.1-or-later](https://github.com/3Shain/dxmt/blob/7c8dee1c2d73415301ceb7d1fa810861cef4cd67/LICENSE). Copyright (c) 2023-2026 Feifan He for CodeWeavers. |
| GStreamer and dependency libraries | Frameworks files from the Template archive | Separately licensed. Plugins and external libraries may use GPL or other licenses. See [GStreamer's licensing FAQ](https://gstreamer.freedesktop.org/documentation/frequently-asked-questions/licensing.html). |
| Windows Steam | [Valve's installer](https://cdn.akamai.steamstatic.com/client/installer/SteamSetup.exe) | Proprietary. Downloaded from Valve. |
| Outer Wilds | The user's Steam library | Proprietary. Game ownership is required. |

Extraction includes the Template archive's top-level dependency dylibs, GStreamer, and DXMT. It excludes the Sikarugir launcher/SDK and Apple's D3DMetal renderer.

Exact source/build correspondence for the Sikarugir engine and repacked dependencies has not been established. Before distributing those binaries, verify their corresponding source, notices, and redistribution requirements. The source links above do not establish that the pinned builds are reproducible.
