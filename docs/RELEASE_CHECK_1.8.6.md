# v1.8.6 release verification — 2026-11-08
- 21 isolated regression checks passed (5.924 seconds).
- Rust release and PyInstaller UI/Inno installer builds completed.
- Isolated QA launcher uses a separate mutex name so it cannot affect the installed app.
- Restart helper observed the first hidden startup, stopped its processes, retried once and detected a visible window.
- Stop-only helper left zero matching QA processes.
- One 2-second idle sample: 0 CPU seconds, 52.1 MiB working set. Not a cross-PC guarantee.
- Installed v1.8.4 and user data were not replaced by this release work.
- Full installed v1.8.4-to-v1.8.6 upgrade, physical monitor changes and interrupted installation require further verification.
