#![windows_subsystem = "windows"]
use std::env;
#[link(name="user32")]
extern "system" { fn MessageBoxW(hwnd: isize, text: *const u16, title: *const u16, flags: u32) -> i32; }
#[link(name="kernel32")]
extern "system" {
    fn CreateMutexW(attrs: *const std::ffi::c_void, owner: i32, name: *const u16) -> isize;
    fn GetLastError() -> u32;
    fn CloseHandle(handle: isize) -> i32;
    fn SetDllDirectoryW(path: *const u16) -> i32;
}
fn main() {
    let name: Vec<u16> = "Local\\mikunoi.StockCalculator.SingleInstance".encode_utf16().chain(Some(0)).collect();
    let mutex = unsafe { CreateMutexW(std::ptr::null(), 0, name.as_ptr()) };
    let duplicate = unsafe { GetLastError() } == 183;
    if mutex == 0 || duplicate {
        let text: Vec<u16> = "투자계산기가 이미 실행 중이거나 실행 잠금을 확보할 수 없습니다. 작업표시줄에서 확인해 주세요.\nThe calculator is already running or its startup lock is unavailable. Please check the taskbar.".encode_utf16().chain(Some(0)).collect();
        let title: Vec<u16> = "mikunoi_Stock_Calculator".encode_utf16().chain(Some(0)).collect();
        unsafe { MessageBoxW(0, text.as_ptr(), title.as_ptr(), 0x40); if mutex != 0 { CloseHandle(mutex); } }
        return;
    }
    let result = (|| -> std::io::Result<()> {
        let base = env::current_exe()?.parent().unwrap().to_path_buf();
        run_ui(&base)?;
        Ok(())
    })();
    unsafe { CloseHandle(mutex); }
    if let Err(error) = result {
        let text: Vec<u16> = format!("Could not start mikunoi_Stock_Calculator. Please reinstall the application.\n{}",error).encode_utf16().chain(Some(0)).collect();
        let title: Vec<u16> = "mikunoi_Stock_Calculator".encode_utf16().chain(Some(0)).collect();
        unsafe { MessageBoxW(0,text.as_ptr(),title.as_ptr(),0x10); }
    }
}

#[repr(C)]
struct ShellInfo {
    size:u32, mask:u32, hwnd:isize, verb:*const u16, file:*const u16,
    parameters:*const u16, directory:*const u16, show:i32, instance:isize,
    id_list:*const std::ffi::c_void, class:*const u16, class_key:isize,
    hot_key:u32, icon:isize, process:isize,
}
#[link(name="shell32")]
extern "system" { fn ShellExecuteExW(info:*mut ShellInfo)->i32; }
#[link(name="kernel32")]
extern "system" {
    fn GetExitCodeProcess(handle:isize,code:*mut u32)->i32;
}
fn run_ui(base:&std::path::Path)->std::io::Result<()> {
    use std::os::windows::ffi::OsStrExt;
    // The new UI must not reuse a previous frozen app runtime after updating.
    env::set_var("PYINSTALLER_RESET_ENVIRONMENT", "1");
    unsafe { SetDllDirectoryW(std::ptr::null()); }
    let file:Vec<u16>=base.join("runtime").join("CalculatorUI.exe").as_os_str().encode_wide().chain(Some(0)).collect();
    let directory:Vec<u16>=base.as_os_str().encode_wide().chain(Some(0)).collect();
    let mut info:ShellInfo=unsafe{std::mem::zeroed()};
    info.size=std::mem::size_of::<ShellInfo>() as u32;
    info.mask=0x40|0x100;info.file=file.as_ptr();info.directory=directory.as_ptr();info.show=1;
    if unsafe{ShellExecuteExW(&mut info)}==0{return Err(std::io::Error::last_os_error());}
    if info.process==0{return Err(std::io::Error::other("Missing application process handle"));}
    let wait=wait_ui(info.process);
    let mut code=0;let read=unsafe{GetExitCodeProcess(info.process,&mut code)};
    unsafe{CloseHandle(info.process);}
    if wait!=0 || read==0 || code!=0{return Err(std::io::Error::other(format!("Application exit: {code}")));}
    Ok(())
}

#[repr(C)]
struct Message { hwnd:isize, message:u32, wparam:usize, lparam:isize, time:u32, x:i32, y:i32, private:u32 }
#[link(name="user32")]
extern "system" {
    fn MsgWaitForMultipleObjects(count:u32,handles:*const isize,all:i32,timeout:u32,wake:u32)->u32;
    fn PeekMessageW(message:*mut Message,hwnd:isize,min:u32,max:u32,remove:u32)->i32;
    fn TranslateMessage(message:*const Message)->i32;
    fn DispatchMessageW(message:*const Message)->isize;
}
fn wait_ui(handle:isize)->u32 {
    loop {
        let result=unsafe{MsgWaitForMultipleObjects(1,&handle,0,u32::MAX,0x04FF)};
        if result!=1{return result;}
        let mut message:Message=unsafe{std::mem::zeroed()};
        while unsafe{PeekMessageW(&mut message,0,0,0,1)}!=0 {
            unsafe{TranslateMessage(&message);DispatchMessageW(&message);}
        }
    }
}
