# 1.8.0 검증 / Validation (2026-11-08)

10 isolated regression tests passed: fractional average cost, invalid quantities, 8-place quantity preservation through Excel/CSV/JSON, KRW/USD conversion, allocation funding invariants, five-goal history, English UI and image text, language/theme restart persistence, chart selection, cached tabs and shutdown.
사용자 자산 파일 대신 임시 LOCALAPPDATA에서 시험했습니다.
300 cached tab switches took approximately 42 ms in hidden Tk (not a visual frame-rate benchmark).

Remaining limits: Windows-native file dialogs follow OS language; user-entered names remain unchanged. Independent clean-PC testing and broad visual checks across all screen sizes are not completed. Installer is unsigned.
