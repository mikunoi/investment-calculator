from i18n import tr
"""Local, orderless average-cost simulator with a self-contained visual theme."""
from decimal import Decimal, InvalidOperation
from datetime import datetime
from quantity import shares, display_shares
import tkinter as tk
from tkinter import ttk, messagebox


def number(raw):
    value = Decimal(str(raw).replace(',', '').strip())
    if not value.is_finite() or value < 0:
        raise ValueError(tr('0 이상의 숫자를 입력해 주세요.'))
    return value


def calculate(quantity, average, additions):
    quantity, average = shares(quantity), number(average)
    cost, added = quantity * average, Decimal(0)
    for price, count in additions:
        price, count = number(price), shares(count)
        if count and not price:
            raise ValueError(tr('매수 가격은 0보다 커야 합니다.'))
        added += price * count
        cost += price * count
        quantity += count
    if quantity <= 0:
        raise ValueError(tr('보유수량 또는 추가 매수 수량을 입력해 주세요.'))
    return quantity, cost, cost / quantity, added


PALETTES = {
    'default': dict(page='#031522', card='#102333', field='#192F41', line='#294256',
                    text='#F2F6FC', muted='#91A5B8', accent='#629CFF', button='#3275F5',
                    hover='#4889FF', soft='#183956', result='#122C46', good='#6CD9BE', error='#FFB394'),
    'white': dict(page='#FFFFFF', card='#F4F4F4', field='#FFFFFF', line='#D8D8D8',
                  text='#202020', muted='#666666', accent='#333333', button='#303030',
                  hover='#505050', soft='#E4E4E4', result='#EDEDED', good='#333333', error='#444444'),
    'matrix': dict(page='#031522', card='#0C2517', field='#153922', line='#2C5134',
                   text='#C6E8C0', muted='#7FA37D', accent='#96DB8D', button='#2C6437',
                   hover='#3B8048', soft='#1A4124', result='#10311B', good='#9FE78E', error='#D3DCA2'),
}

PALETTES['toss'] = dict(page='#F2F4F6', card='#FFFFFF', field='#F2F4F6', line='#D1D6DB', text='#191F28', muted='#6B7684', accent='#3182F6', button='#3182F6', hover='#1B64DA', soft='#E8F3FF', result='#FFFFFF', good='#159C82', error='#D94154')


def rounded(canvas, x1, y1, x2, y2, radius=16, **kwargs):
    r = min(radius, (x2-x1)/2, (y2-y1)/2)
    return canvas.create_polygon(x1+r,y1,x2-r,y1,x2,y1,x2,y1+r,
        x2,y2-r,x2,y2,x2-r,y2,x1+r,y2,x1,y2,x1,y2-r,x1,y1+r,x1,y1,
        smooth=True, splinesteps=24, **kwargs)


class Card(tk.Canvas):
    def __init__(self, parent, palette, fill=None):
        self.fill = fill or palette['card']
        super().__init__(parent, bg=palette['page'], highlightthickness=0, bd=0, height=100)
        self.body = tk.Frame(self, bg=self.fill)
        self.slot = self.create_window(22, 16, anchor='nw', window=self.body)
        self.layout_job=None
        self.bind('<Configure>', self.schedule_layout)
        self.body.bind('<Configure>', self.schedule_layout)
        self.bind('<Destroy>', self.cancel_layout, add='+')

    def schedule_layout(self,event=None):
        if self.layout_job is None:self.layout_job=self.after(20,self.layout)

    def cancel_layout(self,event):
        if event.widget is self and self.layout_job is not None:
            self.after_cancel(self.layout_job);self.layout_job=None

    def layout(self, event=None):
        self.layout_job=None
        width = max(80, self.winfo_width())
        if width!=getattr(self,'_layout_width',None):
            self._layout_width=width
            self.itemconfigure(self.slot, width=max(40, width-44))
        height = self.body.winfo_reqheight()+32
        if (width,height)==getattr(self,'_layout_size',None):return
        self._layout_size=(width,height)
        if int(self.cget('height')) != height:
            self.configure(height=height)
        self.delete('shape')
        rounded(self, 0, 0, width, height, fill=self.fill, outline='', tags='shape')
        self.tag_lower('shape')


