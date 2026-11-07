use std::{env, path::PathBuf, process::Command};
fn main() {
    let root = PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap());
    let icon = root.join("../assets/matrix-icon.ico").canonicalize().unwrap();
    println!("cargo:rerun-if-changed={}", icon.display());
    println!("cargo:rerun-if-env-changed=RC");
    let out = PathBuf::from(env::var("OUT_DIR").unwrap());
    let rc = out.join("icon.rc");
    let res = out.join("icon.res");
    std::fs::copy(&icon, out.join("app.ico")).unwrap();
    std::fs::write(&rc, "1 ICON \"app.ico\"\n").unwrap();
    let compiler = env::var("RC").unwrap_or_else(|_| "C:/Program Files (x86)/Windows Kits/10/bin/10.0.26100.0/x64/rc.exe".into());
    let status = Command::new(compiler).current_dir(&out).arg("/nologo").arg("/fo").arg("icon.res").arg("icon.rc").status().expect("Windows SDK resource compiler required; set RC");
    assert!(status.success(), "Icon resource compilation failed");
    println!("cargo:rustc-link-arg={}", res.display());
}

