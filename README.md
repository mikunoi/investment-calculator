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

# mikunoi_Stock_Calculator

**mikunoi**의 Windows 오프라인 주식 계산기 · MIT License

## 다운로드
[최신 버전 다운로드](https://github.com/mikunoi/investment-calculator/releases/latest)

Assets에서 **mikunoi_Stock_Calculator-Setup-1.8.5-x64.exe**를 받아 실행하세요.
Windows 10/11 x64 · Rust/Python 별도 설치 불필요 · 설치파일은 코드 서명되지 않았습니다.

## 기능
- 평단관리: 정수 및 소수점 수량으로 추가 매수 후 평균단가 계산
- 비중계산: 평가자산과 현금 기준 목표, 차트, 이미지 미리보기·저장
- 국내 KRW / 해외 USD 자산, 수동 환율, 최대 소수점 8자리 수량
- Excel/CSV/JSON 가져오기·내보내기, 목표 이력 최근 5개
- 한글 / US 표시 언어와 다크·라이트·메트릭스 테마: 마지막 선택 자동 저장
- 언어 전환 시 입력 중인 평단 조건과 비중 목표 유지
- 제작자명 클릭 후 승인 문구로 소스 TXT 내보내기

US는 영어 표시 모드입니다. 비중 계산의 기준 통화는 **KRW**이며 USD 자산은 입력 환율로 환산합니다.
사용자가 입력한 종목명과 목표 이름은 번역하지 않습니다. 실제 주문·실시간 시세 조회 기능은 없습니다.
목표를 내 자산에 덮어쓰는 기능은 보류하여 포함하지 않았습니다.

## 기존 이용자와 자료 보존
1.7.0의 투자계산기에서 이름이 변경되었습니다. 기존 설치 ID와 자료 경로는 유지합니다.
재설치 시 내 자산·저장 목표·설정은 보존됩니다.
자료 경로: `%LOCALAPPDATA%/IndependentInvestmentCalculator`
자료도 삭제하려면 설치파일의 제거 메뉴에서 저장 자료 삭제 옵션을 선택하세요.
엑셀 내보내기 수량은 8자리 정밀도 보존을 위해 텍스트 셀로 저장합니다.

## 개발·라이선스
Rust 실행기 + Python Tkinter UI입니다. [개발 안내](SOURCE_GUIDE.md) / [MIT](LICENSE) / [외부 구성요소](THIRD_PARTY.md)
[1.8.2 검증 결과](docs/RELEASE_CHECK_1.8.2.md)

---

# English

**mikunoi_Stock_Calculator** is a free, offline Windows stock calculator by **mikunoi**, released under the MIT License.

## Download
[Download the latest release](https://github.com/mikunoi/investment-calculator/releases/latest)

Under **Assets**, download **mikunoi_Stock_Calculator-Setup-1.8.5-x64.exe** and run it.
Windows 10/11 x64. End users do not need to install Rust or Python. The installer is not code-signed.
The Source code ZIP is for developers; the EXE is the installer.

## Features
- Average cost simulator with whole and fractional shares
- Portfolio allocation targets, donut charts and image export with preview
- Korean KRW and US USD assets, manual FX rate, up to 8 decimal places for share quantities
- Excel/CSV/JSON import/export; the five most recently saved target scenarios
- Korean / US English interface; Dark, Light and Matrix themes
- Language and theme restored on restart; in-progress calculator inputs retained when switching language
- Export the source as a Desktop TXT by clicking the creator name and entering the displayed confirmation phrase

**US selects English text, not USD reporting.** Allocation totals are in KRW, and USD assets are converted using your entered rate.
Your own holding and target names are preserved. No real trades or live market data requests are made.
Applying allocation targets to overwrite your assets is not included.

## Upgrade, data and removal
This app was named 투자계산기 in v1.7.0. Its installation identity and local data folder are preserved for upgrades.
Assets, saved targets and preferences are retained during reinstallations.
Data: `%LOCALAPPDATA%/IndependentInvestmentCalculator`
To remove data as well, use the installer removal option and select the data-deletion checkbox.
Excel exports store share quantities as text to preserve all eight decimal places.

## Development and license
Rust launcher + Python/Tkinter UI. See [development guide](SOURCE_GUIDE.md).
[MIT License](LICENSE), Copyright (c) 2026 mikunoi. Third-party components retain their own licenses.
See [release checks](docs/RELEASE_CHECK_1.8.2.md) for validation and remaining limits.


## 1.8.2 업데이트 / Update
실행 시 한 번 GitHub 새 버전을 확인하고 프로그램 아이콘·버전·변경내용을 안내합니다. 이용자가 업데이트를 선택하면 파일 검증 후 설치합니다. 예수금 감액 표시와 현재 평가금액/목표금액 열도 개선했습니다.

The app checks GitHub once at startup. When a newer release is available, a dialog shows the app icon, versions and release notes. Installation starts only after you choose Update and the download passes integrity checks. Cash withdrawal display and current/target valuation columns are also improved.

기존 1.8.0에는 업데이터가 없으므로 최초 1회 직접 설치해야 합니다. / Original 1.8.0 users must install this version manually once to enable future in-app updates.

### 업데이트 보류 / Update reminders
팝업의 `7일 동안 보이지 않기`는 재시작 후에도 유지됩니다. `나중에` 또는 7일 보류 후 우측 상단 `업데이트` 버튼에서 다시 열 수 있습니다. 1.8.1 설치본은 업데이트 조회 오류가 있어 1.8.2를 한 번 직접 설치하세요.

Choose **Remind me in 7 days** to pause automatic prompts across restarts. **Update** at the top right reopens the dialog after deferral. Version 1.8.1 has a packaged HTTPS issue; manually install 1.8.2 once to fix it.

### 1.8.3 검증 / Validation
추가 디버깅: 다운로드 진행 영역의 팝업 배경 크기 보정, 재시도 진행률 초기화, 7일 보류 설정을 포함한 파일별 원자적 백업. 격리 회귀검사 16개 통과.

Additional fixes: update card resizing during downloads, progress reset on retry, atomic per-file backups including reminder settings. 16 isolated regression tests passed. Other-PC and power-loss recovery remain untested.


## 1.8.4 누적 수정 / Cumulative fixes
- 이전 공개 업데이트로 덮어써졌던 로컬 수정사항을 정식 설치파일에 통합했습니다.
- Windows Shell 기반 Rust 런처로 실행 경로 보완, 중복 실행 시 안내, 화면 작업영역에 맞는 창 크기·위치 보정.
- 업데이트 팝업 드래그, 항상 위 표시, 본창 종료 시 함께 종료. 아이콘 녹색 업데이트 버튼.
- 시작 화면과 종료 시 예약 콜백 정리. 자산·목표·언어·테마는 보존합니다.

Includes the previously local-only fixes in the official installer: Windows Shell-based Rust launch, single-instance notice, monitor work-area sizing, draggable always-on-top update dialog, green update buttons, and pending UI callback cleanup. Existing holdings, saved targets, language and theme are preserved. The update dialog stays above other apps until dismissed.

If an older version cannot open, install the latest EXE manually. No Rust/Python installation is required. See [validation](docs/RELEASE_CHECK_1.8.4.md).

Validation: 18 isolated regression checks and three packaged launch/close cycles passed. The launcher processes Windows messages while waiting for the UI; duplicate launch shows a notice without creating another calculator.

## v1.8.5 안정화 / Stabilization
창 초기 표시 순서와 업데이트 실행환경 분리를 개선하고, 최소화 중 화면 감시 빈도를 줄였습니다. 21개 회귀검사를 통과했습니다.
Improved initial window display and isolated updater runtime environments. Reduced monitor polling while minimized. 21 regression checks passed; see docs/RELEASE_CHECK_1.8.5.md for limits.