class SoftButton(tk.Canvas):
    def __init__(self, parent, text, command, palette, primary=False, width=132, height=42):
        super().__init__(parent, width=width, height=height, bg=parent.cget('bg'),
                         bd=0, highlightthickness=0, cursor='hand2', takefocus=1)
        self.title, self.command, self.p, self.primary = text, command, palette, primary
        self.over = False
        self.bind('<Configure>', self.draw)
        self.bind('<Enter>', lambda e: self.hover(True))
        self.bind('<Leave>', lambda e: self.hover(False))
        self.bind('<FocusIn>', lambda e: self.hover(True))
        self.bind('<FocusOut>', lambda e: self.hover(False))
        self.bind('<ButtonRelease-1>', lambda e: self.invoke())
        self.bind('<Return>', lambda e: self.invoke())
        self.bind('<space>', lambda e: self.invoke())

    def hover(self, active):
        self.over = active
        self.draw()

    def draw(self, event=None):
        self.delete('all')
        fill = self.p['hover' if self.over else 'button'] if self.primary else self.p['line' if self.over else 'field']
        rounded(self, 0, 0, self.winfo_width(), self.winfo_height(), 12, fill=fill, outline='')
        self.create_text(self.winfo_width()/2, self.winfo_height()/2, text=self.title,
                         fill='#FFFFFF' if self.primary else self.p['text'], font=('맑은 고딕', 11, 'bold'))

    def invoke(self):
        self.command()


class NumberField(tk.Canvas):
    def __init__(self, parent, variable, unit, palette):
        super().__init__(parent, height=51, width=160, bg=parent.cget('bg'), bd=0, highlightthickness=0)
        self.p, self.focused = palette, False
        self.entry = tk.Entry(self, textvariable=variable, font=('맑은 고딕', 16), width=7,
            bg=palette['field'], fg=palette['text'], insertbackground=palette['accent'],
            selectbackground=palette['soft'], selectforeground=palette['text'], relief='flat', bd=0,
            highlightthickness=0, justify='right')
        self.unit = tk.Label(self, text=unit, font=('맑은 고딕', 11), bg=palette['field'], fg=palette['muted'])
        self.entry_slot = self.create_window(13, 25, anchor='w', window=self.entry)
        self.unit_slot = self.create_window(145, 25, anchor='e', window=self.unit)
        self.bind('<Configure>', self.draw)
        self.entry.bind('<FocusIn>', lambda e: self.focus(True))
        self.entry.bind('<FocusOut>', lambda e: self.focus(False))
        self.entry.bind('<Control-a>', lambda e: (self.entry.select_range(0, 'end'), 'break')[1])
        def commas(event):
            from allocation_media import format_money
            format_money(self.entry,variable)
        self.entry.bind('<KeyRelease>',commas,add='+')

    def focus(self, active):
        self.focused = active
        self.draw()

    def draw(self, event=None):
        width = max(80, self.winfo_width())
        unit_width = max(25, self.unit.winfo_reqwidth())
        self.itemconfigure(self.entry_slot, width=max(25, width-unit_width-34))
        self.coords(self.unit_slot, width-12, 25)
        self.delete('shape')
        rounded(self, 1, 1, width-1, 50, 10, fill=self.p['field'],
                outline=self.p['accent'] if self.focused else self.p['field'], width=2, tags='shape')
        self.tag_lower('shape')


