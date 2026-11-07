"""Drag scrolling for read-only content; interactive controls keep native gestures."""
import tkinter as tk
from tkinter import ttk

def bind_drag(widget, target=None):
    target = target or widget
    state = {}
    def press(e):
        state.update(y=e.y_root, first=e.y_root, moved=False)
    def move(e):
        if not state or (not state['moved'] and abs(e.y_root-state['first']) < 6): return
        state['moved'] = True
        delta = state['y']-e.y_root
        if isinstance(target, tk.Canvas):
            region = target.bbox('all')
            if region:
                height = max(1,region[3]-region[1])
                target.yview_moveto(target.yview()[0]+delta/height)
        else:
            units = int(delta/12)
            if not units:return 'break'
            target.yview_scroll(units,'units')
        state['y']=e.y_root
        return 'break'
    def release(e):
        moved=state.get('moved',False);state.clear()
        if moved:return 'break'
    widget.bind('<ButtonPress-1>',press,add='+')
    widget.bind('<B1-Motion>',move,add='+')
    widget.bind('<ButtonRelease-1>',release,add='+')

class SlimScrollbar(tk.Canvas):
    """Arrowless scrollbar with a ten-percent wider hover target."""
    _owns_theme = True
    _independent_scroll = True

    def __init__(self,parent,orient='vertical',command=None,**kwargs):
        from average_cost import PALETTES
        import dashboard_theme as theme
        self.p=PALETTES.get(theme.CURRENT,PALETTES['default'])
        self.vertical=orient=='vertical';self.command=command
        self.first,self.last,self.over,self.dragging=0.,1.,False,False
        background=self.p['page'] if parent.cget('bg')=='#031522' else parent.cget('bg')
        super().__init__(parent,bg=background,highlightthickness=0,bd=0,
                         **({'width':11} if self.vertical else {'height':11}))
        self.bind('<Configure>',lambda e:self.draw())
        self.bind('<Enter>',lambda e:self.hover(True))
        self.bind('<Leave>',lambda e:self.hover(False))
        self.bind('<Button-1>',self.press)
        self.bind('<B1-Motion>',self.drag)
        self.bind('<ButtonRelease-1>',lambda e:setattr(self,'dragging',False))

    def set(self,first,last):
        values=float(first),float(last)
        if values==(self.first,self.last):return
        self.first,self.last=values;self.draw()

    def configure(self,cnf=None,**kwargs):
        if 'command' in kwargs:self.command=kwargs.pop('command')
        return super().configure(cnf,**kwargs)

    config=configure

    def refresh_palette(self):
        from average_cost import PALETTES
        import dashboard_theme as theme
        self.p=PALETTES.get(theme.CURRENT,PALETTES['default'])
        self.configure(bg=self.master.cget('bg'));self.draw()

    def hover(self,active):
        self.over=active
        # Reserve the hover width to avoid resizing/repainting the whole page.
        self.draw()

    def geometry_values(self):
        length=max(1,self.winfo_height() if self.vertical else self.winfo_width())
        span=min(length,max(28,length*(self.last-self.first)))
        travel=max(0,length-span)
        start=travel*self.first/max(.000001,1-(self.last-self.first))
        return length,span,travel,start

    def draw(self):
        self.delete('all')
        if self.last-self.first>=.999999:return
        _,span,_,start=self.geometry_values()
        cross=(self.winfo_width() if self.vertical else self.winfo_height())/2
        points=(cross,start+3,cross,start+span-3) if self.vertical else (start+3,cross,start+span-3,cross)
        self.create_line(*points,fill=self.p['accent'] if self.over else self.p['muted'],width=6.6 if self.over else 6,capstyle='round')

    def press(self,event):
        if self.last-self.first>=.999999:return 'break'
        pos=event.y if self.vertical else event.x
        _,span,_,start=self.geometry_values()
        self.offset=pos-start if start<=pos<=start+span else span/2
        self.dragging=True;self.drag(event)
        return 'break'

    def drag(self,event):
        if not self.dragging:return 'break'
        pos=event.y if self.vertical else event.x
        _,_,travel,_=self.geometry_values()
        fraction=max(0,min(1,(pos-self.offset)/max(1,travel)))*(1-(self.last-self.first))
        if self.command:self.command('moveto',fraction)
        return 'break'

def scroll_page(parent, bg, slim=True):
    bar=SlimScrollbar(parent) if slim else ttk.Scrollbar(parent)
    bar.pack(side='right',fill='y')
    canvas=tk.Canvas(parent,bg=bg,highlightthickness=0,yscrollcommand=bar.set)
    canvas.pack(fill='both',expand=True)
    if slim:bar.command=canvas.yview
    else:bar.config(command=canvas.yview)
    body=tk.Frame(canvas,bg=bg)
    item=canvas.create_window(0,0,window=body,anchor='nw')
    body.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.bind('<Configure>',lambda e:canvas.itemconfigure(item,width=e.width))
    def attach():
        if not canvas.winfo_exists():return
        def walk(w):
            if getattr(w,'_independent_scroll',False):return
            w.bind('<MouseWheel>',lambda e:(canvas.yview_scroll(-1 if e.delta>0 else 1,'units'),'break')[1],add='+')
            if isinstance(w,(tk.Frame,tk.Label,tk.Canvas)):bind_drag(w,canvas)
            for child in w.winfo_children():walk(child)
        walk(canvas)
    parent.after_idle(attach)
    return body
