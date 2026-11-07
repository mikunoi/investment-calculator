# 투자계산기 개발 안내
Rust stdlib 실행기 + Python 3.12 Tkinter UI 구성입니다.
ui/main.py: 앱, portfolio_data.py: 자산 검증, average_cost.py: 평단,
allocation_tool.py: 목표 비중, allocation_export.py: 이미지 저장.

## 실행 (PowerShell)
```powershell
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe build_source.py
.venv/Scripts/python.exe ui/main.py
```

## 설치파일 빌드
Rust stable MSVC, Visual Studio C++ Build Tools, Windows SDK, Inno Setup을 설치하세요.
SDK 버전이 다르면 RC 환경변수에 rc.exe 경로를 지정하세요.
```powershell
./build.ps1 -Compiler 'C:/Program Files (x86)/Inno Setup 7/ISCC.exe'
```
결과는 releases 폴더에 생성됩니다. 최종 사용자에게 개발 도구는 필요하지 않습니다.

## 소스 TXT 복원
BEGIN FILE/END FILE 사이를 같은 상대 경로에 저장하세요.
BASE64 FILE은 디코딩하여 지정된 아이콘 경로에 저장하세요.
생성된 generated 폴더를 다시 소스 묶음에 넣지 마세요.

## 동작 유지
자료는 LOCALAPPDATA/IndependentInvestmentCalculator에 보존됩니다.
실제 주문과 네트워크 조회가 없는 오프라인 계산기입니다.
탭은 애니메이션 없이 전환합니다. 목표 이력은 최근 5개입니다.
환율이 없는 해외 자산은 경고합니다. 수량은 정수로 입력합니다.
소스 저장 승인 문구는 정확히 '감사합니다 mikunoi님'입니다.

## 라이선스
MIT License, Copyright (c) 2026 mikunoi. LICENSE를 함께 유지하세요.
