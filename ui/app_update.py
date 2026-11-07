"""One startup check; no resident updater, credentials, or portfolio upload."""
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from uuid import uuid4
from PIL import Image, ImageTk
from i18n import tr
import i18n

VERSION = '1.8.1'
REPO = 'mikunoi/investment-calculator'
API = 'https://api.github.com/repos/' + REPO + '/releases/latest'
DATA = Path(os.environ['LOCALAPPDATA']) / 'IndependentInvestmentCalculator'
MAX_FILE = 150 * 1024 * 1024


def file_digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source,'sha256').hexdigest()


def version(value):
    match = re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)', str(value))
    return tuple(map(int, match.groups())) if match else None


def release():
    request = Request(API, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'mikunoi-Stock-Calculator/' + VERSION})
    with urlopen(request, timeout=6) as response:
        raw = response.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        return None
    data = json.loads(raw)
    tag = data.get('tag_name', '')
    target = version(tag)
    if not target or target <= version(VERSION) or data.get('draft') or data.get('prerelease'):
        return None
    name = 'mikunoi_Stock_Calculator-Setup-' + tag.lstrip('v') + '-x64.exe'
    for asset in data.get('assets', []):
        digest = str(asset.get('digest', ''))
        url = str(asset.get('browser_download_url', ''))
        parsed = urlparse(url)
        expected = '/' + REPO + '/releases/download/' + tag + '/' + name
        if (asset.get('name') == name and asset.get('state') == 'uploaded'
                and parsed.scheme == 'https' and parsed.netloc == 'github.com'
                and parsed.path == expected and not parsed.query and not parsed.fragment
                and re.fullmatch(r'sha256:[a-fA-F0-9]{64}', digest)
                and 0 < int(asset.get('size', 0)) <= MAX_FILE):
            return dict(tag=tag, name=name, url=url, digest=digest[7:].lower(),
                        size=int(asset['size']), notes=str(data.get('body') or '')[:30000])
    return None


def download(info, cancel, messages):
    cache = DATA / 'update-cache'
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / (uuid4().hex + '-' + info['name'])
    partial = target.with_suffix('.part')
    complete = False
    try:
        request = Request(info['url'], headers={'User-Agent': 'mikunoi-Stock-Calculator/' + VERSION})
        digest = hashlib.sha256(); count = 0; last_notice = 0
        started = time.monotonic()
        with urlopen(request, timeout=10) as response, partial.open('xb') as output:
            final = urlparse(response.geturl())
            if final.scheme != 'https' or final.hostname not in ('github.com', 'release-assets.githubusercontent.com', 'objects.githubusercontent.com'):
                raise ValueError('Unexpected download destination')
            while True:
                if cancel.is_set():return
                if time.monotonic() - started > 600:raise TimeoutError('Download timed out')
                chunk = response.read(128 * 1024)
                if not chunk:break
                count += len(chunk)
                if count > info['size'] or count > MAX_FILE:raise ValueError('Unexpected file size')
                output.write(chunk); digest.update(chunk)
                if time.monotonic() - last_notice > .25:
                    messages.put(('progress', count / info['size'] * 100));last_notice = time.monotonic()
            output.flush();os.fsync(output.fileno())
        if cancel.is_set():return
        if count != info['size'] or digest.hexdigest() != info['digest']:
            raise ValueError('Installer integrity check failed')
        partial.replace(target);complete = True
        messages.put(('downloaded', target))
    finally:
        if not complete:partial.unlink(missing_ok=True)


def notes_for_language(text):
    # Display publisher text only; never render HTML or execute release content.
    marker = '## English'
    if marker in text:
        before, after = text.split(marker, 1)
        text = after if i18n.LANGUAGE == 'en' else before
    return text.strip() or tr('변경사항은 GitHub 릴리스에서 확인할 수 있습니다.')


