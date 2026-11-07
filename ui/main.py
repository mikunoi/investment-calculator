"""Standalone offline investment calculator. No broker or ATS imports."""
import os
import sys
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from copy import deepcopy
import dashboard_theme as theme
from average_cost import AverageCostView, PALETTES, SoftButton, number
from allocation_tool import AllocationView
from scroll_support import scroll_page, SlimScrollbar

DATA_DIR=Path(os.environ['LOCALAPPDATA'])/'IndependentInvestmentCalculator'
DATA_FILE=DATA_DIR/'portfolio.json'
SETTINGS_FILE=DATA_DIR/'settings.json'
MODES={'다크':'default','라이트':'toss','메트릭스':'matrix'}

from portfolio_data import validate
from allocation_media import format_money

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('투자계산기');self.geometry('1220x860');self.minsize(880,640)
        icon=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent.parent))/'assets'/'matrix-icon.ico'
        self.iconbitmap(default=str(icon))
        self.data=validate({});self.current=''
        self.pages={};self.data_revision=0;self.closing=False
        self.protocol('WM_DELETE_WINDOW',self.close)
        try:
            if DATA_FILE.exists():self.data=validate(json.loads(DATA_FILE.read_text(encoding='utf-8')))
        except Exception:
            messagebox.showwarning('보유자료 확인','저장된 자료를 읽지 못했습니다. 원본 파일은 유지됩니다. 새 자료를 저장하기 전에 백업해 주세요.',parent=self)
        saved_mode='다크'
        try:
            saved_mode=json.loads(SETTINGS_FILE.read_text(encoding='utf-8')).get('mode','다크')
        except (OSError,ValueError,AttributeError):pass
        if saved_mode not in MODES:saved_mode='다크'
        theme.select(MODES[saved_mode]);self.p=PALETTES[theme.CURRENT];self.configure(bg=self.p['page'])
        self.apply_style()
        self.nav=tk.Frame(self,bg=self.p['page']);self.nav.pack(fill='x',padx=18,pady=14)
        tk.Label(self.nav,text='투자계산기',font=('맑은 고딕',20,'bold'),bg=self.p['page'],fg=self.p['text']).pack(side='left',padx=(0,20))
        for title,kind in [('평단관리','average'),('비중계산','allocation'),('내 자산','assets')]:
            SoftButton(self.nav,title,lambda k=kind:self.show(k),self.p,width=110,height=40).pack(side='left',padx=4)
        self.mode=tk.StringVar(value=saved_mode)
        choice=ttk.Combobox(self.nav,textvariable=self.mode,values=list(MODES),state='readonly',width=8)
        choice.pack(side='right');choice.bind('<<ComboboxSelected>>',self.change_theme)
        self.host=tk.Frame(self,bg=self.p['page']);self.host.pack(fill='both',expand=True,padx=18,pady=(0,8))
        self.footer=tk.Frame(self,bg=self.p['page']);self.footer.pack(fill='x',padx=18,pady=(0,8))
        self.footer_line=tk.Frame(self.footer,bg=self.p['page']);self.footer_line.pack()
        self.status=tk.Label(self.footer_line,text='오프라인 계산 · 국내 KRW / 해외 USD · 비중은 원화 환산',font=('맑은 고딕',9),bg=self.p['page'],fg=self.p['muted'])
        self.status.pack(side='left')
        self.creator=tk.Label(self.footer_line,text='  |  mikunoi',cursor='hand2',takefocus=True,font=('맑은 고딕',9,'underline'),bg=self.p['page'],fg=self.p['muted'])
        self.creator.pack(side='left')
        from source_export import show_source_export
        for event in ('<Button-1>','<Return>','<space>'):
            self.creator.bind(event,lambda _:show_source_export(self))
        self.credit=tk.Label(self.footer_line,text=' · 2026 · v1.7.0',font=('맑은 고딕',9),bg=self.p['page'],fg=self.p['muted'])
        self.credit.pack(side='left')
        self.show('average')

    def apply_style(self):
        p=self.p;style=ttk.Style(self);style.theme_use('clam')
        style.configure('.',background=p['page'],foreground=p['text'],font=('맑은 고딕',11))
        style.configure('TEntry',fieldbackground=p['field'],foreground=p['text'],insertcolor=p['text'],bordercolor=p['line'],padding=6)
        style.configure('TCombobox',fieldbackground=p['field'],background=p['field'],foreground=p['text'],arrowcolor=p['text'],bordercolor=p['line'],padding=6)
        style.map('TCombobox',fieldbackground=[('readonly',p['field'])],foreground=[('readonly',p['text'])],selectbackground=[('readonly',p['field'])],selectforeground=[('readonly',p['text'])])
        style.configure('Treeview',background=p['card'],fieldbackground=p['card'],foreground=p['text'],rowheight=32,bordercolor=p['line'])
        style.configure('Treeview.Heading',background=p['field'],foreground=p['text'],padding=7)
        style.map('Treeview',background=[('selected',p['button'])],foreground=[('selected','white')])
        self.option_add('*TCombobox*Listbox.background',p['field']);self.option_add('*TCombobox*Listbox.foreground',p['text'])
        self.option_add('*TCombobox*Listbox.selectBackground',p['button']);self.option_add('*TCombobox*Listbox.selectForeground','white')

    def change_theme(self,event=None):
        theme.select(MODES.get(self.mode.get(),'default'));self.p=PALETTES[theme.CURRENT]
        try:
            DATA_DIR.mkdir(parents=True,exist_ok=True)
            temp=DATA_DIR/'settings.tmp'
            temp.write_text(json.dumps({'mode':self.mode.get()},ensure_ascii=False),encoding='utf-8')
            temp.replace(SETTINGS_FILE)
        except OSError as error:messagebox.showerror('테마 저장 실패',str(error),parent=self)
        self.configure(bg=self.p['page']);self.host.configure(bg=self.p['page'])
        self.nav.configure(bg=self.p['page'])
        for child in self.nav.winfo_children():
            if isinstance(child,SoftButton):child.p=self.p;child.configure(bg=self.p['page']);child.draw()
            elif isinstance(child,tk.Label):child.configure(bg=self.p['page'],fg=self.p['text'])
        self.status.configure(bg=self.p['page'],fg=self.p['muted'])
        self.credit.configure(bg=self.p['page'],fg=self.p['muted'])
        self.creator.configure(bg=self.p['page'],fg=self.p['muted'])
        self.footer.configure(bg=self.p['page']);self.footer_line.configure(bg=self.p['page'])
        self.apply_style()
        self.show(self.current)

    def show(self,kind):
        if self.closing:return
        stamp=(theme.CURRENT,self.data_revision)
        cached=self.pages.get(kind)
        if cached and cached[1]==stamp:
            if self.current!=kind:cached[0].tkraise()
            self.current=kind
            return
        # Build behind the current page, so partial geometry is never exposed.
        previous=self.pages.get(self.current)
        frame=tk.Frame(self.host,bg=self.p['page'])
        frame.place(x=0,y=0,relwidth=1,relheight=1)
        if previous:frame.lower(previous[0])
        try:
            body=scroll_page(frame,self.p['page'])
            if kind=='average':AverageCostView(body,lambda:deepcopy(self.data),theme.CURRENT).pack(fill='both',expand=True,padx=8)
            elif kind=='allocation':AllocationView(body,lambda:deepcopy(self.data),self.save_fx).pack(fill='both',expand=True,padx=8)
            else:self.assets(body)
            frame.update_idletasks()
        except Exception:
            frame.destroy()
            raise
        self.pages[kind]=(frame,stamp)
        frame.tkraise();self.current=kind
        if cached:cached[0].destroy()
        # Keep at most one current revision per tab; no growing cache.
        for key,(page,version) in list(self.pages.items()):
            if version!=stamp:
                page.destroy();del self.pages[key]

    def close(self):
        if self.closing:return
        self.closing=True
        # Widgets own their registered Tcl callbacks; destroy them through their owners.
        self.destroy()
        self.pages.clear()

    def save_fx(self,fx):
        proposal=deepcopy(self.data);proposal['fx']=fx
        self.persist(validate(proposal))
        if 'allocation' in self.pages:
            frame,_=self.pages['allocation']
            self.pages['allocation']=(frame,(theme.CURRENT,self.data_revision))

    def persist(self,data):
        DATA_DIR.mkdir(parents=True,exist_ok=True)
        temp=DATA_DIR/'portfolio.tmp'
        temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(DATA_FILE)
        self.data=data
        self.data_revision+=1

    def assets(self,body):
        p=self.p
        tk.Label(body,text='내 자산',font=('맑은 고딕',23,'bold'),bg=p['page'],fg=p['text']).pack(anchor='w',pady=10)
        tk.Label(body,text='국내는 원, 해외는 USD 기준 주당 매입가와 현재가를 입력하세요. 예수금은 원화 기준입니다.',font=('맑은 고딕',11),bg=p['page'],fg=p['muted']).pack(anchor='w',pady=6)
        if self.data.get('fx_missing'):
            tk.Label(body,text='해외자산이 있습니다. 비중계산에서 현재 환율을 입력해 주세요.',bg=p['page'],fg=p['error'],font=('맑은 고딕',11)).pack(anchor='w')
        top=tk.Frame(body,bg=p['page']);top.pack(fill='x',pady=12)
        tk.Label(top,text='현재 예수금 (원)',bg=p['page'],fg=p['text']).pack(side='left')
        cash=tk.StringVar(value=f"{Decimal(self.data['cash']):,f}");cash_entry=ttk.Entry(top,textvariable=cash,width=22);cash_entry.pack(side='left',padx=10)
        cash_entry.bind('<KeyRelease>',lambda e:format_money(cash_entry,cash))
        def save_cash():
            try:
                proposal=deepcopy(self.data);proposal['cash']=cash.get();self.persist(validate(proposal))
                self.status.config(text='예수금을 저장했습니다. 계산기 탭에서 반영됩니다.')
            except Exception as e:messagebox.showerror('입력 확인',str(e),parent=self)
        SoftButton(top,'예수금 저장',save_cash,p,width=120,height=36).pack(side='left')
        cols=('market','name','symbol','quantity','buy_price','current_price')
        table=tk.Frame(body,bg=p['page']);table.pack(fill='x',pady=10)
        tree=ttk.Treeview(table,columns=cols,show='headings',height=12,selectmode='browse')
        bar=SlimScrollbar(table,command=tree.yview);bar.pack(side='right',fill='y');tree.configure(yscrollcommand=bar.set);tree.pack(fill='both',expand=True)
        for col,label in zip(cols,('구분','종목명','종목코드','보유수량','매입가','현재가')):
            tree.heading(col,text=label);tree.column(col,width=80 if col=='market' else 220 if col=='name' else 135,anchor='center' if col in ('market','symbol') else 'w' if col=='name' else 'e')
        for i,row in enumerate(self.data['holdings']):
            unit='USD' if row['market']=='us' else '원'
            tree.insert('', 'end',iid=str(i),values=('해외' if row['market']=='us' else '국내',row['name'],row['symbol'],f"{row['quantity']:,}",f"{Decimal(row['buy_price']):,.2f} {unit}",f"{Decimal(row['current_price']):,.2f} {unit}"))
        def edit(index=None):
            win=tk.Toplevel(self);win.withdraw();win.title('보유종목 '+('추가' if index is None else '수정'));win.transient(self)
            win.configure(bg=p['page']);win.resizable(False,False)
            values={}
            row={} if index is None else self.data['holdings'][index]
            market=tk.StringVar(value='해외' if row.get('market')=='us' else '국내')
            tk.Label(win,text='자산 구분',bg=p['page'],fg=p['text']).grid(row=0,column=0,padx=18,pady=10)
            ttk.Combobox(win,textvariable=market,values=['국내','해외'],state='readonly').grid(row=0,column=1,padx=18,pady=10)
            unit_labels=[]
            for i,(col,title) in enumerate(zip(cols[1:],('종목명','종목코드 (선택)','보유수량 (주)','매입가','현재가')),1):
                label=tk.Label(win,text=title,bg=p['page'],fg=p['text'],font=('맑은 고딕',11));label.grid(row=i,column=0,sticky='w',padx=18,pady=10)
                if col in ('buy_price','current_price'):unit_labels.append((label,title))
                text=str(row.get(col,''))
                if text and col in ('quantity','buy_price','current_price'):text=f'{Decimal(text):,f}'
                values[col]=tk.StringVar(value=text)
                entry=ttk.Entry(win,textvariable=values[col],width=32);entry.grid(row=i,column=1,padx=18,pady=10)
                if col in ('quantity','buy_price','current_price'):entry.bind('<KeyRelease>',lambda e,w=entry,v=values[col]:format_money(w,v))
            def units(*args):
                for label,title in unit_labels:label.config(text=title+(' (USD)' if market.get()=='해외' else ' (원)'))
            market.trace_add('write',units);units()
            def commit():
                try:
                    proposal=deepcopy(self.data);item={c:v.get() or ('0' if c in cols[3:] else '') for c,v in values.items()};item['market']='us' if market.get()=='해외' else 'kr'
                    if index is None:proposal['holdings'].append(item)
                    else:proposal['holdings'][index]=item
                    self.persist(validate(proposal));win.destroy();self.show('assets')
                except Exception as e:messagebox.showerror('입력 확인',str(e),parent=win)
            SoftButton(win,'저장',commit,p,primary=True).grid(row=6,column=1,pady=16,sticky='e',padx=18)
            win.update_idletasks();w=win.winfo_reqwidth();h=win.winfo_reqheight()
            win.geometry(f'+{max(0,self.winfo_rootx()+(self.winfo_width()-w)//2)}+{max(0,self.winfo_rooty()+(self.winfo_height()-h)//2)}')
            win.deiconify();win.grab_set()
        def selected():
            return int(tree.selection()[0]) if tree.selection() else None
        def edit_selected():
            i=selected()
            if i is not None:edit(i)
        def delete():
            i=selected()
            if i is not None and messagebox.askyesno('종목 삭제','선택한 종목을 삭제할까요?',parent=self):
                proposal=deepcopy(self.data);del proposal['holdings'][i];self.persist(validate(proposal));self.show('assets')
        tree.bind('<Double-Button-1>',lambda e:edit_selected())
        actions=tk.Frame(body,bg=p['page']);actions.pack(fill='x')
        for title,fn in [('종목 추가',edit),('선택 수정',edit_selected),('선택 삭제',delete),('자료 내보내기',self.export_data),('자료 가져오기',self.import_data),('형식 안내',self.format_guide)]:
            SoftButton(actions,title,fn,p,width=118,height=38).pack(side='left',padx=3)

    def format_guide(self):
        from asset_files import GUIDE, export_file
        win=tk.Toplevel(self);win.title('자산 가져오기 형식 안내');win.transient(self);win.configure(bg=self.p['page'])
        tk.Label(win,text=GUIDE,justify='left',wraplength=650,bg=self.p['page'],fg=self.p['text'],font=('맑은 고딕',11)).pack(padx=22,pady=20)
        def template():
            path=filedialog.asksaveasfilename(parent=win,defaultextension='.xlsx',filetypes=[('Excel 양식','*.xlsx')],initialfile='투자계산기-입력양식.xlsx')
            if path:
                try:export_file(path,dict(cash='50000',holdings=[dict(name='예시 ETF',symbol='0046A0',quantity=10,krw='100000',evaluation_krw='105000')]))
                except Exception as e:messagebox.showerror('저장 실패',str(e),parent=win)
        ttk.Button(win,text='예제 엑셀 양식 저장',command=template).pack(pady=(0,18))
        win.update_idletasks();w=win.winfo_reqwidth();h=win.winfo_reqheight()
        win.geometry(f'+{max(0,self.winfo_rootx()+(self.winfo_width()-w)//2)}+{max(0,self.winfo_rooty()+(self.winfo_height()-h)//2)}')

    def export_data(self):
        from asset_files import export_file
        path=filedialog.asksaveasfilename(parent=self,defaultextension='.xlsx',filetypes=[('Excel','*.xlsx'),('스프레드시트 CSV','*.csv'),('기존 JSON','*.json')],initialfile='투자계산기-자산.xlsx')
        if path:
            try:export_file(path,self.data)
            except Exception as e:messagebox.showerror('저장 실패',str(e),parent=self)

    def import_data(self):
        from asset_files import import_file
        path=filedialog.askopenfilename(parent=self,filetypes=[('Excel / CSV / JSON','*.xlsx *.csv *.json')])
        if not path:return
        try:
            data=validate(import_file(path))
            if messagebox.askyesno('자산 자료 가져오기',f"종목 {len(data['holdings'])}개, 예수금 {Decimal(data['cash']):,.0f}원입니다. 현재 내 자산을 교체할까요?",parent=self):
                self.persist(data);self.show('assets')
        except Exception as e:messagebox.showerror('자료 확인',str(e),parent=self)

if __name__=='__main__':
    import ctypes
    try:ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('mikunoi.InvestmentCalculator')
    except (AttributeError,OSError):pass
    try:ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:pass
    App().mainloop()






