# v1.8.7 release verification — 2026-11-08

- 21 existing isolated regression checks passed.
- Settings screen exercised in Korean and English with mocked actions: three buttons, equal 44 px height, correct create/open/uninstall handlers.
- Isolated Inno installation with a separate product ID preserved the exact maintenance installer. Its uninstaller removed the maintenance file, runtime, and test install directory.
- Direct hidden UI startup failed to show a window in one attempt. In an isolated launcher run, the update restart helper detected the first hidden startup, cleaned it up, and displayed a window on its second attempt. This is a mitigation, not a verified root cause.
- QA launcher used a separate mutex and data directory. Cleanup left zero matching QA processes. A two-second sample immediately after startup used 0.266 CPU seconds and 54.2 MiB working set, not a steady-state benchmark.
- Actual installed v1.8.6 to v1.8.7 update, interactive uninstallation, different machines, and interrupted installation remain unverified.
