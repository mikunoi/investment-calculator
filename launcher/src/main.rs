#![windows_subsystem = "windows"]
use std::{env, process::Command, os::windows::process::CommandExt};
#[link(name="user32")]
extern "system" { fn MessageBoxW(hwnd: isize, text: *const u16, title: *const u16, flags: u32) -> i32; }
fn main() {
    let result = (|| -> std::io::Result<()> {
        let base = env::current_exe()?.parent().unwrap().to_path_buf();
        let status = Command::new(base.join("runtime").join("CalculatorUI.exe"))
            .current_dir(&base).creation_flags(0x08000000).status()?;
        if !status.success() { return Err(std::io::Error::other(format!("Application exited with {}", status))); }
        Ok(())
    })();
    if let Err(error) = result {
        let text: Vec<u16> = format!("Could not start mikunoi_Stock_Calculator. Please reinstall the application.\n{}",error).encode_utf16().chain(Some(0)).collect();
        let title: Vec<u16> = "mikunoi_Stock_Calculator".encode_utf16().chain(Some(0)).collect();
        unsafe { MessageBoxW(0,text.as_ptr(),title.as_ptr(),0x10); }
    }
}
