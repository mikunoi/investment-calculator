# 1.8.3 — 2026-11-08
- Repaint the rounded update card only when its size changes; coalesce resize events. Fix background sizing when download progress expands.
- Reset progress before retry and cancel pending drawing callbacks when closing.
- Atomically replace each data backup file and include the seven-day reminder preference.
- Full regression and packaged checks required before publication; no trading changes.

# 1.8.2 — 2026-11-08
- Redesigned update dialog with rounded card/buttons, version pill, clean notes, app icon and progress visible only during download.
- Added persistent seven-day reminder suppression and a top-right Update button after deferral; manual reopening works during suppression.
- Fixed packaged HTTPS initialization: include the public certificate resource required by the build Python distribution. TLS verification remains enabled.
- 1.8.1 startup update checks silently failed in the frozen executable; install 1.8.2 manually once if using that build.

# Changelog / 변경 이력

## 1.8.0
- Renamed to mikunoi_Stock_Calculator / 앱 표시 이름 변경
- Korean / US English UI, persisted across restarts / 언어 저장
- Fractional shares up to 8 decimal places / 국내·해외 소수점 수량
- Exact quantity strings in storage and spreadsheet export / 수량 정밀도 보존
- Bilingual import formats, installer and documentation / 한영 양식·설치 안내
- Ten isolated regression checks pass / 격리 회귀검사 10개 통과

## 1.7.0
- Dark / Light / Matrix theme persistence
- Initial MIT GitHub release


## 1.8.1
Startup-only update notification with app icon and release notes. Verified installer download and data-preserving in-place update mode. Interrupted downloads leave the installed application unchanged. Power loss during installation may require rerunning setup. 13 isolated regression tests passed, including download integrity and cancellation. Power-loss recovery is not verified.
