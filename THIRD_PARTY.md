# Third-party components

The repository contains no third-party runtime binaries. During preparation, the installer downloads the exact upstream archives listed in `dependencies.json`, verifies SHA-256 hashes, and extracts selected runtime files locally. This project's MIT license applies only to its original source and documentation.

| Component | Source and purpose | License notes |
| --- | --- | --- |
| Wine Sikarugir 11.0 revision 1 | [Sikarugir engine releases](https://github.com/Sikarugir-App/Engines/releases/tag/v1.0), Windows compatibility runtime. [Downstream source repository](https://github.com/Sikarugir-App/wine). | [Wine 11.0 is LGPL-2.1-or-later](https://github.com/wine-mirror/wine/blob/wine-11.0/LICENSE). Source and downstream provenance must be verified for any future redistribution of these binaries. |
| DXMT v0.80-244-g7c8dee1 | Selected DXMT runtime from [Template 1.0.18](https://github.com/Sikarugir-App/Template/releases/tag/v1.0), translates Direct3D to Metal. The reported version points to [upstream commit 7c8dee1](https://github.com/3Shain/dxmt/tree/7c8dee1c2d73415301ceb7d1fa810861cef4cd67). | The installed license identifies Copyright (c) 2023-2026 Feifan He for CodeWeavers, [LGPL-2.1-or-later](https://github.com/3Shain/dxmt/blob/7c8dee1c2d73415301ceb7d1fa810861cef4cd67/LICENSE). |
| Dependency libraries and GStreamer | Selected Frameworks files from the same Template archive | A collection of separately licensed libraries, not a uniformly LGPL bundle. GStreamer plugins and external libraries can carry other licenses, including GPL. See the [GStreamer licensing FAQ](https://gstreamer.freedesktop.org/documentation/frequently-asked-questions/licensing.html). They are not covered by our MIT license. |
| Windows Steam installer | [Valve's official installer](https://cdn.akamai.steamstatic.com/client/installer/SteamSetup.exe) | Proprietary. Downloaded from Valve, not included in the repository. The user completes installation and sign-in. |
| Outer Wilds | Downloaded separately through the user's Steam account | Proprietary. Ownership is required. No game code, assets, artwork, or saves are distributed here. |

The Template download also contains components this project does not install, including the Sikarugir launcher/SDK and Apple's D3DMetal renderer. Extraction selects top-level dependency dylibs, GStreamer, and DXMT only. No D3DMetal files are selected.

The pinned engine expects `SikarugirAppWine11=1`, and its DXMT build uses `WINEDLLPATH_DXMT`. Those integration settings reproduce the tested installation. They do not transfer ownership or change upstream licensing.

This is a source-only release. Before adding bundled binaries, audit the exact artifacts, their notices, corresponding source availability, and each license's redistribution obligations. A link to a binary archive is not a substitute for the corresponding source where a license requires it.

Exact source/build correspondence for the Sikarugir engine, its repacked GStreamer framework, and custom dependency dylibs has not been established here. The public Wine source repository is a provenance pointer, not a claim that this project can reproduce the pinned engine. Runtime downloads remain opaque upstream artifacts verified by their archive hashes. The GitHub release tag is mutable and availability is not guaranteed. The installer rejects changed bytes rather than accepting a replacement automatically.
