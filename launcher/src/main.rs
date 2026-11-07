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
    if mutex == 0 { return; }
    if duplicate {
        let gate_name: Vec<u16> = "Local\\mikunoi.StockCalculator.RestartApproval".encode_utf16().chain(Some(0)).collect();
        let gate = unsafe { CreateMutexW(std::ptr::null(), 0, gate_name.as_ptr()) };
        let busy = unsafe { GetLastError() } == 183;
        if gate == 0 || busy {
            unsafe { if gate != 0 { CloseHandle(gate); } CloseHandle(mutex); }
            return;
        }
        let text: Vec<u16> = "이미 실행 중인 계산기를 모두 종료하고 새 계산기를 여시겠습니까?\n저장하지 않은 입력과 목표 설정은 손실될 수 있습니다.\n\nClose existing calculator windows and open a new calculator?\nUnsaved input and target settings may be lost."
            .encode_utf16().chain(Some(0)).collect();
        let title: Vec<u16> = "mikunoi_Stock_Calculator".encode_utf16().chain(Some(0)).collect();
        let approved = unsafe { MessageBoxW(0, text.as_ptr(), title.as_ptr(), 0x124) } == 6;
        let stopped = approved && stop_previous().is_ok();
        unsafe { CloseHandle(gate); }
        if !stopped {
            if approved {
                let error: Vec<u16> = "기존 계산기를 종료하지 못했습니다. 새 실행을 취소했습니다.\nCould not close the existing calculator. Restart cancelled.".encode_utf16().chain(Some(0)).collect();
                unsafe { MessageBoxW(0,error.as_ptr(),title.as_ptr(),0x10); }
            }
            unsafe { CloseHandle(mutex); }
            return;
        }
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

// Short-lived cleanup, restricted to this installation and Windows session.
fn stop_previous() -> std::io::Result<()> {
    use std::os::windows::process::CommandExt;
    let exe = env::current_exe()?;
    let base = exe.parent().ok_or_else(|| std::io::Error::other("Missing installation directory"))?;
    let script = r#"
$ErrorActionPreference='Stop'
$me=[int]$env:CALCULATOR_RESTART_PID
$root=$env:CALCULATOR_RESTART_DIR
$launcher=Join-Path $root 'mikunoi_Stock_Calculator.exe'
$ui=Join-Path $root 'runtime\CalculatorUI.exe'
$session=(Get-Process -Id $me).SessionId
function Matches { @(Get-Process | Where-Object { $_.Id -ne $me -and $_.SessionId -eq $session -and ($_.Path -eq $launcher -or $_.Path -eq $ui) }) }
# Stop waiting launchers first so forced UI exit cannot create an error dialog.
foreach($p in (Matches | Sort-Object @{Expression={if($_.Path -eq $launcher){0}else{1}}})) {
 $fresh=Get-Process -Id $p.Id -ErrorAction SilentlyContinue
 if($fresh -and $fresh.StartTime -eq $p.StartTime -and $fresh.SessionId -eq $session -and ($fresh.Path -eq $launcher -or $fresh.Path -eq $ui)) {
  if($fresh.Path -eq $ui){ [void]$fresh.CloseMainWindow(); [void]$fresh.WaitForExit(2000) }
  if(-not $fresh.HasExited){ $fresh.Kill(); if(-not $fresh.WaitForExit(5000)){throw 'Shutdown timeout'} }
 }
}
if((Matches).Count -gt 0){exit 1}
exit 0
"#;
    let powershell = std::path::PathBuf::from(env::var_os("SystemRoot").unwrap_or_else(|| "C:\\Windows".into()))
        .join("System32/WindowsPowerShell/v1.0/powershell.exe");
    let status = std::process::Command::new(powershell)
        .args(["-NoProfile", "-NonInteractive", "-Command", script])
        .env("CALCULATOR_RESTART_PID", std::process::id().to_string())
        .env("CALCULATOR_RESTART_DIR", base)
        .creation_flags(0x08000000).status()?;
    if !status.success() { return Err(std::io::Error::other("Previous calculator did not exit")); }
    Ok(())
}
