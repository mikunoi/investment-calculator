from i18n import tr
"""Allocation preview and shared shortage rendering helpers."""
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from PIL import Image, ImageDraw, ImageTk
from scroll_support import SlimScrollbar
from average_cost import SoftButton


def format_money(entry, variable):
    raw = variable.get()
    clean = raw.replace(',', '')
    if not re.fullmatch(r'-?\d*(?:\.\d*)?', clean) or clean in ('','-'):return
    point = len(raw[:entry.index('insert')].replace(',', ''))
    whole, dot, fraction = clean.partition('.')
    negative=whole.startswith('-')
    formatted = ('-' if negative else '')+f'{int(whole.lstrip("-") or 0):,}' + (dot + fraction if dot else '')
    if formatted == raw:return
    variable.set(formatted)
    count = 0
    for index, char in enumerate(formatted):
        count += char != ','
        if count >= point:
            entry.icursor(index + 1);break


def hatch_sector(image, bounds, start, extent, scale):
    mask = Image.new('L', image.size)
    brush = ImageDraw.Draw(mask)
    if extent >= 359.999999:brush.ellipse(bounds, fill=255)
    else:brush.pieslice(bounds,start=start,end=start+extent,fill=255)
    stripes = Image.new('RGB', image.size, '#E99083')
    draw = ImageDraw.Draw(stripes)
    width,height=image.size
    for x in range(-height,width,12*scale):
        draw.line((x,0,x+height,height),fill='#763A34',width=3*scale)
    image.paste(stripes,(0,0),mask)
    stripes.close();mask.close()


def preview(owner, image, palette):
    parent=owner.winfo_toplevel()
    window=tk.Toplevel(parent);window.withdraw();window.title(tr('비중계산 이미지 미리보기'))
    window.configure(bg=palette['page']);window.transient(parent)
    width=min(1100,window.winfo_screenwidth()-80)
    height=min(850,window.winfo_screenheight()-100)
    x=max(0,min(parent.winfo_rootx()+(parent.winfo_width()-width)//2,window.winfo_screenwidth()-width))
    y=max(0,min(parent.winfo_rooty()+(parent.winfo_height()-height)//2,window.winfo_screenheight()-height))
    window.geometry(f'{width}x{height}+{x}+{y}')
    actions=tk.Frame(window,bg=palette['page']);actions.pack(fill='x',padx=18,pady=12)
    tk.Label(actions,text=tr('목표 설정과 차트를 확인한 후 저장하세요.'),font=('맑은 고딕',12),bg=palette['page'],fg=palette['text']).pack(side='left')
    def save():
        path=filedialog.asksaveasfilename(parent=window,title=tr('비중계산 이미지 저장'),defaultextension='.png',
            filetypes=[(tr('PNG 이미지'),'*.png')],initialfile=tr('비중계산_')+datetime.now().strftime('%Y%m%d_%H%M%S')+'.png')
        if not path:return
        try:
            image.save(path,format='PNG')
            messagebox.showinfo(tr('이미지 저장'),tr('PNG 이미지를 저장했습니다.'),parent=window)
        except Exception as error:messagebox.showerror(tr('저장 실패'),str(error),parent=window)
    SoftButton(actions,tr('PNG 저장'),save,palette,primary=True,width=120,height=40).pack(side='right')
    content=tk.Frame(window,bg=palette['page']);content.pack(fill='both',expand=True,padx=16,pady=(0,16))
    canvas=tk.Canvas(content,bg=palette['page'],highlightthickness=0)
    bar=SlimScrollbar(content,orient='vertical',command=canvas.yview)
    canvas.configure(yscrollcommand=bar.set);bar.pack(side='right',fill='y');canvas.pack(fill='both',expand=True)
    ratio=min(1,(width-65)/image.width)
    thumbnail=image.resize((round(image.width*ratio),round(image.height*ratio)),Image.Resampling.LANCZOS)
    photo=ImageTk.PhotoImage(thumbnail,master=window);thumbnail.close()
    canvas.image=photo
    canvas.create_image(0,0,image=photo,anchor='nw');canvas.configure(scrollregion=canvas.bbox('all'))
    canvas.bind('<MouseWheel>',lambda e:canvas.yview_scroll(-1 if e.delta>0 else 1,'units'))
    window.bind('<Destroy>',lambda e:image.close() if e.widget==window else None,add='+')
    window.deiconify()
