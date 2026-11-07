from i18n import tr
"""Display-only allocation scenarios using the dashboard snapshot."""
import tkinter as tk
import math
from tkinter import ttk, filedialog, messagebox
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from PIL import Image, ImageDraw, ImageTk
from average_cost import PALETTES, Card, SoftButton, NumberField, number
from chart_palette import COLORS
import dashboard_theme as theme
from scroll_support import SlimScrollbar
from allocation_media import hatch_sector, preview, format_money

ZERO = Decimal(0)

def cash_adjustment(raw):
    value=Decimal(str(raw or 0).replace(',','').strip())
    if not value.is_finite():raise ValueError(tr('예수금 조정에 유효한 숫자를 입력해 주세요.'))
    return value


def evaluation_capital(data):
    if data.get('fx_missing'):raise ValueError(tr('해외자산이 있습니다. 현재 환율(1 USD당 원)을 입력하고 적용해 주세요.'))
    return sum((number(h.get('evaluation_krw')) for h in data.get('holdings', [])), ZERO) + number(data.get('cash'))


def scenario(data, plans, extra, basis='evaluation', _funded=False):
    """Apply valuation targets; purchases/sales settle against cash."""
    capital = evaluation_capital(data) + cash_adjustment(extra)
    cash = number(data.get('cash')) + cash_adjustment(extra)
    if capital <= 0:
        raise ValueError(tr('총 운용자금을 확인해 주세요.'))
    rows = []
    for index, item in enumerate(data.get('holdings', [])):
        book = number(item.get('krw'))
        value = number(item.get('evaluation_krw'))
        rows.append(dict(key=('holding', index), name=item.get('name') or item.get('symbol') or tr('이름 없음'),
                         symbol=item.get('symbol') or '', purchase=book, evaluation=value, changed=False))
    current = {row['key']: row for row in rows}
    results = []
    key_field = 'evaluation'
    for plan in plans:
        if plan['kind'] not in ('percent','amount'):raise ValueError(tr('목표 유형이 올바르지 않습니다.'))
        value=number(plan['value'])
        if plan['kind']=='percent' and value>100:raise ValueError(tr('목표 비중은 100% 이하여야 합니다.'))
        target = capital * plan['value'] / 100 if plan['kind'] == 'percent' else plan['value']
        if target > capital:
            raise ValueError(f"{plan['name']}{tr('의 목표 금액이 계산 기준 운용자금을 초과합니다.')}")
        row = current.get(plan['key'])
        if row is None:
            row = dict(key=plan['key'], name=plan['name'], symbol=plan['symbol'], purchase=ZERO, evaluation=ZERO, changed=False)
            rows.append(row)
            current[plan['key']] = row
        target_basis = 'evaluation'
        before = row[target_basis]
        delta = target - before
        if delta >= 0:
            row['purchase'] += delta
            row['evaluation'] += delta
        elif before:
            # A partial sale removes the same fraction of cost and current valuation.
            factor = target / before
            delta = -row['evaluation'] * (1-factor)
            row['purchase'] *= factor
            row['evaluation'] *= factor
        cash -= delta
        row['changed'] = True
        results.append(dict(key=row['key'], name=row['name'], symbol=row['symbol'], before=before, target=target, delta=delta, weight=target / capital * 100, basis=target_basis))
    deficit = max(ZERO, -cash)
    percent_sum = sum((plan['value']/100 for plan in plans if plan['kind']=='percent'), ZERO)
    funding = ZERO
    if deficit:
        funding = (deficit/(1-percent_sum)).to_integral_value(rounding=ROUND_CEILING) if percent_sum<1 else None
    if funding and not _funded:
        funded_capital,_,funded_rows,funded_results=scenario(data,plans,cash_adjustment(extra)+funding,basis,True)
        cash_row=next(r for r in funded_rows if r['key']==('cash',))
        cash_row['funding']=funding
        cash_row['funded_capital']=funded_capital
        # Keep the unfunded cash balance for the warning, but show the completed funding scenario.
        return capital,cash,funded_rows,funded_results
    for row in rows:row['shortfall'] = ZERO
    rows.append(dict(key=('cash',), name=tr('현금'), symbol='', purchase=max(ZERO,cash), evaluation=max(ZERO,cash),
                     changed=False, shortfall=ZERO, funding=funding, funded_capital=capital))
    total = sum((row[key_field] for row in rows), ZERO)
    for row in rows:
        row['weight'] = row[key_field] / total * 100 if total else ZERO
    return capital, cash, rows, results


