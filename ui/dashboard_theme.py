"""Presentation-only themes. No account, scheduler, strategy or network access."""
from PIL import Image, ImageOps
from tkinter import ttk, TclError

CURRENT='default'
NAMES={'default':'기본','white':'화이트 · 블랙 앤 화이트','matrix':'매트릭스 · 레트로 터미널','toss':'토스증권 스타일'}


# Presentation palette only; broker identity colors retain their meaning.
TOSS_COLORS = {
    '#031522':'#F2F4F6', '#061E30':'#FFFFFF', '#12435C':'#E5E8EB',
    '#EDF5FC':'#191F28', '#8DA6B9':'#6B7684', '#145166':'#D9E8FF',
    '#0C2B42':'#F2F4F6', '#314B61':'#E8F3FF', '#063D36':'#E8F3FF',
    '#38222F':'#FFF0F1', '#27677F':'#E5E8EB', '#062A2C':'#F5F8FF',
    '#147568':'#F5F8FF', '#00D6AF':'#159C82', '#E58390':'#E45464',
    '#0B3045':'#F2F4F6', '#0D2C40':'#F2F4F6', '#AFCFE2':'#6B7684',
    '#B4C6D3':'#6B7684', '#73BCD8':'#3182F6', '#65BFDD':'#3182F6',
    '#E3EAF0':'#191F28', '#98A8B7':'#6B7684', '#66C2AC':'#159C65', '#DE8B98':'#D94154',
    '#C9B76D':'#967218', '#FFFFFF':'#191F28',
    '#102D3E':'#E5E8EB', '#071A2A':'#FFFFFF', '#092A3E':'#F2F4F6',
    '#102F43':'#E5E8EB', '#537D97':'#B0B8C1', '#729DB5':'#8B95A1',
    '#72D3F4':'#2272EB', '#C79DE8':'#8555B6', '#AA82C4':'#8055A0',
    '#6AB7E6':'#2272EB', '#E08D99':'#E54B60', '#0D2C43':'#FFFFFF',
    '#39738F':'#D1D6DB',
    '#A65D7B':'#D99AB8', '#669DD1':'#96BFFF', '#D9B84F':'#ECCE7B',
}


def toss_color(value):
    if value.upper() in ('#E4EAF2','#A5C8FF','#C1B5F3','#9EDDD3','#F3D58C','#EDB5CE','#B1D5F1','#D2C4EB','#BDDCCB'):return value
    if value.upper() in TOSS_COLORS:return TOSS_COLORS[value.upper()]
    r,g,b=(int(value[i:i+2],16) for i in (1,3,5))
    if r < 65 and g < 100 and b < 125 and b >= g >= r:
        return '#F2F4F6'
    if min(r,g,b)>165 and max(r,g,b)-min(r,g,b)<65:
        return '#333D4B'
    return value


def select(name):
    global CURRENT
    CURRENT=name if name in NAMES else 'default'


def rgb(level,theme):
    if theme=='white':
        v=max(0,min(255,round(255-level*1.04)))
        if level<40:v=round(255-level*.15)
        if level<25:v=255
        return (v,v,v)
    glow=round(5+230*(level/255)**1.16)
    return (round(glow*.36),glow,round(glow*.19))


def color(value):
    if CURRENT=='default' or not isinstance(value,str) or len(value)!=7 or not value.startswith('#'):return value
    if CURRENT=='toss':return toss_color(value)
    try:r,g,b=(int(value[i:i+2],16) for i in (1,3,5))
    except ValueError:return value
    return '#%02x%02x%02x'%rgb(round(.299*r+.587*g+.114*b),CURRENT)


def image(im,theme=None):
    theme=theme or CURRENT
    if theme=='default':return im
    if theme=='toss':
        # Sidebar glyphs only: continuous luminance interpolation, never quantization.
        gray=ImageOps.grayscale(im)
        background=(242,244,247); foreground=(51,61,75)
        channels=[]
        for c in range(3):
            table=[round(background[c]+(foreground[c]-background[c])*max(0,min(1,(i-25)/215))) for i in range(256)]
            channels.append(gray.point(table))
        return Image.merge('RGB',channels)
    gray=ImageOps.grayscale(im)
    channels=[gray.point([rgb(i,theme)[c] for i in range(256)]) for c in range(3)]
    return Image.merge('RGB',channels)


