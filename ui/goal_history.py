"""Five explicitly saved scenarios, each with its original local asset snapshot."""
import os,json,uuid
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from tkinter import simpledialog,messagebox
import tkinter as tk
from tkinter import ttk

PATH=Path(os.environ['LOCALAPPDATA'])/'IndependentInvestmentCalculator'/'goals.json'

def read():
    if not PATH.exists():return []
    value=json.loads(PATH.read_text(encoding='utf-8'))
    if not isinstance(value,list):raise ValueError('목표 저장 파일 형식이 올바르지 않습니다.')
    return value[:5]

def save(view):
    try:
        if not view.plans:raise ValueError('먼저 저장할 목표를 추가해 주세요.')
        from allocation_tool import scenario
        scenario(view.data,view.plans,view.extra.get())
        name=simpledialog.askstring('목표 저장','저장할 목표 이름',initialvalue=datetime.now().strftime('%m/%d %H:%M 목표'),parent=view.winfo_toplevel())
        if name is None:return
        item=dict(id=uuid.uuid4().hex,name=name.strip() or '목표',at=datetime.now().isoformat(timespec='seconds'),data=view.data,plans=view.plans,extra=view.extra.get())
        items=[item]+read();items=items[:5]
        PATH.parent.mkdir(parents=True,exist_ok=True)
        tmp=PATH.with_suffix('.tmp');tmp.write_text(json.dumps(items,ensure_ascii=False,indent=2,default=str),encoding='utf-8');tmp.replace(PATH)
        messagebox.showinfo('목표 저장','저장했습니다. 최근 5개까지 보관합니다.',parent=view.winfo_toplevel())
    except Exception as e:messagebox.showerror('목표 저장 실패',str(e),parent=view.winfo_toplevel())

def load(view):
    try:items=read()
    except Exception as e:messagebox.showerror('목표 불러오기',str(e),parent=view.winfo_toplevel());return
    if not items:messagebox.showinfo('목표 불러오기','저장한 목표가 없습니다.',parent=view.winfo_toplevel());return
    parent=view.winfo_toplevel();p=view.p
    win=tk.Toplevel(parent);win.withdraw();win.title('최근 목표 불러오기');win.transient(parent);win.configure(bg=p['page'])
    tk.Label(win,text='저장 당시 자산과 예수금으로 복원합니다. 내 자산 목록은 바뀌지 않습니다.',bg=p['page'],fg=p['text'],font=('맑은 고딕',11)).pack(padx=18,pady=16)
    listing=tk.Listbox(win,height=7,bg=p['field'],fg=p['text'],selectbackground=p['button'],selectforeground='white',font=('맑은 고딕',12),exportselection=False)
    listing.pack(fill='both',expand=True,padx=18)
    for item in items:listing.insert('end',f"{item['at'].replace('T',' ')}  ·  {item['name']}")
    listing.selection_set(0)
    def restore():
        try:
            if not listing.curselection():return
            item=items[listing.curselection()[0]]
            from allocation_tool import scenario
            plans=[dict(plan,key=tuple(plan['key']),value=Decimal(plan['value'])) for plan in item['plans']]
            scenario(item['data'],plans,item['extra'])
            provider=view.provider
            try:
                view.provider=lambda:item['data'];view.refresh()
            finally:view.provider=provider
            view.plans=plans;view.extra.set(item['extra']);view.update_all()
            view.snapshot=True
            view.form_status.config(text='저장 당시 자산 기준 · 자료 갱신 시 현재 내 자산으로 전환됩니다.')
            win.destroy()
        except Exception as e:messagebox.showerror('목표 복원 실패',str(e),parent=win)
    def rename():
        try:
            if not listing.curselection():return
            index=listing.curselection()[0];item=items[index]
            name=simpledialog.askstring('목표 이름 수정','새 목표 이름',initialvalue=item['name'],parent=win)
            if name is None:return
            name=name.strip()
            if not name:raise ValueError('목표 이름을 입력해 주세요.')
            latest=read()
            target=next((r for r in latest if r.get('id')==item['id']),None)
            if target is None:raise ValueError('이 목표가 더 이상 저장되어 있지 않습니다. 창을 다시 열어 주세요.')
            target['name']=name
            tmp=PATH.with_suffix('.tmp')
            tmp.write_text(json.dumps(latest,ensure_ascii=False,indent=2,default=str),encoding='utf-8');tmp.replace(PATH)
            item['name']=name
            listing.delete(index);listing.insert(index,f"{item['at'].replace('T',' ')}  ·  {name}")
            listing.selection_set(index)
        except Exception as e:messagebox.showerror('목표 이름 수정 실패',str(e),parent=win)
    actions=tk.Frame(win,bg=p['page']);actions.pack(pady=16)
    ttk.Button(actions,text='이름 수정',command=rename).pack(side='left',padx=6)
    ttk.Button(actions,text='선택한 목표 불러오기',command=restore).pack(side='left',padx=6)
    listing.bind('<Double-Button-1>',lambda e:restore())
    win.update_idletasks();w=win.winfo_reqwidth();h=win.winfo_reqheight()
    win.geometry(f'+{max(0,parent.winfo_rootx()+(parent.winfo_width()-w)//2)}+{max(0,parent.winfo_rooty()+(parent.winfo_height()-h)//2)}')
    win.deiconify();win.grab_set()
