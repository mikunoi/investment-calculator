# v1.8.9 — 2026-11-08

- 설정에 GitHub 개발 페이지 버튼을 추가했습니다. 기본 브라우저에서 투자계산기 저장소를 엽니다.
- 한글과 US 언어를 지원하며, 버튼을 열 수 없는 경우 안내합니다.

## English

- Added a GitHub project page button to Settings. It opens the calculator repository in the default browser.
- Supports Korean and English and reports if a browser cannot be opened.

# v1.8.8 — 2026-11-08

- 업데이트 후 계산기 프로세스를 이름과 설치 경로로 빠르게 확인합니다.
- 첫 창이 나타나지 않으면 1.3초 후 재시도하고, 두 번째 실행이 느린 경우 곧바로 종료하지 않습니다.
- 이 PC의 격리 시험에서 설치 종료 후 창 표시까지 약 1.2초, 강제 재시도는 약 2.25초였습니다. 다른 환경에서는 시간이 달라질 수 있습니다.

## English

- Checks only calculator processes at the installed paths after an update.
- Retries after 1.3 seconds if the first window is missing, while allowing more time for a slower second launch.
- On this PC, an isolated update showed its window about 1.2 seconds after setup exited; a forced retry took about 2.25 seconds. Other environments can take longer.

# v1.8.7 — 2026-11-08

- 설정 탭에서 바탕화면 바로가기를 만들고 설치 폴더를 열 수 있습니다.
- 설치제거 버튼은 계산기를 닫고 설치파일의 설치·제거 선택 화면을 엽니다. 설정 버튼의 높이를 통일했습니다.
- 설정 기능과 최신 코드가 내장 소스 저장 자료에 포함됩니다.

## English

- The Settings tab can create a desktop shortcut and open the installation folder.
- The Uninstall button closes the calculator and opens the install/remove selection screen. Settings buttons share the same height.
- Source export includes the current settings features and code.

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

