# v1.8.9 release verification — 2026-11-08

- 21 existing isolated regression checks passed in 6.524 seconds.
- Korean and English Settings GitHub buttons were invoked with a mocked browser; both requested https://github.com/mikunoi/investment-calculator and used 44 px height. Actual browser launch is not covered by this check.
- A packaged UI using a QA-only launcher with a separate mutex and user-data directory displayed its window. After two seconds of stabilization a two-second sample showed 0 CPU seconds and 52 MiB working set; cleanup left zero QA calculator processes. This is a single-PC sample.
- The real installed version was not upgraded for this release. Actual installed upgrade, interactive GitHub button use, other PCs and power interruption remain unverified. Previously noted intermittent hidden startup remains a known limitation.
