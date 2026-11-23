"""APK imzalama: apksigner/zipalign varsa onlarla, yoksa debug keystore uret."""
import os, shutil, subprocess
from pathlib import Path
from .builder import find_tool, log

def ensure_keystore(ks: Path):
    if ks.exists(): return
    keytool = find_tool(["keytool"]) or shutil.which("keytool")
    if not keytool:
        java_home = os.environ.get("JAVA_HOME","")
        keytool = str(Path(java_home)/"bin/keytool") if java_home else None
    if not keytool or not Path(keytool).exists():
        raise RuntimeError("keytool bulunamadi (Java JDK kurulu olmali).")
    subprocess.run([keytool,"-genkeypair","-v","-keystore",str(ks),"-alias","apkforge",
        "-keyalg","RSA","-keysize","2048","-validity","10000",
        "-storepass","android","-keypass","android",
        "-dname","CN=APKForge"], check=True, capture_output=True)
    log("Debug keystore uretildi: " + str(ks))

def sign(apk_path: str) -> str:
    apk = Path(apk_path)
    signed = apk.with_name(apk.stem.replace("_unsigned","") + "_signed.apk")
    zipalign, apksigner = find_tool(["zipalign"]), find_tool(["apksigner"])
    ks = Path.home()/".apkforge/debug.keystore"
    ensure_keystore(ks)
    if apksigner:
        aligned = apk.with_suffix(".aligned.apk")
        if zipalign:
            subprocess.run([zipalign,"-f","-p","4",str(apk),str(aligned)], check=True, capture_output=True)
        else:
            aligned = apk
        subprocess.run([apksigner,"sign","--ks",str(ks),"--ks-pass","pass:android",
                        "--out",str(signed),str(aligned)], check=True, capture_output=True)
        return str(signed)
    # son care: jarsigner
    jarsigner = find_tool(["jarsigner"])
    if jarsigner:
        shutil.copy(apk, signed)
        subprocess.run([jarsigner,"-keystore",str(ks),"-storepass","android",
                        "-signedjar",str(signed),str(apk),"apkforge"], check=True, capture_output=True)
        log("UYARI: zipalign yapilamadi, jarsigner ile imzalandi.")
        return str(signed)
    raise RuntimeError("Imzalama araci yok: apksigner (SDK build-tools) veya jarsigner (JDK) gerekli.")
