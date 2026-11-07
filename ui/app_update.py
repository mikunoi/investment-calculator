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
from PIL import Image, ImageTk, ImageDraw
from i18n import tr
import i18n
from scroll_support import SlimScrollbar

VERSION = '1.8.6'
REPO = 'mikunoi/investment-calculator'
API = 'https://api.github.com/repos/' + REPO + '/releases/latest'
DATA = Path(os.environ['LOCALAPPDATA']) / 'IndependentInvestmentCalculator'
MAX_FILE = 150 * 1024 * 1024


def installer_environment():
    env=os.environ.copy()
    env['PYINSTALLER_RESET_ENVIRONMENT']='1'
    for key in ('TCL_LIBRARY','TK_LIBRARY','PYTHONHOME','PYTHONPATH'):
        env.pop(key,None)
    return env


def spawn_installer(command,cwd):
    # External setup must use the system DLL search path, not our bundled runtime.
    kernel=None
    if os.name=='nt' and getattr(sys,'frozen',False):
        import ctypes
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.SetDllDirectoryW.argtypes=[ctypes.c_wchar_p]
        if not kernel.SetDllDirectoryW(None):raise ctypes.WinError(ctypes.get_last_error())
    try:
        return subprocess.Popen(command,cwd=cwd,env=installer_environment())
    finally:
        if kernel is not None:kernel.SetDllDirectoryW(getattr(sys,'_MEIPASS',None))


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
    lines=[]
    for line in text.splitlines():
        line=re.sub(r'^\s*#{1,6}\s*', '', line).strip()
        if line in ('한국어','English'):continue
        line=re.sub(r'^[-*]\s+', '• ', line)
        line=line.replace('**','').replace('`','')
        lines.append(line)
    return '\n'.join(lines).strip() or tr('변경사항은 GitHub 릴리스에서 확인할 수 있습니다.')


def snoozed_until():
    try:
        value=float(json.loads((DATA/'update-preferences.json').read_text(encoding='utf-8')).get('snoozed_until',0))
        return value if 0<value<float('inf') else 0
    except (OSError,ValueError,TypeError,AttributeError):return 0


def save_snooze(until):
    DATA.mkdir(parents=True,exist_ok=True)
    temp=DATA/'update-preferences.tmp'
    temp.write_text(json.dumps({'snoozed_until':until}),encoding='utf-8')
    temp.replace(DATA/'update-preferences.json')


class RoundedAction(tk.Canvas):
    def __init__(self,parent,text,command,fill,foreground,width=200):
        super().__init__(parent,width=width,height=54,bg=parent['bg'],highlightthickness=0,bd=0,cursor='hand2')
        self.action=command;self.disabled=False
        scale=3
        pic=Image.new('RGBA',(width*scale,54*scale))
        ImageDraw.Draw(pic).rounded_rectangle((1,1,width*scale-2,54*scale-2),radius=12*scale,fill=fill,outline='#64809A',width=2)
        self.art=ImageTk.PhotoImage(pic.resize((width,54),Image.Resampling.LANCZOS))
        self.create_image(0,0,image=self.art,anchor='nw')
        self.caption=self.create_text(width/2,27,text=text,fill=foreground,font=('맑은 고딕',13,'bold'))
        self.bind('<Button-1>',lambda e:self.action() if not self.disabled else None)
        self.bind('<Return>',lambda e:self.action() if not self.disabled else None)
        self.configure(takefocus=True)
    def config(self,**kwargs):
        if 'state' in kwargs:
            self.disabled=kwargs.pop('state')=='disabled'
            self.configure(cursor='' if self.disabled else 'hand2')
        if kwargs:super().configure(**kwargs)



