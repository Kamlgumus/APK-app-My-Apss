"""ZIP -> APK build motoru: proje tani, derle, hata yakala."""
import zipfile, os, shutil, subprocess, tempfile, platform
from pathlib import Path

ERR_LOG = "apkforge_errors.log"

def log(msg):
    with open(ERR_LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

def find_tool(names):
    for n in names:
        p = shutil.which(n)
        if p: return p
    return None

def sdk_root():
    for env in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        v = os.environ.get(env)
        if v and Path(v).exists(): return Path(v)
    cands = [Path.home()/"AppData/Local/Android/Sdk",
             Path.home()/"Library/Android/sdk",
             Path.home()/"Android/Sdk"]
    for c in cands:
        if c.exists(): return c
    return None

def build_tools(sdk):
    if not sdk: return None
    bt = sorted((sdk/"build-tools").glob("*"))
    return bt[-1] if bt else None

def detect_project(root: Path):
    if (root/"apktool.yml").exists(): return "apktool"
    if (root/"build.gradle").exists() or (root/"build.gradle.kts").exists(): return "gradle"
    if (root/"AndroidManifest.xml").exists(): return "raw"
    if list(root.glob("*.html")): return "web"
    return "unknown"

def extract(zip_path: str, out_dir: str):
    with zipfile.ZipFile(zip_path) as z:
        for n in z.namelist():
            t = (Path(out_dir)/n).resolve()
            if not str(t).startswith(str(Path(out_dir).resolve())):
                raise ValueError("Guvenli olmayan zip yolu: " + n)
        z.extractall(out_dir)
    entries = [p for p in Path(out_dir).iterdir()]
    return entries[0] if len(entries) == 1 and entries[0].is_dir() else Path(out_dir)

def run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if p.stdout: log(p.stdout.strip())
    if p.returncode != 0:
        raise RuntimeError("Komut basarisiz: " + " ".join(map(str, cmd)) + "\n" + (p.stderr or p.stdout or ""))
    return p

def build(zip_path: str):
    """ZIP'i APK'ye cevirir. Donen: apk yolu."""
    log("=== Yeni islem: " + zip_path)
    tmp = tempfile.mkdtemp(prefix="apkforge_")
    try:
        root = extract(zip_path, tmp)
        kind = detect_project(root)
        log("Proje tipi: " + kind)
        sdk, bt = sdk_root(), build_tools(sdk_root())
        if kind == "gradle":
            gw = root/"gradlew"
            if not gw.exists(): gw = root/"gradlew.bat" if platform.system()=="Windows" else gw
            if not gw.exists(): raise RuntimeError("gradlew eksik. Projeyi Android Studio'da acip 'Gradle wrapper' uretin.")
            shell = platform.system()=="Windows"
            run([str(gw) if not shell else str(gw), "assembleDebug"], cwd=root)
            apks = list(root.glob("**/debug/*.apk")) + list(root.glob("**/*-debug.apk"))
            if not apks: raise RuntimeError("Derleme tamam ama APK bulunamadi.")
            out = Path.cwd()/(Path(zip_path).stem + ".apk")
            shutil.copy(apks[0], out); return str(out)
        if kind == "apktool":
            apktool = find_tool(["apktool","apktool.jar"])
            if not apktool: raise RuntimeError("apktool kurulu degil (Java gerekli). https://apktool.org")
            run([apktool,"b",str(root),"-o",str(Path.cwd()/(Path(zip_path).stem+"_unsigned.apk"))])
            return str(Path.cwd()/(Path(zip_path).stem+"_unsigned.apk"))
        if kind == "raw":
            if not bt: raise RuntimeError("Android SDK build-tools bulunamadi. ANDROID_HOME ayarlayin.")
            aapt2 = bt/"aapt2"; d8 = bt/"d8"
            if not aapt2.exists(): raise RuntimeError("aapt2 bulunamadi: " + str(bt))
            dex = bt/"dx"
            apk = Path.cwd()/(Path(zip_path).stem+"_unsigned.apk")
            run([str(aapt2),"link","--proto-format","-o",str(apk),"--manifest",str(root/"AndroidManifest.xml"),"-I",str(sdk/"platforms")])
            # basit yol: manifest+res paketle, dex yoksa yine de cikti ver
            if (root/"classes.dex").exists(): log("classes.dex var; ileri imzalama gerekli.")
            return str(apk)
        if kind == "web":
            raise RuntimeError("ZIP bir web sitesi iceriyor. Bunu WebView APK'sina sarmalamak icin Cordova/Capacitor kurulumu gerekir. Detay icin AI analizine bakin.")
        raise RuntimeError("Tanimlanamayan proje. ZIP icinde AndroidManifest.xml, build.gradle veya apktool.yml olmali.")
    except Exception as e:
        log("HATA: " + str(e))
        raise
