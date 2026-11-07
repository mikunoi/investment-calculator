"""Local Windows integration for the standalone calculator."""
import os
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from i18n import tr
from average_cost import SoftButton


def install_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent.parent
    return Path(__file__).resolve().parent.parent / 'package'


def shortcut(action):
    root = install_dir()
    exe = root / 'mikunoi_Stock_Calculator.exe'
    if not exe.is_file():
        raise OSError(tr('설치된 실행파일을 찾을 수 없습니다.'))
    script = r"""
$ErrorActionPreference='Stop'
$w=New-Object -ComObject WScript.Shell
$link=Join-Path $w.SpecialFolders.Item('Desktop') 'mikunoi_Stock_Calculator.lnk'
$exe=Join-Path $env:CALC_INSTALL_ROOT 'mikunoi_Stock_Calculator.exe'
$exists=Test-Path -LiteralPath $link
$owned=$false
if($exists){$s=$w.CreateShortcut($link);$owned=($s.TargetPath -eq $exe)}
if($env:CALC_SHORTCUT_ACTION -eq 'status'){if($owned){'1'}else{'0'};exit}
if($exists -and -not $owned){throw 'A different shortcut already uses this name.'}
if($env:CALC_SHORTCUT_ACTION -eq 'create'){
 $s=$w.CreateShortcut($link);$s.TargetPath=$exe;$s.WorkingDirectory=$env:CALC_INSTALL_ROOT
 $s.IconLocation=$exe+',0';$s.Description='mikunoi_Stock_Calculator';$s.Save()
}else{if($owned){Remove-Item -LiteralPath $link}}
"""
    env = os.environ.copy()
    env.update(CALC_INSTALL_ROOT=str(root), CALC_SHORTCUT_ACTION=action)
    ps = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    result = subprocess.run([str(ps), '-NoProfile', '-NonInteractive', '-Command', script],
                            env=env, capture_output=True, text=True, creationflags=0x08000000, timeout=15)
    if result.returncode:
        raise OSError(tr('바로가기를 변경하지 못했습니다. 같은 이름의 다른 바로가기가 있는지 확인해 주세요.'))
    return result.stdout.strip() == '1'


def settings_page(app, body):
    p=app.p
    tk.Label(body,text=tr('설정'),font=('맑은 고딕',23,'bold'),bg=p['page'],fg=p['text']).pack(anchor='w',padx=12,pady=(14,22))
    card=tk.Frame(body,bg=p['card']);card.pack(fill='x',padx=10,pady=8)
    info=tk.Label(card,text='',bg=p['card'],fg=p['muted'],font=('맑은 고딕',11))
    def create_shortcut():
        try:
            shortcut('create')
            info.config(text=tr('바로가기를 추가했습니다.'))
        except Exception as error:
            messagebox.showerror(tr('설정'),str(error),parent=app)
    SoftButton(card,tr('바탕화면 바로가기 만들기'),create_shortcut,p,width=270,height=44).pack(anchor='w',padx=24,pady=(22,10))
    info.pack(anchor='w',padx=24,pady=(0,18))
    def open_folder():
        try:os.startfile(str(install_dir()))
        except OSError as error:messagebox.showerror(tr('설정'),str(error),parent=app)
    SoftButton(card,tr('설치 폴더 열기'),open_folder,p,width=210,height=44).pack(anchor='w',padx=24,pady=(0,18))
    def open_maintenance():
        try:
            import shutil, tempfile
            from app_update import spawn_installer
            setup=install_dir()/'maintenance-setup.exe'
            if not setup.is_file():
                raise OSError(tr('설치파일을 찾을 수 없습니다. 내려받은 설치파일을 실행해 주세요.'))
            # Run outside the installation folder so removal can delete that folder.
            folder=Path(tempfile.mkdtemp(prefix='mikunoi-maintenance-'))
            target=folder/'setup.exe';shutil.copy2(setup,target)
            spawn_installer([str(target)],str(folder))
            app.close()
        except Exception as error:
            messagebox.showerror(tr('설치제거'),str(error),parent=app)
    SoftButton(card,tr('설치제거'),open_maintenance,p,width=210,height=44).pack(anchor='w',padx=24,pady=(0,10))
    tk.Label(card,text=tr('계산기를 닫고 설치파일을 엽니다. 설치제거 항목을 선택해 주세요.'),bg=p['card'],fg=p['muted'],font=('맑은 고딕',11)).pack(anchor='w',padx=24,pady=(0,18))
    tk.Label(card,text=str(install_dir()),bg=p['card'],fg=p['muted'],font=('맑은 고딕',10),wraplength=850,justify='left').pack(anchor='w',padx=24,pady=(0,22))
