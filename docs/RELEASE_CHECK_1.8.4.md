# 1.8.4 validation — 2026-11-08
18 isolated regression tests passed (8.109 seconds), including fractional shares, FX, withdrawal, targets, bilingual persistence, exports, update checks/digests/cancellation, topmost modeless popup and callback teardown.
The Rust launcher now pumps Windows messages while waiting for the shell-launched UI. Three consecutive packaged launch/close cycles passed. Duplicate launch displayed a notice and left one calculator UI. Package checks use isolated user data.
Known limits: physical monitor switching, other PCs and abrupt power loss remain untested. Popup bounds are clamped; full inner responsive layout is not promised. No signed executable certificate.