class StartupUpdate:
    def __init__(self, app):
        self.app = app;self.messages = queue.Queue();self.cancel = threading.Event()
        self.job = None;self.dialog = None;self.downloading = False
        self.job = app.after(1000, self.start)

    def start(self):
        self.job = None
        if self.cancel.is_set():return
        def work():
            # Remove only this updater's old downloads; never traverse user folders.
            try:
                cache=DATA/'update-cache'
                if cache.is_dir():
                    for item in cache.iterdir():
                        if re.fullmatch(r'[a-f0-9]{32}-mikunoi_Stock_Calculator-Setup-\d+\.\d+\.\d+-x64\.(exe|part)',item.name):
                            try:
                                if item.is_file() and time.time()-item.stat().st_mtime>7*86400:item.unlink()
                            except OSError:pass
            except OSError:pass
            try:self.messages.put(('release', release()))
            except Exception:self.messages.put(('release', None))
        threading.Thread(target=work, daemon=True, name='startup-version-check').start()
        self.poll()

    def poll(self):
        self.job = None
        if self.cancel.is_set():return
        finished = False
        try:
            while True:
                kind, value = self.messages.get_nowait()
                if kind == 'release':
                    finished = True
                    if value:self.show(value)
                elif kind == 'progress':
                    if self.dialog and self.dialog.winfo_exists():self.progress['value'] = value
                elif kind == 'downloaded':
                    finished = True;self.launch(value)
                elif kind == 'error':
                    finished = True;self.downloading = False
                    self.status.config(text=tr('다운로드하지 못했습니다. 기존 프로그램은 유지됩니다. 다시 시도해 주세요.'))
                    self.update_button.config(state='normal')
        except queue.Empty:pass
        if not finished:self.job = self.app.after(150, self.poll)

    def show(self, info):
        self.info = info;p = self.app.p
        win = self.dialog = tk.Toplevel(self.app);win.withdraw();win.transient(self.app)
        win.title(tr('업데이트 안내'));win.configure(bg=p['card']);win.resizable(False, False)
        icon = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent)) / 'assets/matrix-icon.ico'
        win.iconbitmap(str(icon));self.icon = ImageTk.PhotoImage(Image.open(icon).convert('RGBA').resize((64,64), Image.Resampling.LANCZOS))
        tk.Label(win, image=self.icon, bg=p['card']).pack(pady=(22,12))
        def label(text, size=11, bold=False):
            tk.Label(win, text=text, font=('맑은 고딕',size,'bold' if bold else 'normal'),bg=p['card'],fg=p['text']).pack(pady=5)
        label(tr('새로운 업데이트가 있습니다'),19,True);label('mikunoi_Stock_Calculator')
        label(f"{tr('현재')} v{VERSION}  →  {tr('새 버전')} {info['tag']}",12,True)
        label(tr('주요 변경사항'),13,True)
        frame=tk.Frame(win,bg=p['card']);frame.pack(fill='both',padx=24,pady=8)
        body=tk.Text(frame,width=62,height=9,wrap='word',bg=p['field'],fg=p['text'],relief='flat',font=('맑은 고딕',11),padx=12,pady=10)
        bar=ttk.Scrollbar(frame,command=body.yview);body.configure(yscrollcommand=bar.set)
        bar.pack(side='right',fill='y');body.pack(fill='both',expand=True)
        body.insert('1.0',notes_for_language(info['notes']));body.config(state='disabled')
        label(tr('내 자산 · 저장한 목표 · 설정은 유지됩니다.'))
        label(tr('저장하지 않은 계산 입력은 업데이트 전에 저장해 주세요.'),10)
        self.status=tk.Label(win,text='',bg=p['card'],fg=p['muted'],wraplength=530);self.status.pack(pady=4)
        self.progress=ttk.Progressbar(win,length=500,maximum=100);self.progress.pack(pady=4)
        buttons=tk.Frame(win,bg=p['card']);buttons.pack(pady=(12,22))
        tk.Button(buttons,text=tr('나중에'),command=self.dismiss,bg=p['field'],fg=p['text'],relief='flat',font=('맑은 고딕',12),padx=28,pady=10).pack(side='left',padx=6)
        self.update_button=tk.Button(buttons,text=tr('지금 업데이트'),command=self.begin_download,bg='#3176F6',fg='white',relief='flat',font=('맑은 고딕',12,'bold'),padx=25,pady=10)
        self.update_button.pack(side='left',padx=6)
        win.protocol('WM_DELETE_WINDOW',self.dismiss);win.update_idletasks()
        x=max(0,self.app.winfo_rootx()+(self.app.winfo_width()-win.winfo_reqwidth())//2)
        y=max(0,self.app.winfo_rooty()+(self.app.winfo_height()-win.winfo_reqheight())//2)
        win.geometry(f'+{x}+{y}');win.deiconify();win.grab_set()

    def dismiss(self):
        self.stop()
        if self.dialog and self.dialog.winfo_exists():self.dialog.destroy()

    def begin_download(self):
        if self.downloading:return
        self.downloading=True;self.update_button.config(state='disabled')
        self.status.config(text=tr('설치파일 다운로드 및 무결성 확인 중…'))
        def work():
            try:download(self.info,self.cancel,self.messages)
            except Exception:self.messages.put(('error',None))
        threading.Thread(target=work,daemon=True,name='update-download').start();self.poll()

    def launch(self, installer):
        if self.cancel.is_set():return
        try:
            # Recheck immediately before execution, including any cached-file changes.
            if file_digest(installer)!=self.info['digest']:
                raise ValueError('Installer integrity check failed')
            backup=DATA/'update-backup';backup.mkdir(exist_ok=True)
            for name in ('portfolio.json','goals.json','settings.json'):
                source=DATA/name
                if source.is_file():shutil.copy2(source,backup/name)
            if not getattr(sys,'frozen',False):raise RuntimeError('Updates require the installed application')
            install=Path(sys.executable).resolve().parent.parent
            if not (install/'mikunoi_Stock_Calculator.exe').is_file():raise RuntimeError('Installation path is invalid')
            subprocess.Popen([str(installer),'/APPUPDATE=1','/SILENT','/NORESTART','/DIR='+str(install),'/LOG='+str(DATA/'update-install.log')],cwd=str(installer.parent))
        except Exception:
            self.downloading=False;self.update_button.config(state='normal')
            self.status.config(text=tr('업데이트를 시작하지 못했습니다. 기존 프로그램은 유지됩니다.'))
            return
        self.app.close()

    def stop(self):
        self.cancel.set()
        if self.job is not None:
            self.app.after_cancel(self.job);self.job=None
