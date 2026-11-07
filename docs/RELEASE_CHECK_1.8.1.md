# 1.8.1 validation (2026-11-08)
13 isolated regression tests passed. No personal portfolio files used.
Coverage: fractional shares, FX, allocation funding, export image, bilingual UI, saved preferences/goals, original/target valuation and colors, release metadata validation, download SHA256/size validation and cancellation.
Optimization: startup check only; no recurring release checks, service, or scheduled task. Stream installer hashing; bounded downloads. Cached tabs retained (300 hidden Tk switches approximately 37 ms; not a visual FPS benchmark).
A full power-loss installation/recovery test and other-PC test have not been performed. Unsigned installer. Original 1.8.0 does not have an updater; a one-time manual install is needed.

Local in-place /APPUPDATE installation completed with exit 0. Saved portfolio/goals/settings hashes unchanged; installed UI hash matched package. Launcher now waits for the UI process; native window and child process observed after launch.
