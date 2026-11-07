# 1.8.6 — 2026-11-08
- 업데이트 설치기가 종료된 뒤 이전 계산기를 정리하고 재시작합니다. 창이 나타나지 않으면 한 번 재시도하며 실패한 프로세스를 정리합니다.
- 중복 실행 시 미저장 정보 손실 안내와 승인을 받고 기존 계산기를 종료합니다. 취소하면 기존 창을 유지합니다.
- 업데이트 팝업 둥근 테두리의 분홍색 잔상을 제거했습니다.
- Wait for the installer to exit before restarting. Retry once if no window appears, then clean up failed processes.
- Ask for confirmation before replacing a running calculator; cancelling keeps the current instance.
- Remove magenta fringes around the rounded update dialog.
- Verification: 21 regression checks passed. Physical display changes and power-loss recovery are not covered.

# 1.8.5 — 2026-11-08
- Build the root window before first display to reduce startup mapping races.
- Reset the frozen-runtime environment in the Rust launcher; sanitize DLL search paths and Python/Tcl variables when starting the external updater.
- Fit each popup to its own monitor and clamp tiny/negative-origin work areas safely.
- Reduce monitor polling while minimized; unchanged work areas do not trigger geometry changes.
- Preserve all v1.8.4 features. This release does not alter trading services or personal portfolios.

# 1.8.4 — 2026-11-08
- Consolidate local startup, window placement, single-instance and update-popup fixes.
- Rust uses ShellExecuteExW and waits for the UI process; no hidden console startup flags.
- Cancel delayed startup/scroll/monitor callbacks on teardown.
- Keep all fractional-share, FX, targets, bilingual UI/export and data-preservation features.

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

## 2026-11-08 Local 1.8.5 update restart fix (not published)
- Update setup stops only calculator processes whose full executable paths match the validated installation, before replacing files.
- After setup exits, a separate short-lived helper closes remaining calculator processes, releases the single-instance owner, and starts the calculator once.
- The helper is not a resident/background service. Saved assets, goals and preferences are not deleted.
- Local display version remains 1.8.5. GitHub v1.8.5 has not been replaced. Build and installed restart verification pending.