class AverageCostView(tk.Frame):
    # The global legacy theme walker must not overwrite this page's typography or canvas palette.
    _owns_theme = True

    def __init__(self, parent, data_provider, theme_name='default'):
        self.p = dict(PALETTES.get(theme_name, PALETTES['default']))
        if theme_name == 'matrix':
            self.p['page'] = parent.cget('bg')
        super().__init__(parent, bg=self.p['page'])
        self.data_provider, self.holdings, self.rows = data_provider, [], []
        self.pending, self.loading, self.narrow = None, True, None
        self.currency = tk.StringVar(value=tr('원'))
        self.last_currency=tr('원')
        self.quantity, self.average = tk.StringVar(value='0'), tk.StringVar(value='0.00')
        self.price_fields = []
        self.create_page()
        self.quantity.trace_add('write', self.changed)
        self.average.trace_add('write', self.changed)
        self.currency.trace_add('write', self.changed_currency)
        self.add_row()
        self.refresh_holdings()
        self.loading = False
        self.show_empty()
        self.bind('<Configure>', self.responsive)
        self.bind('<Destroy>', self.on_destroy, add='+')

    def label(self, parent, text='', size=11, role='text', bold=False, **kwargs):
        return tk.Label(parent, text=text, bg=parent.cget('bg'), fg=self.p[role],
                        font=('맑은 고딕', size, 'bold' if bold else 'normal'), anchor='w', justify='left', **kwargs)

    def create_page(self):
        header = tk.Frame(self, bg=self.p['page'])
        header.pack(fill='x', pady=(2, 12))
        self.label(header, tr('투자 도구  /  평균단가 시뮬레이터'), 10, 'muted').pack(anchor='w')
        self.label(header, tr('추가 매수하면, 평단이 얼마나 바뀔까요?'), 21, bold=True).pack(anchor='w', pady=(4, 2))
        self.label(header, tr('내 보유종목으로 시작하고, 여러 매수 조건을 가볍게 비교해 보세요.'), 11, 'muted').pack(anchor='w')
        self.columns = tk.Frame(self, bg=self.p['page'])
        self.columns.pack(fill='x')
        self.columns.columnconfigure(0, weight=3, minsize=490)
        self.columns.columnconfigure(1, weight=2, minsize=330)
        self.left = tk.Frame(self.columns, bg=self.p['page'])
        self.right = tk.Frame(self.columns, bg=self.p['page'])
        self.left.grid(row=0, column=0, sticky='new', padx=(0, 20))
        self.right.grid(row=0, column=1, sticky='new')

        holding = Card(self.left, self.p)
        holding.pack(fill='x', pady=(0, 16))
        body = holding.body
        self.section(body, '01', tr('현재 보유정보'), tr('보유종목 선택 또는 직접 입력'))
        select_row = tk.Frame(body, bg=body.cget('bg'))
        select_row.pack(fill='x', pady=(10, 10))
        select_row.columnconfigure(0, weight=1)
        style = ttk.Style(self)
        style.configure('Average.TCombobox', padding=10, font=('맑은 고딕', 12),
                        fieldbackground=self.p['field'], foreground=self.p['text'], background=self.p['field'],
                        arrowcolor=self.p['muted'], borderwidth=0, relief='flat',
                        lightcolor=self.p['field'], darkcolor=self.p['field'], bordercolor=self.p['field'])
        style.map('Average.TCombobox', fieldbackground=[('readonly', self.p['field'])],
                  foreground=[('readonly', self.p['text'])], selectbackground=[('readonly', self.p['field'])],
                  selectforeground=[('readonly', self.p['text'])])
        self.choices = ttk.Combobox(select_row, state='readonly', style='Average.TCombobox',
                                    font=('맑은 고딕', 12), width=20)
        self.choices.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        self.choices.bind('<<ComboboxSelected>>', self.load_holding)
        SoftButton(select_row, tr('목록 갱신'), self.refresh_holdings, self.p, width=95).grid(row=0, column=1)
        fields = tk.Frame(body, bg=body.cget('bg'))
        fields.pack(fill='x')
        fields.columnconfigure((0, 1), weight=1, uniform='fields')
        for column, title, variable, unit in ((0, tr('보유수량'), self.quantity, tr('주')), (1, tr('현재 평균단가'), self.average, tr('원'))):
            cell = tk.Frame(fields, bg=body.cget('bg'))
            cell.grid(row=0, column=column, sticky='ew', padx=(0, 8) if column==0 else (8, 0))
            self.label(cell, title, 11, 'muted').pack(anchor='w', pady=(0, 8))
            field = NumberField(cell, variable, unit, self.p)
            field.pack(fill='x')
            if column==1:self.price_fields.append(field)
        details = tk.Frame(body, bg=body.cget('bg'))
        details.pack(fill='x', pady=(8, 0))
        self.source = self.label(details, tr('직접 입력 · 보유 정보를 입력해 주세요.'), 10, 'muted')
        self.source.pack(side='left', fill='x', expand=True)
        self.currency_choice = ttk.Combobox(details, textvariable=self.currency, values=(tr('원'),'USD'),
                    state='readonly', width=5, style='Average.TCombobox', font=('맑은 고딕', 10))
        self.currency_choice.pack(side='right')
        for combo in (self.choices, self.currency_choice):
            popup = combo.tk.call('ttk::combobox::PopdownWindow', combo)
            combo.tk.call(str(popup)+'.f.l', 'configure', '-font', ('맑은 고딕', 12),
                          '-background', self.p['field'], '-foreground', self.p['text'],
                          '-selectbackground', self.p['soft'], '-selectforeground', self.p['text'])

        scenario = Card(self.left, self.p)
        scenario.pack(fill='x')
        body = scenario.body
        self.section(body, '02', tr('추가 매수 시나리오'), tr('원하는 만큼 매수 회차를 추가하세요'))
        self.row_area = tk.Frame(body, bg=body.cget('bg'))
        self.row_area.pack(fill='x', pady=(12, 0))
        SoftButton(body, tr('＋  매수 회차 추가'), self.add_row, self.p, height=43).pack(fill='x', pady=(14, 0))
        self.label(body, tr('입력한 조건은 오른쪽 결과에 바로 반영됩니다.'), 10, 'muted').pack(anchor='w', pady=(13, 0))

        result = Card(self.right, self.p, self.p['result'])
        result.pack(fill='x')
        body = result.body
        self.label(body, 'SIMULATION', 10, 'accent', True).pack(anchor='w')
        self.label(body, tr('예상 평균단가'), 14, bold=True).pack(anchor='w', pady=(14, 4))
        self.average_result = self.label(body, '—', 30, bold=True)
        self.average_result.pack(anchor='w')
        self.delta = self.label(body, tr('조건을 입력하면 결과가 나타나요'), 11, 'muted')
        self.delta.pack(anchor='w', pady=(6, 12))
        tk.Frame(body, height=1, bg=self.p['line']).pack(fill='x')
        self.result_values = {}
        for key, title in (('quantity',tr('예상 총수량')),('added',tr('추가 필요금액')),('cost',tr('예상 총매입액'))):
            row = tk.Frame(body, bg=body.cget('bg'))
            row.pack(fill='x', pady=(12, 0))
            self.label(row, title, 11, 'muted').pack(side='left')
            value = self.label(row, '—', 13, bold=True)
            value.pack(side='right')
            self.result_values[key] = value
        self.comparison = tk.Canvas(body, bg=body.cget('bg'), height=108, highlightthickness=0)
        self.comparison.pack(fill='x', pady=(12, 0))
        self.comparison.bind('<Configure>', lambda e:self.draw_comparison())
        self.compare_values = None
        self.status = self.label(body, tr('수량과 가격을 입력해 주세요.'), 10, 'muted', wraplength=285)
        self.status.pack(anchor='w', pady=(12, 0))
        SoftButton(body, tr('다시 계산하기'), self.run, self.p, primary=True, height=46).pack(fill='x', pady=(18, 0))
        foot = tk.Frame(self.right, bg=self.p['page'])
        foot.pack(fill='x', padx=8, pady=18)
        self.label(foot, tr('계산 전에 확인해 주세요'), 11, bold=True).pack(anchor='w')
        self.label(foot, tr('수수료·세금은 제외한 예상값입니다.\n입력한 가격으로 전량 체결된다고 가정합니다.\n실제 계좌나 주문에는 반영되지 않습니다.'),
                   10, 'muted', wraplength=315).pack(anchor='w', pady=(8, 0))

    def section(self, parent, number_text, title, subtitle):
        row = tk.Frame(parent, bg=parent.cget('bg'))
        row.pack(fill='x')
        self.label(row, number_text, 11, 'accent', True).pack(side='left', padx=(0, 10))
        self.label(row, title, 15, bold=True).pack(side='left')
        self.label(parent, subtitle, 10, 'muted').pack(anchor='w', pady=(6, 0))

    def add_row(self):
        row = {'price':tk.StringVar(value='0.00'), 'quantity':tk.StringVar(value='0')}
        self.rows.append(row)
        frame = tk.Frame(self.row_area, bg=self.p['card'])
        row['frame'] = frame
        frame.pack(fill='x', pady=(6, 0))
        heading = tk.Frame(frame, bg=self.p['card'])
        heading.pack(fill='x', pady=(0, 4))
        row['label'] = self.label(heading, f"{len(self.rows):02d}{tr('차 매수')}", 11, bold=True)
        row['label'].pack(side='left')
        SoftButton(heading, tr('삭제'), lambda:self.remove_row(row), self.p, width=58, height=30).pack(side='right')
        fields = tk.Frame(frame, bg=self.p['card'])
        fields.pack(fill='x')
        fields.columnconfigure((0,1), weight=1, uniform='row')
        for column, key, title, unit in ((0,'quantity',tr('매수 수량'),tr('주')),(1,'price',tr('매수 가격'),self.currency.get())):
            cell = tk.Frame(fields, bg=self.p['card'])
            cell.grid(row=0, column=column, sticky='ew', padx=(0,8) if column==0 else (8,0))
            self.label(cell, title, 10, 'muted').pack(anchor='w', pady=(0,6))
            field = NumberField(cell, row[key], unit, self.p)
            field.pack(fill='x')
            if key=='price':
                row['field']=field
                self.price_fields.append(field)
            row[key].trace_add('write', self.changed)
        self.changed()

    def remove_row(self, row):
        self.rows.remove(row)
        self.price_fields.remove(row['field'])
        row['frame'].destroy()
        for index, remaining in enumerate(self.rows, 1):remaining['label'].configure(text=f"{index:02d}{tr('차 매수')}")
        self.changed()

    def changed(self, *args):
        if self.loading:return
        if self.pending:self.after_cancel(self.pending)
        self.pending = self.after(180, self.run)

    def changed_currency(self, *args):
        selected=self.currency.get()
        if not self.loading and selected!=self.last_currency:
            variables=[self.average]+[r['price'] for r in self.rows]
            try:
                prices=[number(v.get() or 0) for v in variables]
                if any(prices):
                    fx=number((self.data_provider() or {}).get('fx') or 0)
                    if fx<=0:raise ValueError(tr('비중계산에서 현재 환율을 먼저 입력해 주세요. 입력된 가격도 함께 환산합니다.'))
                    multiplier=fx if selected==tr('원') else 1/fx
                    self.loading=True
                    for variable,value in zip(variables,prices):variable.set(f'{value*multiplier:,.2f}')
                    self.loading=False
            except (ValueError,InvalidOperation) as error:
                self.loading=True;self.currency.set(self.last_currency);self.loading=False
                messagebox.showwarning(tr('통화 변경'),str(error),parent=self.winfo_toplevel());return
        self.last_currency=selected
        for field in self.price_fields:
            field.unit.configure(text=self.currency.get())
            field.draw()
        self.changed()

    def refresh_holdings(self):
        data = self.data_provider() or {}
        self.holdings = [dict(r) for r in data.get('holdings',[]) if not r.get('manual')
                         and number(r.get('quantity',0))>0 and r.get('purchase') is not None]
        labels = [tr('직접 입력으로 계산하기')]
        for row in self.holdings:
            broker = {'kiwoom':tr('키움'),'kis':tr('한투')}.get(row.get('broker'),tr('직접입력'))
            labels.append(f"{broker} · {row.get('name',row['symbol'])} ({row['symbol']})")
        self.choices.configure(values=labels)
        self.choices.current(0)
        self.load_holding()

    def load_holding(self, event=None):
        self.loading = True
        index = self.choices.current()
        for row in self.rows:
            row['price'].set('0.00');row['quantity'].set('0')
        self.quantity.set('0');self.average.set('0.00')
        self.currency_choice.configure(state='readonly')
        self.source.configure(text=tr('직접 입력 · 같은 통화로 가격을 입력하세요.'))
        if index>0:
            row = self.holdings[index-1]
            try:
                q, cost = number(row['quantity']), number(row['purchase'])
                if q<=0:raise ValueError()
                self.quantity.set(display_shares(q));self.average.set(f'{cost/q:,.2f}')
                self.currency.set('USD' if row.get('market')=='us' else tr('원'))
                self.currency_choice.configure(state='readonly')
                at = row.get('at','')
                try:at=datetime.fromisoformat(at).astimezone().strftime('%m.%d %H:%M')
                except (ValueError,TypeError):at=tr('시각 미확인')
                self.source.configure(text=f"{tr('보유자료 ')}{at}{tr(' 기준 · 매입액 ÷ 수량')}")
            except (ValueError,KeyError,InvalidOperation):
                self.source.configure(text=tr('보유수량·매입액 확인 필요 · 직접 입력 가능'))
        self.loading = False
        self.run()

    def money(self, value):
        return f"{value:,.2f} {('USD' if self.currency.get() == 'USD' else tr('원'))}"

    def show_empty(self, message=None, error=False):
        if message is None:message=tr('수량과 가격을 입력해 주세요.')
        self.average_result.configure(text='—')
        self.delta.configure(text=tr('조건을 입력하면 결과가 나타나요'), fg=self.p['muted'])
        for widget in self.result_values.values():widget.configure(text='—')
        self.status.configure(text=message, fg=self.p['error' if error else 'muted'])
        self.compare_values = None
        self.draw_comparison()

    def run(self):
        if self.pending:
            self.after_cancel(self.pending);self.pending=None
        try:
            q, cost, avg, added = calculate(self.quantity.get(), self.average.get(),
                [(r['price'].get(),r['quantity'].get()) for r in self.rows])
            old = number(self.average.get())
            self.average_result.configure(text=self.money(avg), font=('맑은 고딕', 27 if len(self.money(avg))<17 else 20,'bold'))
            if old:
                change = (avg/old-1)*100
                self.delta.configure(text=f"{tr('현재 평단 대비 ')}{change:+.2f}%", fg=self.p['good' if change<0 else 'accent'])
            else:self.delta.configure(text=tr('신규 매수 기준'), fg=self.p['accent'])
            self.result_values['quantity'].configure(text=f"{display_shares(q)}{tr('주')}")
            self.result_values['added'].configure(text=self.money(added))
            self.result_values['cost'].configure(text=self.money(cost))
            self.status.configure(text=tr('입력값 반영 완료 · 평균단가는 소수 2자리 기준'),fg=self.p['muted'])
            self.compare_values = old, avg
            self.draw_comparison()
        except (InvalidOperation,ValueError,ArithmeticError) as error:
            empty = self.quantity.get() in ('0','') and all(r['quantity'].get() in ('0','') for r in self.rows)
            self.show_empty(tr('수량과 가격을 입력해 주세요.') if empty else
                (str(error) if isinstance(error,ValueError) else tr('숫자 입력을 확인해 주세요.')), not empty)

    def draw_comparison(self):
        canvas = self.comparison
        canvas.delete('all')
        width = max(100,canvas.winfo_width())
        maximum = max(self.compare_values) if self.compare_values else Decimal(1)
        for i,title in enumerate((tr('현재'),tr('예상'))):
            y=i*52
            value = self.compare_values[i] if self.compare_values else None
            canvas.create_text(0,y+8,text=title,anchor='w',fill=self.p['muted'],font=('맑은 고딕',10))
            canvas.create_text(width,y+8,text=self.money(value) if value is not None else '—',anchor='e',fill=self.p['text'],font=('맑은 고딕',10,'bold'))
            rounded(canvas,0,y+25,width,y+32,4,fill=self.p['line'],outline='')
            if value is not None and maximum>0 and value>0:
                rounded(canvas,0,y+25,max(8,float(value/maximum)*width),y+32,4,
                        fill=self.p['muted' if i==0 else 'accent'],outline='')

    def responsive(self, event):
        if event.widget is not self:return
        narrow = event.width < 880
        if narrow == self.narrow:return
        self.narrow = narrow
        if narrow:
            self.columns.columnconfigure(1,weight=0,minsize=0)
            self.left.grid_configure(row=0,column=0,padx=0)
            self.right.grid_configure(row=1,column=0,pady=(18,0))
        else:
            self.columns.columnconfigure(1,weight=2,minsize=330)
            self.left.grid_configure(row=0,column=0,padx=(0,20))
            self.right.grid_configure(row=0,column=1,pady=0)

    def on_destroy(self, event):
        if event.widget is self and self.pending:
            self.after_cancel(self.pending);self.pending=None


def build(app):
    import dashboard_theme as theme
    view = AverageCostView(app.content, lambda:app.data, theme.CURRENT)
    view.pack(fill='both',expand=True,padx=(0,12),pady=4)
    app.average_cost_view = view
    return view