def chart_color(index,is_cash,original,theme=None):
    theme=theme or CURRENT
    if theme=='toss':
        palette=('#A5C8FF','#C1B5F3','#9EDDD3','#F3D58C','#EDB5CE','#B1D5F1','#D2C4EB','#BDDCCB')
        return '#E4EAF2' if is_cash else palette[index%len(palette)]
    if theme=='default':return '#8DA6B9' if is_cash else original
    shades=(180,65,135,220,95,155,45,200,115,240)
    v=110 if is_cash else shades[index%len(shades)]
    return '#%02x%02x%02x'%(v,v,v)


def widgets(root):
    """Track original colors so switching themes never remaps a mapped color."""
    if getattr(root,'_independent_scroll',False):
        root.refresh_palette()
        return
    if getattr(root, '_owns_theme', False):
        return  # Self-contained tool pages set their palette when opened.
    try:
        memory=getattr(root,'_theme_colors',{})
        for option in ('background','foreground','activebackground','activeforeground','selectcolor',
                       'insertbackground','highlightbackground','highlightcolor','disabledforeground'):
            try:
                current=str(root.cget(option));base,last=memory.get(option,(current,None))
                if current!=last:base=current
                defaults={'background':'#061E30','foreground':'#EDF5FC','activebackground':'#145166',
                          'activeforeground':'#EDF5FC','selectcolor':'#061E30','insertbackground':'#EDF5FC',
                          'highlightbackground':'#12435C','highlightcolor':'#8DA6B9','disabledforeground':'#8DA6B9'}
                if option not in memory and current==str(root.configure(option)[3]):base=defaults[option]
                if not base.startswith('#'):
                    try:base='#%02x%02x%02x'%tuple(v//257 for v in root.winfo_rgb(base))
                    except TclError:pass
                mapped=color(base)
                if current!=mapped:root.configure(**{option:mapped})
                memory[option]=(base,mapped)
            except TclError:pass
        root._theme_colors=memory
        if hasattr(root,'_theme_source_image') and getattr(root,'_theme_image_style',None)!=CURRENT:
            from PIL import ImageTk
            root.nav_image=ImageTk.PhotoImage(image(root._theme_source_image))
            root.configure(image=root.nav_image);root._theme_image_style=CURRENT
        for child in root.winfo_children():widgets(child)
    except TclError:return


def style(root):
    s=ttk.Style(root)
    s.configure('Treeview',background=color('#061E30'),fieldbackground=color('#061E30'),foreground=color('#EDF5FC'))
    s.configure('Treeview.Heading',background=color('#12435C'),foreground=color('#EDF5FC'))
    s.map('Treeview.Heading',background=[('pressed',color('#145166')),('active',color('#314B61'))],foreground=[('!disabled',color('#EDF5FC'))])
    s.map('Treeview',background=[('selected',color('#314B61'))],foreground=[('selected',color('#EDF5FC'))])
    for direction in ('Vertical','Horizontal'):
        s.configure(direction+'.TScrollbar',background=color('#12435C'),troughcolor=color('#061E30'),arrowcolor=color('#8DA6B9'))
    s.configure('TNotebook',background=color('#031522'))
    s.configure('TNotebook.Tab',background=color('#061E30'),foreground=color('#EDF5FC'))
    s.map('TNotebook.Tab',background=[('selected',color('#12435C')),('active',color('#145166')),('!selected',color('#061E30'))],
          foreground=[('disabled',color('#8DA6B9')),('!disabled',color('#EDF5FC'))])
    for direction in ('Vertical','Horizontal'):
        s.map(direction+'.TScrollbar',background=[('pressed',color('#537D97')),('active',color('#314B61'))])
    s.configure('TCombobox',fieldbackground=color('#061E30'),foreground=color('#EDF5FC'),background=color('#12435C'))
    s.map('TCombobox',fieldbackground=[('readonly',color('#061E30'))],foreground=[('readonly',color('#EDF5FC'))])

