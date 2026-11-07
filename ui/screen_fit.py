"""Keep calculator windows inside the current Windows monitor work area."""
import ctypes
from ctypes import wintypes as W
import tkinter as tk

def fit_bounds(rect, area, initial=False):
    left,top,right,bottom=area
    aw,ah=max(1,right-left),max(1,bottom-top)
    x,y,width,height=rect
    nw,nh=max(1,min(width,aw-24)),max(1,min(height,ah-24))
    if initial:
        nw,nh=max(1,min(1362,aw-32)),max(1,min(892,ah-32))
        x,y=left+(aw-nw)//2,top+(ah-nh)//2
    else:
        x,y=max(left,min(x,right-nw)),max(top,min(y,bottom-nh))
    return x,y,nw,nh

class MonitorInfo(ctypes.Structure):
    _fields_ = [('size', W.DWORD), ('monitor', W.RECT), ('work', W.RECT), ('flags', W.DWORD)]

class ScreenFit:
    def __init__(self, app):
        self.app, self.job, self.signature = app, None, {}
        self.user = ctypes.WinDLL('user32', use_last_error=True)
        self.user.GetAncestor.argtypes=[W.HWND,W.UINT];self.user.GetAncestor.restype=W.HWND
        self.user.MonitorFromWindow.argtypes=[W.HWND,W.DWORD];self.user.MonitorFromWindow.restype=W.HANDLE
        self.user.GetMonitorInfoW.argtypes=[W.HANDLE,ctypes.POINTER(MonitorInfo)]
        self.user.GetWindowRect.argtypes=[W.HWND,ctypes.POINTER(W.RECT)]
        self.user.SetWindowPos.argtypes=[W.HWND,W.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,W.UINT]
        self.initial_job=app.after(100,self.initial_fit)
        self.map_jobs=set()
        self.job=app.after(1500,self.poll)
        self.map_binding=app.bind('<Map>',self.mapped,add='+')

    def initial_fit(self):
        self.initial_job=None
        if not self.app.closing:self.safe_fit(self.app,initial=True)

    def area(self, win):
        hwnd=self.user.GetAncestor(win.winfo_id(),2)
        info=MonitorInfo();info.size=ctypes.sizeof(info)
        if not self.user.GetMonitorInfoW(self.user.MonitorFromWindow(hwnd,2),ctypes.byref(info)):
            raise OSError('Monitor work area unavailable')
        r=info.work
        return hwnd,(r.left,r.top,r.right,r.bottom)

    def fit(self, win, initial=False):
        if win.state() in ('iconic','withdrawn'):return
        hwnd,(l,t,r,b)=self.area(win)
        if win is self.app:
            win.minsize(max(1,min(880,r-l-32)),max(1,min(640,b-t-64)))
        rect=W.RECT()
        if not self.user.GetWindowRect(hwnd,ctypes.byref(rect)):return
        width,height=rect.right-rect.left,rect.bottom-rect.top
        x,y,nw,nh=fit_bounds((rect.left,rect.top,width,height),(l,t,r,b),initial)
        if (x,y,nw,nh)!=(rect.left,rect.top,width,height):
            # Native coordinates support monitors left/above the primary screen.
            self.user.SetWindowPos(hwnd,None,x,y,nw,nh,0x0014)

    def mapped(self,event):
        if isinstance(event.widget,tk.Toplevel):
            job=None
            def run():
                self.map_jobs.discard(job)
                if not self.app.closing:self.safe_fit(event.widget)
            job=self.app.after_idle(run);self.map_jobs.add(job)

    def safe_fit(self,win,initial=False):
        try:
            if win.winfo_exists():self.fit(win,initial)
        except (tk.TclError,OSError):pass

    def poll(self):
        self.job=None
        if self.app.closing:return
        windows=[self.app]+[w for w in self.app.winfo_children() if isinstance(w,tk.Toplevel)]
        current={}
        for win in windows:
            try:
                if win.state() in ('withdrawn','iconic'):continue
                area=self.area(win)[1];key=str(win)
                current[key]=area
                if self.signature.get(key)!=area:self.safe_fit(win)
            except (tk.TclError,OSError):pass
        self.signature=current
        delay=5000 if self.app.state()=='iconic' else 1500
        self.job=self.app.after(delay,self.poll)

    def stop(self):
        for job in [self.job,self.initial_job,*self.map_jobs]:
            if job is not None:self.app.after_cancel(job)
        self.job=self.initial_job=None;self.map_jobs.clear()
        if self.map_binding:self.app.unbind("<Map>",self.map_binding);self.map_binding=None
