# 투자계산기

**mikunoi**의 Windows용 오프라인 투자 도구 · MIT License

## 다운로드
[최신 버전 설치파일 다운로드](https://github.com/mikunoi/investment-calculator/releases/latest)

Releases의 `InvestmentCalculator-Setup-1.7.0-x64.exe`를 실행하세요.
Windows 10/11 x64용입니다. 사용자는 Rust/Python을 별도로 설치할 필요가 없습니다.
설치파일은 코드 서명되지 않았습니다.

## 주요 기능
- 평단관리: 추가 매수 수량·가격으로 평균단가 계산
- 비중계산: 평가자산+현금 기준 목표, 원형차트, 이미지 미리보기/저장
- 국내 KRW / 해외 USD 자산 및 수동 환율 입력
- Excel/CSV/JSON 가져오기·내보내기
- 최근 목표 5개 저장·불러오기·이름 변경
- 다크·라이트·메트릭스와 마지막 테마 유지
- 제작자명 클릭 후 승인 문구로 소스 TXT 저장

실제 주문과 실시간 시세 조회 기능은 없습니다. 목표를 내 자산에 덮어쓰는 기능은 포함하지 않습니다.

## 데이터와 제거
자료는 `%LOCALAPPDATA%/IndependentInvestmentCalculator`에 저장됩니다.
재설치 및 일반 제거 시 기존 자산과 목표는 보존됩니다.
자료도 지우려면 설치파일의 제거 메뉴에서 저장 자료 삭제 옵션을 선택하세요.

## 개발
Rust 실행기 + Python Tkinter UI입니다. [개발 안내](SOURCE_GUIDE.md)를 참고하세요.

## 라이선스
[MIT](LICENSE) · Copyright (c) 2026 mikunoi.
외부 의존성은 각각의 라이선스를 따릅니다. [외부 구성요소](THIRD_PARTY.md)

## 검증 범위
1.7.0 Windows 빌드 완료. 최신 테마 변경의 GUI 회귀 시험과 다른 PC 설치는 미검증입니다.
