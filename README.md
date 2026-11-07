# mikunoi_Stock_Calculator

**mikunoi**의 Windows 오프라인 주식 계산기 · MIT License

## 다운로드
[최신 버전 다운로드](https://github.com/mikunoi/investment-calculator/releases/latest)

Assets에서 **mikunoi_Stock_Calculator-Setup-1.8.0-x64.exe**를 받아 실행하세요.
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
[1.8.0 검증 결과](docs/RELEASE_CHECK_1.8.0.md)

---

# English

**mikunoi_Stock_Calculator** is a free, offline Windows stock calculator by **mikunoi**, released under the MIT License.

## Download
[Download the latest release](https://github.com/mikunoi/investment-calculator/releases/latest)

Under **Assets**, download **mikunoi_Stock_Calculator-Setup-1.8.0-x64.exe** and run it.
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
See [release checks](docs/RELEASE_CHECK_1.8.0.md) for validation and remaining limits.