class AllocationView(tk.Frame):
    _owns_theme = True

    def __init__(self, parent, provider, fx_saver=None):
        self.p = PALETTES.get(theme.CURRENT, PALETTES['default'])
        super().__init__(parent, bg=self.p['page'])
        self.provider, self.data, self.holdings, self.plans = provider, {}, [], []
        self.fx_saver=fx_saver
        self.fx=tk.StringVar(value='')
        self.editing_key = None
        self.busy = False
        self.direction = 'percent'
        self.percent = tk.StringVar(value='')
        self.amount = tk.StringVar(value='')
        self.extra = tk.StringVar(value='')
        self.new_name = tk.StringVar(value='')
        self.new_code = tk.StringVar(value='')
        self.basis = tk.StringVar(value='evaluation')
        heading=tk.Frame(self,bg=self.p['page']);heading.pack(fill='x',pady=(2,3))
        self.label(heading, tr('비중계산'), 23, bold=True).pack(side='left')
        SoftButton(heading,tr('이미지 저장'),self.save_image,self.p,primary=True,width=130,height=40).pack(side='right')
        import goal_history
        SoftButton(heading,tr('목표 불러오기'),lambda:goal_history.load(self),self.p,width=135,height=40).pack(side='right',padx=5)
        SoftButton(heading,tr('목표 저장'),lambda:goal_history.save(self),self.p,width=110,height=40).pack(side='right')
        self.label(self, tr('추가 자금과 종목별 목표를 입력해 예상 포트폴리오를 살펴보세요.'), 12, muted=True).pack(anchor='w', pady=(0, 14))
        columns = tk.Frame(self, bg=self.p['page']); columns.pack(fill='both', expand=True)
        columns.columnconfigure(0, weight=1, uniform='columns'); columns.columnconfigure(1, weight=1, uniform='columns')
        left = tk.Frame(columns, bg=self.p['page']); left.grid(row=0, column=0, sticky='nsew', padx=(0, 8))
        right = tk.Frame(columns, bg=self.p['page']); right.grid(row=0, column=1, sticky='nsew', padx=(8, 0))
        self.columns,self.left,self.right,self.narrow=columns,left,right,None
        self.bind('<Configure>',self.responsive)
        capital_card = Card(left, self.p); capital_card.pack(fill='x', pady=(0, 12))
        body = capital_card.body
        self.capital_label = self.label(body, tr('현재 운용자금 평가액 확인 중'), 16, bold=True); self.capital_label.pack(anchor='w', pady=(8, 4))
        fxrow=tk.Frame(body,bg=self.p['card']);fxrow.pack(fill='x',pady=(4,8))
        self.label(fxrow,tr('현재 환율 · 1 USD ='),11,muted=True).pack(side='left')
        fxentry=ttk.Entry(fxrow,textvariable=self.fx,width=14);fxentry.pack(side='left',padx=8)
        fxentry.bind('<KeyRelease>',lambda e:format_money(fxentry,self.fx))
        self.label(fxrow,tr('원'),11,muted=True).pack(side='left')
        SoftButton(fxrow,tr('환율 적용'),self.apply_fx,self.p,width=100,height=36).pack(side='right')
        row = tk.Frame(body, bg=self.p['card']); row.pack(fill='x')
        self.label(row, tr('예수금 조정 (+입금 / -출금)'), 11, muted=True).pack(anchor='w', pady=(2, 3))
        extra_field=NumberField(row, self.extra, tr('원'), self.p);extra_field.pack(fill='x')
        extra_field.entry.bind('<KeyRelease>',lambda e:format_money(extra_field.entry,self.extra),add='+')
        self.total_label = self.label(body, '', 11, muted=True); self.total_label.pack(anchor='w', pady=(5, 0))
        SoftButton(body,tr('부족액 반영'),self.apply_funding,self.p,width=135,height=38).pack(anchor='e',pady=(4,0))
        SoftButton(body, tr('자료 갱신 · 목표 초기화'), self.refresh, self.p, width=205, height=38).pack(anchor='e', pady=(4, 0))
        form = Card(left, self.p); form.pack(fill='x', pady=(0, 12)); body = form.body
        self.label(body, tr('02  계산할 종목과 목표'), 15, bold=True).pack(anchor='w', pady=(0, 8))
        style = ttk.Style(self)
        style.configure('Allocation.TCombobox', padding=8, fieldbackground=self.p['field'], background=self.p['field'], foreground=self.p['text'], arrowcolor=self.p['muted'])
        style.map('Allocation.TCombobox', fieldbackground=[('readonly',self.p['field'])], foreground=[('readonly',self.p['text'])])
        self.choices = ttk.Combobox(body, state='readonly', style='Allocation.TCombobox', font=('맑은 고딕',11))
        self.choices.pack(fill='x'); self.choices.bind('<<ComboboxSelected>>', self.choice_changed)
        popup=self.choices.tk.call('ttk::combobox::PopdownWindow',self.choices)
        self.choices.tk.call(str(popup)+'.f.l','configure','-font',('맑은 고딕',11),'-background',self.p['field'],'-foreground',self.p['text'],'-selectbackground',self.p['soft'],'-selectforeground',self.p['text'])
        self.new_frame = tk.Frame(body, bg=self.p['card'])
        self.new_frame.columnconfigure((0, 1), weight=1)
        for column, (title, variable) in enumerate(((tr('새 종목명'), self.new_name), (tr('종목코드 (선택)'), self.new_code))):
            cell=tk.Frame(self.new_frame,bg=self.p['card']);cell.grid(row=0,column=column,sticky='ew',padx=(0,6) if column==0 else (6,0))
            self.label(cell,title,10,muted=True).pack(anchor='w')
            tk.Entry(cell,textvariable=variable,bg=self.p['field'],fg=self.p['text'],insertbackground=self.p['text'],relief='flat',font=('맑은 고딕',12)).pack(fill='x',ipady=7)
        self.current_label = self.label(body, '', 10, muted=True); self.current_label.pack(anchor='w', pady=(5, 8))
        fields = tk.Frame(body, bg=self.p['card']); fields.pack(fill='x'); fields.columnconfigure((0,1),weight=1,uniform='inputs')
        for i,title,var,unit in ((0,tr('목표 비중'),self.percent,'%'),(1,tr('목표 금액'),self.amount,tr('원'))):
            cell=tk.Frame(fields,bg=self.p['card']);cell.grid(row=0,column=i,sticky='ew',padx=(0,6) if i==0 else (6,0))
            self.label(cell,title,10,muted=True).pack(anchor='w',pady=(0,3))
            field=NumberField(cell,var,unit,self.p);field.pack(fill='x')
            if unit==tr('원'):field.entry.bind('<KeyRelease>',lambda e,w=field.entry,v=var:format_money(w,v),add='+')
        actions=tk.Frame(body,bg=self.p['card']);actions.pack(fill='x',pady=(8,0))
        self.form_status=self.label(actions,'',10,muted=True,wraplength=300);self.form_status.pack(side='left',fill='x',expand=True)
        self.plan_button=SoftButton(actions,tr('+ 목표 추가'),self.add_plan,self.p,primary=True,width=120,height=40)
        self.plan_button.pack(side='right')
        result = Card(left,self.p);result.pack(fill='x');body=result.body
        self.label(body,tr('03  종목별 목표 금액'),15,bold=True).pack(anchor='w',pady=(0,6))
        self.label(body,tr('행을 더블클릭하면 목표를 수정할 수 있습니다.'),10,muted=True).pack(anchor='w')
        self.target_warning=self.label(body,'',11,wraplength=560)
        self.target_warning.configure(fg='#E5484D')
        funding_line=tk.Frame(body,bg=self.p['card']);self.funding_line=funding_line
        self.funding_prefix=self.label(funding_line,tr('경고: 예수금 부족 · 목표비중 유지에 '),11)
        self.funding_prefix.configure(fg='#E5484D');self.funding_prefix.pack(side='left')
        self.funding_amount=self.label(funding_line,tr('0원'),11,bold=True)
        self.funding_amount.configure(fg='#D9BE68' if theme.CURRENT!='toss' else '#997313')
        self.funding_amount.pack(side='left')
        self.funding_suffix=self.label(funding_line,tr(' 추가 입금이 필요합니다.'),11)
        self.funding_suffix.configure(fg='#E5484D');self.funding_suffix.pack(side='left')
        result_frame=tk.Frame(body,bg=self.p['card']);result_frame.pack(fill='x')
        self.result_list=tk.Listbox(result_frame,height=6,bg=self.p['field'],fg=self.p['text'],selectbackground=self.p['soft'],selectforeground=self.p['text'],font=('맑은 고딕',11),bd=0,highlightthickness=0,exportselection=False)
        self.result_list.bind('<Double-Button-1>',self.edit_plan)
        self.enable_inner_scroll(self.result_list)
        result_scroll=SlimScrollbar(result_frame,orient='vertical',command=self.result_list.yview);self.result_list.configure(yscrollcommand=result_scroll.set)
        result_horizontal=SlimScrollbar(result_frame,orient='horizontal',command=self.result_list.xview)
        self.result_list.configure(xscrollcommand=result_horizontal.set);result_horizontal.pack(side='bottom',fill='x')
        result_scroll.pack(side='right',fill='y');self.result_list.pack(fill='both',expand=True)
        SoftButton(body,tr('선택한 목표 삭제'),self.remove_plan,self.p,width=155,height=38).pack(anchor='e',pady=(7,0))
        chart_card=Card(right,self.p);chart_card.pack(fill='x',pady=(0,12));body=chart_card.body
        top=tk.Frame(body,bg=self.p['card']);top.pack(fill='x')
        self.label(top,tr('04  예상 비중 차트'),15,bold=True).pack(side='left')
        self.label(top,tr('평가금액 기준'),10,muted=True).pack(side='right')
        self.chart=tk.Canvas(body,height=280,bg=self.p['card'],highlightthickness=0);self.chart.pack(fill='x',pady=(3,0));self.chart.bind('<Configure>',lambda e:self.draw_chart())
        self.chart.bind('<Button-1>',self.chart_click)
        self.chart.bind('<Motion>',self.chart_hover)
        self.chart.bind('<Leave>',lambda e:self.chart.delete('shortfall_tip'))
        self.chart_note=self.label(body,'',10,muted=True,wraplength=520);self.chart_note.pack(anchor='w')
        def bind_blank(widget):
            if widget is self.chart:return
            if isinstance(widget,(tk.Frame,tk.Label,tk.Canvas)) and not isinstance(widget,SoftButton):
                widget.bind('<Button-1>',self.clear_chart_selection)
                for child in widget.winfo_children():bind_blank(child)
        bind_blank(chart_card)
        legend=Card(right,self.p);legend.pack(fill='x');body=legend.body
        self.label(body,tr('05  차트 범례'),15,bold=True).pack(anchor='w',pady=(0,7))
        legend_frame=tk.Frame(body,bg=self.p['card']);legend_frame.pack(fill='both',expand=True)
        style.configure('Allocation.Treeview',background=self.p['card'],fieldbackground=self.p['card'],foreground=self.p['text'],rowheight=34,font=('맑은 고딕',11),borderwidth=0)
        style.configure('Allocation.Treeview.Heading',background=self.p['field'],foreground=self.p['muted'],font=('맑은 고딕',10),padding=6)
        style.layout('Allocation.Treeview',[('Treeview.treearea',{'sticky':'nswe'})])
        style.layout('Allocation.Treeview.Heading',[('Treeheading.padding',{'sticky':'nswe','children':[('Treeheading.text',{'sticky':'we'})]})])
        cols=('symbol','name','purchase','evaluation','target','weight')
        self.legend_cell_labels=[];self.legend_cell_colors={};self.legend_paint_job=None
        self.legend=ttk.Treeview(legend_frame,columns=cols,show='tree headings',height=7,selectmode='browse',style='Allocation.Treeview')
        self.legend.heading('#0',text='');self.legend.column('#0',width=28,minwidth=28,stretch=False)
        self.selected_key=None;self.legend_keys={}
        self.legend.bind('<<TreeviewSelect>>',self.select_legend)
        self.legend.bind('<Button-1>',self.toggle_legend)
        self.name_tip=None;self.name_tip_item=None
        self.legend.bind('<Motion>',self.show_name_tip)
        self.legend.bind('<Leave>',lambda e:self.hide_name_tip())
        self.legend.bind('<Configure>',lambda e:(self.hide_name_tip(),self.schedule_legend_colors()))
        self.bind('<Destroy>',self.cleanup_legend,add='+')
        style.map('Allocation.Treeview',background=[('selected',self.p['button'])],foreground=[('selected','#FFFFFF')])
        self.enable_inner_scroll(self.legend)
        for col,title,width in zip(cols,(tr('종목코드'),tr('종목명'),tr('매입금액'),tr('평가금액'),tr('목표금액'),tr('비중')),(78,140,100,100,100,75)):
            self.legend.heading(col,text=title);self.legend.column(col,width=width,minwidth=60,anchor='center' if col=='symbol' else 'w' if col=='name' else 'e')
        bar=SlimScrollbar(legend_frame,orient='vertical',command=self.legend.yview)
        self.legend.configure(yscrollcommand=lambda first,last:(self.hide_name_tip(),bar.set(first,last),self.schedule_legend_colors()))
        horizontal=SlimScrollbar(legend_frame,orient='horizontal',command=self.legend.xview)
        self.legend.configure(xscrollcommand=lambda first,last:(self.hide_name_tip(),horizontal.set(first,last),self.schedule_legend_colors()))
        horizontal.pack(side='bottom',fill='x');bar.pack(side='right',fill='y');self.legend.pack(fill='both',expand=True)
        self.label(body,tr('매입·평가: 현재 자산 · 목표금액·비중: 목표 반영 후'),10,muted=True).pack(anchor='w',pady=(6,0))
        self.label(self,tr('시뮬레이션 전용 · 수수료와 세금 제외 · 실제 주문이나 계좌에 반영되지 않습니다.'),10,muted=True).pack(anchor='w',pady=(10,12))
        self.percent.trace_add('write',lambda *a:self.convert('percent'))
        self.amount.trace_add('write',lambda *a:self.convert('amount'))
        self.extra.trace_add('write',lambda *a:self.update_all())
        self.refresh()

    def apply_funding(self):
        try:
            _,_,rows,_=scenario(self.data,self.plans,self.extra.get())
            funding=next(r['funding'] for r in rows if r['key']==('cash',))
            if funding is None:
                messagebox.showwarning(tr('목표 조정 필요'),tr('추가 입금만으로 목표를 충족할 수 없습니다. 목표 비중을 줄여 주세요.'),parent=self.winfo_toplevel())
                return
            if funding>0:
                self.extra.set(f"{cash_adjustment(self.extra.get())+funding:,f}")
        except (ValueError,InvalidOperation,TypeError) as error:
            messagebox.showerror(tr('입력 확인'),str(error),parent=self.winfo_toplevel())

    def save_image(self):
        from datetime import datetime
        from allocation_export import render
        try:
            capital,cash,rows,results=scenario(self.data,self.plans,self.extra.get(),self.basis.get())
            if not rows:raise ValueError(tr('저장할 자료가 없습니다.'))
            image=render(self.data,cash_adjustment(self.extra.get()),capital,rows,results,self.basis.get(),self.p,theme.CURRENT)
            preview(self,image,self.p)
        except Exception as error:
            messagebox.showerror(tr('이미지 저장 실패'),str(error),parent=self.winfo_toplevel())

    def label(self,parent,text='',size=11,bold=False,muted=False,**kw):
        return tk.Label(parent,text=text,bg=parent.cget('bg'),fg=self.p['muted' if muted else 'text'],font=('맑은 고딕',size,'bold' if bold else 'normal'),anchor='w',justify='left',**kw)

    def enable_inner_scroll(self, widget):
        tag='AllocationInnerScroll'+str(widget)
        widget.bindtags((tag,)+widget.bindtags())
        widget.bind_class(tag,'<MouseWheel>',lambda event:(widget.yview_scroll(-1 if event.delta>0 else 1,'units'),'break')[1])
        widget.bind('<Destroy>',lambda event:widget.unbind_class(tag,'<MouseWheel>') if event.widget==widget else None,add='+')

    def responsive(self,event):
        narrow=event.width<1050
        if narrow==self.narrow:return
        self.narrow=narrow
        self.columns.columnconfigure(1,weight=0 if narrow else 1)
        self.left.grid_configure(row=0,column=0,columnspan=2 if narrow else 1,padx=0 if narrow else (0,8))
        self.right.grid_configure(row=1 if narrow else 0,column=0 if narrow else 1,columnspan=2 if narrow else 1,padx=0 if narrow else (8,0),pady=(12,0) if narrow else 0)

    def apply_fx(self):
        try:
            from portfolio_data import validate
            proposal=dict(self.data,fx=self.fx.get())
            updated=validate(proposal)
            if self.fx_saver and not getattr(self,'snapshot',False):self.fx_saver(self.fx.get())
            self.data=updated;self.holdings=list(updated['holdings']);self.update_all()
        except (ValueError,InvalidOperation) as error:
            messagebox.showerror(tr('환율 입력'),str(error),parent=self.winfo_toplevel())

    def refresh(self):
        self.snapshot=False
        self.data=self.provider() or {}
        self.fx.set(self.data.get('fx',''))
        self.holdings=list(self.data.get('holdings',[]));self.plans=[];self.selected_key=None
        self.finish_edit()
        self.busy=True
        self.percent.set('');self.amount.set('');self.direction='percent'
        self.busy=False
        labels=[tr('새 종목 직접 입력')]
        for row in self.holdings:
            broker=tr('해외') if row.get('market')=='us' else tr('국내')
            labels.append(f"{broker} · {row.get('name') or row.get('symbol','')}"+(f" ({row['symbol']})" if row.get('symbol') else ''))
        self.choices.config(values=labels);self.choices.current(0)
        self.choice_changed();self.update_all()

    def choice_changed(self,event=None):
        if event is not None:self.finish_edit()
        if self.choices.current()==0:
            self.new_frame.pack(after=self.choices,fill='x',pady=(7,0))
            self.current_label.config(text=tr('새 종목명과 선택적인 코드를 입력해 주세요.'))
        else:
            self.new_frame.pack_forget()
            item=self.holdings[self.choices.current()-1]
            try:self.current_label.config(text=f"{tr('현재 매입 ')}{number(item.get('krw')):,.0f}{tr('원 · 평가 ')}{number(item.get('evaluation_krw')):,.0f}{tr('원')}")
            except (InvalidOperation,ValueError,TypeError):self.current_label.config(text=tr('현재 매입액 또는 평가액 확인 필요'))

    def capital(self):
        base=evaluation_capital(self.data);extra=cash_adjustment(self.extra.get())
        if base<=0:raise ValueError(tr('대시보드 운용자금을 확인해 주세요.'))
        if self.plans:
            _,_,rows,_=scenario(self.data,self.plans,extra)
            return next(r.get('funded_capital',base+extra) for r in rows if r['key']==('cash',))
        return base+extra

    def convert(self,direction):
        if self.busy:return
        self.direction=direction;self.busy=True
        try:
            raw=self.percent.get() if direction=='percent' else self.amount.get()
            if not raw.strip():
                (self.amount if direction=='percent' else self.percent).set('')
                self.form_status.config(text=tr('목표 비중 또는 금액을 입력해 주세요.'))
                return
            capital=self.capital()
            value=number(self.percent.get() if direction=='percent' else self.amount.get())
            if direction=='percent':
                if value>100:raise ValueError(tr('비중은 0~100%로 입력해 주세요.'))
                self.amount.set(f'{capital*value/100:,.2f}')
            else:
                if value>capital:raise ValueError(tr('금액이 계산 기준 운용자금을 초과합니다.'))
                self.percent.set(f'{value/capital*100:.2f}')
            self.form_status.config(text=(tr('매입액') if self.basis.get()=='purchase' else tr('평가액'))+tr(' 목표 · 같은 종목은 갱신됩니다.'))
        except (InvalidOperation,ValueError,TypeError) as error:
            (self.amount if direction=='percent' else self.percent).set('')
            self.form_status.config(text=str(error) if isinstance(error,ValueError) else tr('0 이상의 숫자를 입력해 주세요.'))
        finally:self.busy=False

    def add_plan(self):
        try:
            capital=self.capital();kind=self.direction
            value=number(self.percent.get() if kind=='percent' else self.amount.get())
            if value>(100 if kind=='percent' else capital):raise ValueError(tr('목표가 계산 기준 운용자금을 초과합니다.'))
            index=self.choices.current()-1
            if index<0:
                name=self.new_name.get().strip();symbol=self.new_code.get().strip()
                if not name:raise ValueError(tr('새 종목명을 입력해 주세요.'))
                key=('new',name.casefold(),symbol.casefold())
            else:
                row=self.holdings[index];name=row.get('name') or row.get('symbol') or tr('이름 없음');symbol=row.get('symbol') or '';key=('holding',index)
            plan=dict(key=key,name=name,symbol=symbol,kind=kind,value=value,basis=self.basis.get())
            # A selected holding has one target; adding it again replaces its target.
            replace_key=self.editing_key if self.editing_key is not None else key
            proposed=[];inserted=False
            for old in self.plans:
                if old['key']==replace_key:
                    proposed.append(plan);inserted=True
                elif old['key']!=key:proposed.append(old)
            if not inserted:proposed.append(plan)
            scenario(self.data,proposed,self.extra.get(),self.basis.get())
            self.plans=proposed;self.finish_edit();self.update_all()
        except (InvalidOperation,ValueError,TypeError) as error:
            self.form_status.config(text=str(error) if isinstance(error,ValueError) else tr('입력값과 계좌 자료를 확인해 주세요.'))

    def finish_edit(self):
        self.editing_key=None
        self.plan_button.title=tr('+ 목표 추가');self.plan_button.draw()

    def edit_plan(self,event):
        index=self.result_list.nearest(event.y)
        box=self.result_list.bbox(index)
        if not box or not box[1]<=event.y<box[1]+box[3] or index>=len(self.plans):return 'break'
        plan=self.plans[index]
        self.editing_key=plan['key']
        self.choices.current(plan['key'][1]+1 if plan['key'][0]=='holding' else 0)
        self.new_name.set(plan['name']);self.new_code.set(plan['symbol'])
        self.choice_changed()
        self.busy=True
        try:
            self.direction=plan['kind']
            (self.percent if plan['kind']=='percent' else self.amount).set(format(plan['value'],'f'))
        finally:self.busy=False
        self.convert(plan['kind'])
        self.plan_button.title=tr('목표 수정');self.plan_button.draw()
        self.form_status.config(text=tr('수정 중 · 목표 수정 버튼을 누르면 반영됩니다.'))
        self.choices.focus_set()
        return 'break'

    def remove_plan(self):
        selected=self.result_list.curselection()
        if selected:
            del self.plans[selected[0]];self.finish_edit();self.update_all()

    def update_all(self):
        self.hide_name_tip()
        self.convert(self.direction)
        try:
            capital,cash,rows,results=scenario(self.data,self.plans,self.extra.get(),self.basis.get())
            display_capital=next(r.get('funded_capital',capital) for r in rows if r['key']==('cash',))
            target_percent=sum((r['target'] for r in results),ZERO)/display_capital*100
            portfolio_percent=sum((r['evaluation'] for r in rows if r['key'] not in (('cash',),('funding',))),ZERO)/display_capital*100
            warning=(f"{tr('경고: 목표 합계 ')}{target_percent:.4f}{tr('% · 100% 초과 (')}{sum((r['target'] for r in results), ZERO) - capital:,.2f}{tr('원)')}" if target_percent>100 else
                     f"{tr('경고: 미설정 보유종목 포함 ')}{portfolio_percent:.4f}{tr('% · 자금 ')}{max(ZERO, -cash):,.2f}{tr('원 초과. 부족액 반영을 눌러 주세요.')}" if portfolio_percent>100 else '')
            self.target_warning.config(text=warning)
            self.target_warning.pack_forget()
            if warning:self.target_warning.pack(before=self.result_list.master,anchor='w',pady=(4,6))
            self.capital_label.config(text=f"{tr('조정 후 운용자금 평가액  ') if cash_adjustment(self.extra.get()) else tr('현재 운용자금 평가액  ')}{capital:,.0f}{tr('원')}")
            funding=next(r['funding'] for r in rows if r['key']==('cash',))
            self.funding_line.pack_forget()
            if cash<0 and funding is not None:
                self.funding_amount.config(text=f"{funding:,.0f}{tr('원')}")
                self.funding_line.pack(before=self.result_list.master,fill='x',pady=(4,6))
            elif cash<0:
                self.target_warning.config(text=tr('경고: 추가 입금만으로 목표비중을 유지할 수 없습니다. 목표를 줄여 주세요.'))
                self.target_warning.pack(before=self.result_list.master,anchor='w',pady=(4,6))
            cash_text=(f"{tr('예상 예수금 ')}{cash:,.0f}{tr('원')}" if cash>=0 else
                       tr('추가 입금만으로 목표 유지 불가') if funding is None else f"{tr('목표비중 유지 필요 입금 ')}{funding:,.0f}{tr('원')}")
            self.total_label.config(text=f"{tr('계산 기준 합계 ')}{capital:,.0f}{tr('원  ·  ')}{cash_text}")
            self.result_list.delete(0,'end')
            for result in results:
                delta=result['delta'];action=tr('추가') if delta>0 else tr('축소') if delta<0 else tr('유지')
                label=tr('매입') if result['basis']=='purchase' else tr('평가')
                self.result_list.insert('end',f"{result['name']}  {label}{tr(' 목표 ')}{result['target']:,.0f}{tr('원 (')}{result['weight']:.2f}%) · {action} {abs(delta):,.0f}{tr('원')}")
                self.result_list.itemconfig('end',fg=('#159C65' if delta>0 else '#E5484D' if delta<0 else self.p['text']))
            self.rows=rows
            self.legend.delete(*self.legend.get_children())
            self.legend_icons=[];self.legend_keys={};self.legend_cell_colors={}
            if self.selected_key not in [r['key'] for r in self.rows]:self.selected_key=None
            for index,row in enumerate(self.rows):
                color=theme.chart_color(index,row['key']==('cash',),COLORS[index%len(COLORS)],theme.CURRENT)
                icon=Image.new('RGBA',(48,48));ImageDraw.Draw(icon).ellipse((6,6,42,42),fill=color)
                icon=ImageTk.PhotoImage(icon.resize((12,12),Image.Resampling.LANCZOS));self.legend_icons.append(icon)
                tag='row'+str(index)
                self.legend.tag_configure(tag,background=self.p['soft'] if row['changed'] else self.p['card'],foreground=self.p['text'])
                item=self.legend.insert('', 'end',image=icon,values=(row['symbol'] or '—',row['name'],f"{number(self.holdings[row['key'][1]].get('krw')) if row['key'][0]=='holding' else number(self.data.get('cash')) if row['key']==('cash',) else ZERO:,.0f}",f"{number(self.holdings[row['key'][1]].get('evaluation_krw')) if row['key'][0]=='holding' else number(self.data.get('cash')) if row['key']==('cash',) else ZERO:,.0f}",f"{row['evaluation']:,.0f}",f"{row['weight']:.2f}%"),tags=(tag,))
                self.legend_keys[item]=row['key']
                original=number(self.holdings[row['key'][1]].get('evaluation_krw')) if row['key'][0]=='holding' else number(self.data.get('cash')) if row['key']==('cash',) else ZERO
                self.legend_cell_colors[item]=('#159C65' if row['evaluation']>original else '#E5484D' if row['evaluation']<original else self.p['text'])
                if row['key']==self.selected_key:self.legend.selection_set(item)
            total=sum(row['purchase' if self.basis.get()=='purchase' else 'evaluation'] for row in rows)
            self.chart_note.config(text=((cash_text+f"{tr('\n필요 입금 반영 후 예상 포트폴리오 · 평가자산+현금 ')}{display_capital:,.0f}{tr('원')}" ) if cash<0 else f"{tr('차트 합계 ')}{total:,.0f}{tr('원 · 목표 비중은 평가자산+현금 ')}{capital:,.0f}{tr('원 기준\n현재 평가가격으로 거래하는 가정')}"))
            self.draw_chart();self.schedule_legend_colors()
        except (InvalidOperation,ValueError,TypeError) as error:
            self.total_label.config(text=str(error) if isinstance(error,ValueError) else tr('대시보드의 운용자금과 평가자료를 확인해 주세요.'))
            self.capital_label.config(text=tr('현재 운용자금 평가액 · 환율 입력 필요') if self.data.get('fx_missing') else tr('현재 운용자금 평가액  0원 · 내 자산에서 입력해 주세요.'))
            self.funding_line.pack_forget()
            self.target_warning.pack(before=self.result_list.master,anchor='w',pady=(4,6))
            self.target_warning.config(text=str(error) if isinstance(error,ValueError) else tr('입력값과 자료를 확인해 주세요.'))
            self.chart_note.config(text=str(error) if isinstance(error,ValueError) else tr('계산할 수 없는 상태입니다. 입력값과 자료를 확인해 주세요.'))
            self.rows=[];self.legend.delete(*self.legend.get_children());self.result_list.delete(0,'end');self.schedule_legend_colors()
            for plan in self.plans:self.result_list.insert('end',plan['name']+tr('  ·  계산 불가'))
            self.draw_chart()

    def hide_name_tip(self):
        if getattr(self,'name_tip',None) is not None:
            self.name_tip.destroy();self.name_tip=None
        self.name_tip_item=None

    def show_name_tip(self,event):
        item=self.legend.identify_row(event.y)
        if not item or self.legend.identify_column(event.x)!='#2' or self.legend.identify_region(event.x,event.y)!='cell':
            self.hide_name_tip();return
        if item==self.name_tip_item:return
        self.hide_name_tip()
        box=self.legend.bbox(item,'name')
        if not box:return
        name=self.legend.set(item,'name')
        if not name:return
        tip=tk.Toplevel(self);tip.withdraw();tip.overrideredirect(True)
        tip.transient(self.winfo_toplevel());tip.attributes('-topmost',True)
        tip_font_pixels=max(1,round(round(self.winfo_fpixels('12p')*0.60)*1.10))
        tk.Label(tip,text=name,font=('맑은 고딕',-tip_font_pixels),bg=self.p['field'],fg=self.p['text'],
                 padx=12,pady=8,wraplength=min(520,self.winfo_screenwidth()-40),justify='left',
                 highlightthickness=1,highlightbackground=self.p['line']).pack()
        tip.update_idletasks()
        x=self.legend.winfo_rootx()+box[0]
        y=self.legend.winfo_rooty()+box[1]-tip.winfo_reqheight()-6
        x=max(0,min(x,self.winfo_screenwidth()-tip.winfo_reqwidth()-8))
        if y<0:y=self.legend.winfo_rooty()+box[1]+box[3]+6
        tip.geometry(f'+{x}+{y}');tip.deiconify()
        self.name_tip=tip;self.name_tip_item=item

    def cleanup_legend(self,event):
        if event.widget!=self:return
        self.hide_name_tip()
        if self.legend_paint_job is not None:
            self.after_cancel(self.legend_paint_job);self.legend_paint_job=None

    def schedule_legend_colors(self):
        if self.legend_paint_job is None:
            self.legend_paint_job=self.after_idle(self.paint_legend_colors)

    def paint_legend_colors(self):
        self.legend_paint_job=None
        for label in self.legend_cell_labels:label.destroy()
        self.legend_cell_labels=[]
        for item in self.legend.get_children():
            color=self.legend_cell_colors.get(item,self.p['text'])
            selected=item in self.legend.selection()
            tags=self.legend.item(item,'tags')
            bg=self.p['button'] if selected else (self.legend.tag_configure(tags[0],'background') if tags else self.p['card'])
            for col in ('target','weight'):
                box=self.legend.bbox(item,col)
                if not box:continue
                x,y,w,h=box
                if x<0 or x+w>self.legend.winfo_width():continue
                label=tk.Label(self.legend,text=self.legend.set(item,col),fg=color,bg=bg,anchor='e',font=('맑은 고딕',11),padx=3,borderwidth=0)
                label.place(x=x,y=y,width=w,height=h)
                label.bind('<Button-1>',lambda e,i=item:self.click_legend_cell(i))
                label.bind('<MouseWheel>',lambda e:self.scroll_legend_cells(e))
                self.legend_cell_labels.append(label)

    def click_legend_cell(self,item):
        if item in self.legend.selection():self.legend.selection_remove(item)
        else:self.legend.selection_set(item);self.legend.focus(item)
        self.select_legend()
        return 'break'

    def scroll_legend_cells(self,event):
        self.legend.yview_scroll(-1 if event.delta>0 else 1,'units')
        return 'break'

    def toggle_legend(self,event):
        self.hide_name_tip()
        if self.legend.identify_region(event.x,event.y) not in ('tree','cell'):return
        item=self.legend.identify_row(event.y)
        if item and item in self.legend.selection():
            self.legend.selection_remove(item)
            self.selected_key=None;self.draw_chart()
            return 'break'
        if item:
            self.legend.focus_set();self.legend.focus(item)
            self.legend.selection_set(item);self.select_legend()
            return 'break'

    def select_legend(self,event=None):
        self.schedule_legend_colors()
        selected=self.legend.selection()
        key=self.legend_keys.get(selected[0]) if selected else None
        if key!=self.selected_key:
            self.selected_key=key;self.draw_chart()

    def clear_chart_selection(self,event=None):
        self.legend.selection_remove(*self.legend.selection())
        self.legend.focus('')
        if self.selected_key is not None:
            self.selected_key=None;self.draw_chart()
        return 'break'

    def chart_click(self,event):
        width=self.chart.winfo_width();height=self.chart.winfo_height()
        size=max(40,min(width-28,height-22))
        dx=event.x-width/2;dy=event.y-height/2
        if not size*.21<=math.hypot(dx,dy)<=size*.5:
            return self.clear_chart_selection()
        rows=getattr(self,'rows',[])
        field='purchase' if self.basis.get()=='purchase' else 'evaluation'
        total=sum((r[field] for r in rows if r[field]>0),ZERO)
        if not total:return self.clear_chart_selection()
        angle=(math.degrees(math.atan2(dy,dx))+90)%360
        end=0
        for row in rows:
            if row[field]<=0:continue
            end+=float(row[field]/total*360)
            if angle<end:
                for item,key in self.legend_keys.items():
                    if key==row['key']:
                        self.legend.selection_set(item);self.legend.focus(item);self.legend.see(item)
                        if self.selected_key!=key:
                            self.selected_key=key;self.draw_chart()
                        return 'break'
                break
        return self.clear_chart_selection()

    def chart_hover(self,event):
        self.chart.delete('shortfall_tip')
        width=self.chart.winfo_width();height=self.chart.winfo_height()
        size=max(40,min(width-28,height-22))
        dx=event.x-width/2;dy=event.y-height/2
        radius=math.hypot(dx,dy)
        if not size*.21<=radius<=size*.5:return
        angle=math.degrees(math.atan2(dy,dx))
        for start,extent,name,missing in getattr(self,'shortfall_hits',[]):
            if (angle-start)%360<=extent:
                x=width/2;y=8
                item=self.chart.create_text(x,y,text=f"{name}{tr('\n목표비중 유지 필요 입금 ')}{missing:,.0f}{tr('원')}",anchor='n',
                    width=max(80,width-24),fill=self.p['text'],font=('맑은 고딕',10),tags='shortfall_tip')
                box=self.chart.bbox(item)
                rect=self.chart.create_rectangle(box[0]-6,box[1]-4,box[2]+6,box[3]+4,fill=self.p['field'],outline=self.p['line'],tags='shortfall_tip')
                self.chart.tag_lower(rect,item)
                return

    def draw_chart(self):
        if not hasattr(self,'chart'):return
        self.chart.delete('all');self.shortfall_hits=[];rows=getattr(self,'rows',[])
        width=max(1,self.chart.winfo_width());height=max(1,self.chart.winfo_height())
        size=max(40,min(width-28,height-22));x=(width-size)/2;y=(height-size)/2
        key='purchase' if self.basis.get()=='purchase' else 'evaluation';total=sum((r[key] for r in rows),ZERO)
        if not total:
            self.chart.create_text(width/2,height/2,text=tr('차트 자료 확인 중'),fill=self.p['muted'],font=('맑은 고딕',12));return
        start=90
        labels=[]
        # Supersample only the donut tile, keeping native text sharp and memory bounded.
        scale=4
        tile_size=int(math.ceil(size))+4
        signature=(tile_size,self.p['card'],theme.CURRENT,self.selected_key,tuple((r[key],r['key']==('cash',),r.get('shortfall',ZERO)) for r in rows))
        redraw=signature!=getattr(self,'_donut_signature',None)
        if redraw:
            tile=Image.new('RGB',(tile_size*scale,tile_size*scale),self.p['card'])
            brush=ImageDraw.Draw(tile)
            bounds=(2*scale,2*scale,(2+size)*scale,(2+size)*scale)
        selected_slice=None
        for index,row in enumerate(rows):
            value=row[key]
            if value<=0:continue
            extent=float(value/total*360)
            color=theme.chart_color(index,row['key']==('cash',),COLORS[index%len(COLORS)],theme.CURRENT)
            if self.selected_key is not None and row['key']!=self.selected_key:
                color='#%02x%02x%02x'%tuple(round(int(color[i:i+2],16)*.38+int(self.p['card'][i:i+2],16)*.62) for i in (1,3,5))
            elif row['key']==self.selected_key:selected_slice=(-start,extent,color)
            if redraw:
                if extent>=359.999999:brush.ellipse(bounds,fill=color,outline=self.p['card'],width=scale)
                else:brush.pieslice(bounds,start=-start,end=-start+extent,fill=color,outline=self.p['card'],width=scale)
            missing=min(value,row.get('shortfall',ZERO))
            if missing>0:
                hatch_extent=float(missing/total*360)
                hatch_start=-start+extent-hatch_extent
                self.shortfall_hits.append((hatch_start,hatch_extent,row['name'],row['shortfall']))
            if extent>=18:
                angle=math.radians(start-extent/2)
                labels.append((width/2+size*.36*math.cos(angle),height/2-size*.36*math.sin(angle),f'{float(value/total):.0%}',color))
            start-=extent
        if redraw:
            if selected_slice:
                angle,extent,color=selected_slice
                if extent>=359.999999:brush.ellipse(bounds,fill=color,outline=self.p['accent'],width=3*scale)
                else:brush.pieslice(bounds,start=angle,end=angle+extent,fill=color,outline=self.p['accent'],width=3*scale)
            for angle,extent,name,missing in self.shortfall_hits:
                hatch_sector(tile,bounds,angle,extent,scale)
            inset=size*.29
            brush.ellipse(((2+inset)*scale,(2+inset)*scale,(2+size-inset)*scale,(2+size-inset)*scale),fill=self.p['card'])
            thumbnail=tile.resize((tile_size,tile_size),Image.Resampling.LANCZOS)
            self.chart_image=ImageTk.PhotoImage(thumbnail)
            thumbnail.close();tile.close()
            self._donut_signature=signature
        self.chart.create_image(x-2,y-2,image=self.chart_image,anchor='nw')
        self.chart.create_text(width/2,height/2-10,text=(tr('선택 종목') if self.selected_key is not None else tr('예상 비중')),fill=self.p['muted'],font=('맑은 고딕',11))
        self.chart.create_text(width/2,height/2+15,text=tr('매입 기준') if key=='purchase' else tr('평가 기준'),fill=self.p['text'],font=('맑은 고딕',12,'bold'))
        for tx,ty,label,color in labels:
            rgb=[int(color[i:i+2],16) for i in (1,3,5)]
            ink='#172332' if sum(a*b for a,b in zip(rgb,(.299,.587,.114)))>145 else '#FFFFFF'
            self.chart.create_text(tx,ty,text=label,fill=ink,font=('맑은 고딕',11,'bold'))


def build(app):
    view=AllocationView(app.content,lambda:app.data)
    view.pack(fill='both',expand=True,padx=(0,12))
    return view