class StartupUpdate:
    def __init__(self, app):
        self.app = app;self.messages = queue.Queue();self.cancel = threading.Event()
        self.job = None;self.dialog = None;self.downloading = False;self.info=None
        self.raise_job=None;self.owner_bindings=[];self.drag_origin=None
        self.header_button=None;self.art_job=None;self.art_size=None
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
                    if value:
                        self.info=value
                        if time.time()<snoozed_until():self.ensure_button()
                        else:self.show(value)
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
        self.cancel=threading.Event();self.messages=queue.Queue();self.downloading=False
        win = self.dialog = tk.Toplevel(self.app);win.withdraw();win.transient(self.app)
        win.title(tr('업데이트 안내'));win.configure(bg='#FF00FE');win.resizable(False, False)
        win.overrideredirect(True);win.wm_attributes('-transparentcolor','#FF00FE')
        icon = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent)) / 'assets/matrix-icon.ico'
        win.iconbitmap(str(icon))
        with Image.open(icon) as source:self.icon=ImageTk.PhotoImage(source.convert('RGBA').resize((72,72),Image.Resampling.LANCZOS))
        shell=tk.Canvas(win,bg='#FF00FE',highlightthickness=0);shell.pack(fill='both',expand=True)
        panel=tk.Frame(shell,bg=p['card'])
        panel.pack(fill='both',expand=True,padx=16,pady=16)
        close=tk.Label(panel,text='×',bg=p['card'],fg=p['muted'],font=('맑은 고딕',21),cursor='hand2')
        close.place(relx=1,x=-4,y=0,anchor='ne');close.bind('<Button-1>',lambda e:self.dismiss())
        tk.Label(panel,image=self.icon,bg=p['card']).pack(pady=(24,14))
        def label(text,size=11,bold=False,color=None,pady=4):
            item=tk.Label(panel,text=text,font=('맑은 고딕',size,'bold' if bold else 'normal'),bg=p['card'],fg=color or p['text'])
            item.pack(pady=pady);return item
        label(tr('새로운 업데이트가 있습니다'),23,True)
        label('mikunoi_Stock_Calculator',14,pady=(0,18))
        pill=tk.Canvas(panel,width=410,height=42,bg=p['card'],highlightthickness=0)
        pill.pack()
        pic=Image.new('RGBA',(1230,126));ImageDraw.Draw(pic).rounded_rectangle((2,2,1227,123),radius=62,fill=p['field'],outline='#64809A',width=3)
        self.pill_image=ImageTk.PhotoImage(pic.resize((410,42),Image.Resampling.LANCZOS));pill.create_image(0,0,image=self.pill_image,anchor='nw')
        pill.create_text(110,21,text=f"{tr('현재')} v{VERSION}",fill=p['text'],font=('맑은 고딕',12,'bold'))
        pill.create_text(210,21,text='→',fill='#81C4FF',font=('맑은 고딕',16))
        pill.create_text(310,21,text=f"{tr('새 버전')} {info['tag']}",fill='#81C4FF',font=('맑은 고딕',12,'bold'))
        tk.Label(panel,text=tr('주요 변경사항'),font=('맑은 고딕',15,'bold'),bg=p['card'],fg=p['text'],anchor='w').pack(fill='x',padx=36,pady=(22,10))
        frame=tk.Frame(panel,bg=p['card']);frame.pack(fill='both',padx=36)
        body=tk.Text(frame,width=60,height=6,wrap='word',bg=p['card'],fg=p['text'],relief='flat',bd=0,highlightthickness=0,font=('맑은 고딕',12),spacing1=3,spacing3=5,padx=0,pady=0)
        bar=SlimScrollbar(frame,command=body.yview);body.configure(yscrollcommand=bar.set)
        bar.pack(side='right',fill='y');body.pack(fill='both',expand=True)
        body.insert('1.0',notes_for_language(info['notes']));body.config(state='disabled')
        tk.Frame(panel,height=1,bg='#425A70').pack(fill='x',padx=36,pady=(18,12))
        label(tr('내 자산 · 저장한 목표 · 설정은 유지됩니다.'),11,color=p['muted'])
        label(tr('저장하지 않은 계산 입력은 업데이트 전에 저장해 주세요.'),9,color=p['muted'],pady=(2,14))
        self.download_area=tk.Frame(panel,bg=p['card'])
        self.status=tk.Label(self.download_area,text='',bg=p['card'],fg=p['muted'],wraplength=530);self.status.pack(pady=4)
        self.progress=ttk.Progressbar(self.download_area,length=500,maximum=100);self.progress.pack(pady=4)
        self.buttons=tk.Frame(panel,bg=p['card']);self.buttons.pack(pady=(2,12))
        RoundedAction(self.buttons,tr('나중에'),self.dismiss,p['field'],p['text'],180).pack(side='left',padx=8)
        self.update_button=RoundedAction(self.buttons,tr('지금 업데이트'),self.begin_download,'#3CFB91','#063020',216)
        self.update_button.pack(side='left',padx=8)
        snooze=tk.Label(panel,text=tr('7일 동안 보이지 않기'),bg=p['card'],fg=p['muted'],cursor='hand2',takefocus=True,font=('맑은 고딕',10,'underline'))
        snooze.pack(pady=(0,5))
        snooze.bind('<Button-1>',lambda e:self.dismiss(snooze=True));snooze.bind('<Return>',lambda e:self.dismiss(snooze=True))
        win.bind('<Escape>',lambda e:self.dismiss())
        win.protocol('WM_DELETE_WINDOW',self.dismiss);win.update_idletasks()
        self.art_size=None
        self.art_item=shell.create_image(0,0,anchor='nw')
        def paint():
            self.art_job=None
            if not win.winfo_exists():return
            w,h=shell.winfo_width(),shell.winfo_height()
            if (w,h)==self.art_size:return
            self.art_size=w,h
            backdrop=Image.new('RGBA',(w*3,h*3))
            ImageDraw.Draw(backdrop).rounded_rectangle((2,2,w*3-3,h*3-3),radius=22*3,fill=p['card'],outline='#526D84',width=4)
            # Color-key transparency must be binary: partial alpha blends with magenta.
            edge=backdrop.resize((w,h),Image.Resampling.LANCZOS)
            opaque=Image.new('RGBA',(w,h),p['card'])
            opaque.alpha_composite(edge)
            keyed=Image.new('RGB',(w,h),'#FF00FE')
            keyed.paste(opaque.convert('RGB'),mask=edge.getchannel('A').point(lambda a:255 if a>=128 else 0))
            self.card_art=ImageTk.PhotoImage(keyed,master=win)
            shell.itemconfigure(self.art_item,image=self.card_art)
        def resize(event):
            if self.art_job is None:self.art_job=win.after_idle(paint)
        shell.bind('<Configure>',resize)
        paint()
        x=max(0,self.app.winfo_rootx()+(self.app.winfo_width()-win.winfo_reqwidth())//2)
        y=max(0,min(win.winfo_screenheight()-win.winfo_reqheight()-40,self.app.winfo_rooty()+(self.app.winfo_height()-win.winfo_reqheight())//2))
        win.geometry(f'+{x}+{y}');win.deiconify()
        self.attach_window_behavior(win,panel,shell)

    def attach_window_behavior(self,win,panel,shell):
        # Borderless Windows popups can lose owned-window ordering: keep visible until dismissed.
        win.attributes("-topmost",True)
        win.bind("<ButtonPress-1>",lambda event:self.activate_dialog(),add="+")
        def raise_with_owner(event):
            if getattr(self.app,'closing',False):return
            if event.widget.winfo_toplevel() is not self.app:return
            if self.raise_job is None:self.raise_job=self.app.after(200,self.raise_dialog)
        for sequence in ('<FocusIn>','<ButtonPress-1>','<Map>'):
            binding=self.app.bind(sequence,raise_with_owner,add='+')
            self.owner_bindings.append((sequence,binding))
        def start_drag(event):
            self.drag_origin=(event.x_root,event.y_root,win.winfo_x(),win.winfo_y())
        def drag(event):
            if self.drag_origin:
                x,y,wx,wy=self.drag_origin
                win.geometry(f'{wx+event.x_root-x:+d}{wy+event.y_root-y:+d}')
        def end_drag(event):self.drag_origin=None
        # Keep text scrolling and buttons independent from window dragging.
        surfaces=[panel,shell]+[child for child in panel.winfo_children()
            if (isinstance(child,tk.Label) and child.cget('cursor')!='hand2') or isinstance(child,tk.Canvas)]
        for widget in surfaces:
            widget.bind('<ButtonPress-1>',start_drag,add='+')
            widget.bind('<B1-Motion>',drag,add='+')
            widget.bind('<ButtonRelease-1>',end_drag,add='+')
        self.raise_dialog()

    def raise_dialog(self):
        self.raise_job=None
        if not getattr(self.app,'closing',False) and self.dialog and self.dialog.winfo_exists():
            self.dialog.attributes("-topmost",True)
            self.dialog.lift()

    def activate_dialog(self):
        if not getattr(self.app,"closing",False) and self.dialog and self.dialog.winfo_exists():
            self.dialog.attributes("-topmost",True)
            self.dialog.lift()
            self.dialog.focus_force()

    def ensure_button(self):
        if not self.info:return
        if self.header_button is not None and self.header_button.winfo_exists():return
        from average_cost import SoftButton
        class UpdateButton(SoftButton):
            def draw(button,event=None):
                original=button.p
                button.p=dict(original,field='#3CFB91',line='#65FCA8',text='#063020')
                try:super().draw(event)
                finally:button.p=original
        self.header_button=UpdateButton(self.app.nav,tr('업데이트'),self.open_pending,self.app.p,width=92,height=36)
        self.header_button.pack(side='right',padx=8)

    def open_pending(self):
        if self.dialog and self.dialog.winfo_exists():self.activate_dialog();return
        if self.info:self.show(self.info)

    def dismiss(self,snooze=False):
        if snooze:
            try:save_snooze(time.time()+7*24*60*60)
            except OSError:
                messagebox.showerror(tr('업데이트 안내'),tr('보류 설정을 저장하지 못했습니다. 다시 시도해 주세요.'),parent=self.dialog)
                return
        self.stop()
        if self.dialog and self.dialog.winfo_exists():self.dialog.destroy()
        self.dialog=None;self.downloading=False
        self.ensure_button()

    def begin_download(self):
        if self.downloading:return
        self.downloading=True;self.update_button.config(state='disabled')
        self.progress['value']=0
        self.download_area.pack(fill='x',before=self.buttons,pady=(0,8))
        self.status.config(text=tr('설치파일 다운로드 및 무결성 확인 중…'))
        info,cancel,messages=self.info,self.cancel,self.messages
        def work():
            try:download(info,cancel,messages)
            except Exception:messages.put(('error',None))
        threading.Thread(target=work,daemon=True,name='update-download').start();self.poll()

    def launch(self, installer):
        if self.cancel.is_set():return
        try:
            # Recheck immediately before execution, including any cached-file changes.
            if file_digest(installer)!=self.info['digest']:
                raise ValueError('Installer integrity check failed')
            backup=DATA/'update-backup';backup.mkdir(exist_ok=True)
            for name in ('portfolio.json','goals.json','settings.json','update-preferences.json'):
                source=DATA/name
                if source.is_file():
                    pending=backup/(name+'.tmp')
                    shutil.copy2(source,pending);pending.replace(backup/name)
            if not getattr(sys,'frozen',False):raise RuntimeError('Updates require the installed application')
            install=Path(sys.executable).resolve().parent.parent
            if not (install/'mikunoi_Stock_Calculator.exe').is_file():raise RuntimeError('Installation path is invalid')
            spawn_installer([str(installer),'/APPUPDATE=1','/SILENT','/NORESTART','/DIR='+str(install),'/LOG='+str(DATA/'update-install.log')],cwd=str(installer.parent))
        except Exception:
            self.downloading=False;self.update_button.config(state='normal')
            self.status.config(text=tr('업데이트를 시작하지 못했습니다. 기존 프로그램은 유지됩니다.'))
            return
        self.app.close()

    def stop(self):
        self.cancel.set()
        if self.raise_job is not None:
            self.app.after_cancel(self.raise_job);self.raise_job=None
        for sequence,binding in self.owner_bindings:
            self.app.unbind(sequence,binding)
        self.owner_bindings.clear();self.drag_origin=None
        if self.art_job is not None and self.dialog and self.dialog.winfo_exists():
            self.dialog.after_cancel(self.art_job);self.art_job=None
        if self.job is not None:
            self.app.after_cancel(self.job);self.job=None
