# Release validation 1.8.5

- 21 isolated regression checks passed (8.219 s). Includes fractional shares, FX, withdrawals, goal funding, original/target legend, image export, language/preferences, five-goal history, updater payload validation, snooze/reopen, popup ownership and callback cleanup.
- Additional checks: tiny and negative-coordinate monitor bounds; initial window visibility; updater environment cleanup.
- 300 cached tab selections: 148.0 ms in a hidden Tk test (not an end-user rendering benchmark).
- Rapid Tk interpreter recreation can emit a ttk ThemeChanged teardown warning in the test harness; all assertions pass. Physical multi-monitor switching and power interruption remain unverified.
- Rust/PyInstaller/Inno builds passed. An isolated installation over the prior QA folder displayed normally; three additional launch/normal-close cycles passed with both UI and launcher exiting.
- Stable idle sample: 0 CPU seconds over 5 seconds, 57.7 MiB working set. This is one local sample, not a cross-PC performance guarantee.
- Actual user-driven update to 1.8.5 remains for the user to verify; the installed app is intentionally not replaced.
- Local installed version remains 1.8.4 at the user's request; no 1.8.5 installation to the real app folder.
- Runtime isolation guidance: https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html
