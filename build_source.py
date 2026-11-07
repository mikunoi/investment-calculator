"""Build an explicit source-only snapshot, without runtime/user directories."""
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent
files = sorted((ROOT / 'ui').glob('*.py')) + [ROOT / path for path in (
    'build_source.py', 'build.ps1', 'setup.iss', 'launcher/Cargo.toml',
    'launcher/Cargo.lock', 'launcher/build.rs', 'launcher/src/main.rs',
    'SOURCE_GUIDE.md', 'requirements.txt', 'ui/translations.json', 'LICENSE')]
parts = ['투자계산기 소스 묶음 / mikunoi\n'
         'Codex 요청 예시: 아래 파일 경계별 소스를 같은 상대 경로로 복원하고 SOURCE_GUIDE.md를 읽어 개발을 이어가 주세요.\n'
         '개인 자산과 목표, 인증정보, ATS 소스는 포함하지 않습니다.\n'
         '이는 코드 전달용 자료이며 모델의 영구 학습을 보장하지 않습니다.\n']
for path in files:
    name = path.relative_to(ROOT).as_posix()
    parts.append(f'\n===== BEGIN FILE: {name} =====\n{path.read_text(encoding="utf-8-sig")}\n===== END FILE: {name} =====\n')
parts.append('\n===== BASE64 FILE: assets/matrix-icon.ico =====\n' +
             base64.b64encode((ROOT / 'assets/matrix-icon.ico').read_bytes()).decode('ascii') +
             '\n===== END BASE64 FILE =====\n')
(ROOT / 'generated').mkdir(exist_ok=True)
(ROOT / 'generated/InvestmentCalculator-source.txt').write_text(''.join(parts), encoding='utf-8')
