# 1.8.2 validation (2026-11-08)
14 isolated regression checks passed, including reminder persistence, popup reopening, language navigation rebuild and download cancellation/hash verification. Cached tabs: 300 hidden Tk switches approximately 40 ms, not a visual FPS test.
Packaged TLS initialization failure found during the actual 1.8.0 trial. Bundling the build distribution certificate resource fixes the missing file; certificate verification remains enabled. Native trial popup observed.
No resident updater/service or periodic polling: check once per launch, worker exits afterward. Popup artwork is rendered once per opening, without animation.
Other PCs and power-loss recovery remain untested. Local in-place installation succeeded (installer log: Installation process succeeded). Installed UI matches the release package.
