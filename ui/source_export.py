from i18n import tr
"""Explicit local source export; never reads portfolio or goal storage."""
import ctypes
from datetime import datetime
from pathlib import Path
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from uuid import uuid4

def consent_phrase():
    return tr('감사합니다 mikunoi님')


def export_source(consent):
    if consent != consent_phrase():
        raise ValueError(tr('승인 문구가 일치하지 않습니다.'))
    root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
    source = root / ('source' if getattr(sys, 'frozen', False) else 'generated') / 'InvestmentCalculator-source.txt'
    content = source.read_text(encoding='utf-8')
    desktop = ctypes.create_unicode_buffer(32768)
    if ctypes.windll.shell32.SHGetFolderPathW(None, 0x10, None, 0, desktop) != 0:
        raise OSError(tr('바탕화면 위치를 찾을 수 없습니다.'))
    target = Path(desktop.value) / f"{'mikunoi_Stock_Calculator-source-'}{datetime.now():%Y%m%d-%H%M%S}-{uuid4().hex[:6]}.txt"
    with target.open('x', encoding='utf-8-sig') as handle:
        handle.write(content)
    return target


def show_source_export(parent):
    p = parent.p
    dialog = tk.Toplevel(parent)
    dialog.title(tr('투자계산기 소스 저장'))
    dialog.configure(bg=p['page'])
    dialog.transient(parent)
    dialog.resizable(False, False)
    tk.Label(dialog, text=tr('투자계산기 소스를 바탕화면 TXT로 저장하고 메모장으로 엽니다.\nCodex에 전달할 코드와 빌드 안내가 포함됩니다.\n개인 자산·저장된 목표는 포함되지 않습니다.\n\n아래 문구를 정확히 입력하면 저장에 동의한 것으로 처리합니다.'),
             bg=p['page'], fg=p['text'], justify='left', font=('맑은 고딕', 11)).pack(padx=24, pady=20)
    tk.Label(dialog, text=consent_phrase(), bg=p['page'], fg='#3CFB91',
             font=('맑은 고딕', 13, 'bold'), anchor='center').pack(fill='x', padx=24, pady=(0, 20))
    value = tk.StringVar()
    entry = ttk.Entry(dialog, textvariable=value, width=42)
    entry.pack(padx=24, pady=(0, 16))
    buttons = tk.Frame(dialog, bg=p['page'])
    buttons.pack(pady=(0, 20))

    def save():
        if value.get() != consent_phrase():
            return
        try:
            target = export_source(value.get())
        except Exception as exc:
            messagebox.showerror(tr('소스 저장 실패'), str(exc), parent=dialog)
            return
        dialog.destroy()
        try:
            subprocess.Popen(['notepad.exe', str(target)])
        except OSError:
            messagebox.showinfo(tr('소스 저장 완료'), f"{tr('메모장을 열지 못했지만 파일은 저장되었습니다.\n')}{target}", parent=parent)

    button = ttk.Button(buttons, text=tr('동의하고 저장'), command=save, state='disabled')
    button.pack(side='left', padx=6)
    ttk.Button(buttons, text=tr('취소'), command=dialog.destroy).pack(side='left', padx=6)
    value.trace_add('write', lambda *_: button.configure(state='normal' if value.get() == consent_phrase() else 'disabled'))
    dialog.bind('<Escape>', lambda _: dialog.destroy())
    dialog.bind('<Return>', lambda _: save())
    dialog.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() - dialog.winfo_reqwidth()) // 2
    y = parent.winfo_rooty() + (parent.winfo_height() - dialog.winfo_reqheight()) // 2
    dialog.geometry(f'+{max(0,x)}+{max(0,y)}')
    dialog.grab_set()
    entry.focus_set()
