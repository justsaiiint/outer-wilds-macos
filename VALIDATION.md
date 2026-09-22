# Validation

## Gameplay evidence

On one M4 Pro MacBook Pro, 24 GB memory, 20-core GPU, macOS 27.0:

- Player-reported stable 60 FPS after reverting the rendering cap and physics rate to 60.
- Audio, keyboard movement, and mouse look worked in an expedition.
- Borderless fullscreen recovered input on the first return after repeated Cmd+Tab switches.
- The game's own Fullscreen mode caused focus failures. It is deliberately disabled by the launcher.
- Manual minimization and restoration from the Dock in the final borderless mode is unverified.
- The 120 FPS experiment was reported at 40-75 FPS and is not the recommended profile.

These observations came from the original manually assembled setup using the same pinned components. They do not establish support for every Mac, every game location, DLC content, controller, or macOS version.

## Packaged installer

On the same Mac, the packaged `prepare` command completed in a fresh support folder with a separate app. The original playable installation was left untouched.

- All three cached downloads passed the manifest SHA-256 checks.
- Selected runtime files extracted successfully, including relative library symlinks.
- Wine initialized a new prefix, and the game-specific DLL overrides were verified in its registry.
- Wine, DXMT D3D11, and GnuTLS binaries matched the original working installation byte for byte.
- No D3DMetal or Sikarugir SDK files were extracted.
- Automatic display detection produced the expected 3024 × 1964 request.
- The generated app launcher passed shell syntax validation, and `doctor` reported the prepared runtime correctly.
- All 12 automated tests pass. They cover save and visual-setting preservation, settings backups, repeated application, refusal to edit during gameplay, settings-path escape rejection, archive traversal and symlink rejection, extraction selection, download checksum failure, isolation from inherited Wine environment overrides, and launcher fallback when its original Python executable disappears.

Windows Steam installation, sign-in, game download, and gameplay have not been repeated end to end inside this fresh prefix. The gameplay evidence above belongs to the original manual setup. No second-machine validation is claimed.

## Reproduction checklist

1. Run the tests with Python 3.9 or later.
2. Prepare a new root and app path, leaving the original installation untouched.
3. Verify the pinned hashes, extraction scope, Wine startup, and game-specific DLL overrides.
4. Install Windows Steam, sign in yourself, and download the purchased game.
5. Launch through the generated app, confirm borderless coverage, and play an expedition.
6. Check frame pacing and first-return controls after several Cmd+Tab cycles.
7. Separately test manual minimization and restoration from the Dock.

Report skipped steps explicitly. A successful installer or menu launch is not a gameplay result.
