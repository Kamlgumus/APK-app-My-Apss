"""Hata analizi: kural tabanli uzman + istege bagli OpenAI uyumlu API ile dosya ekli yanit."""
import re
from pathlib import Path
from .builder import ERR_LOG, sdk_root, find_tool

RULES = [
 ("gradlew eksik", "Gradle wrapper yok. Cozum: projeyi Android Studio'da ac > 'Sync Project with Gradle Files' calistir; gradle/wrapper/gradle-wrapper.jar dosyasi uretilir. Sonra tekrar ZIP'leyip at.", "https://developer.android.com/studio"),
 ("apktool kurulu degil", "apktool gerekli. Windows: scoop install apktool / Mac: brew install apktool / Linux: apt install apktool. Java 17+ sart.", "https://apktool.org"),
 ("SDK build-tools bulunamadi", "Android SDK yuklu gorunmuyor. Android Studio > SDK Manager'dan 'Android SDK Build-Tools' kur; ANDROID_HOME ortam degiskenini ayarla.", "https://developer.android.com/studio/intro/update#sdk-manager"),
 ("keytool bulunamadi", "JDK kurulu degil. OpenJDK 17 kur (adoptium.net). Kurduktan sonra JAVA_HOME ayarla.", "https://adoptium.net"),
 ("Execution failed for task ':app:compileDebugJavaWithJavac'", "Java derleme hatasi. Koddaki kirmizi satirlari logda bul; buyuk ihtimal import veya sozdizimi hatasi.", None),
 ("ANDROID_HOME", "ANDROID_HOME tanimli degil. Windows: Sistem Ortam Degiskenleri'ne ANDROID_HOME=C:\\\\Users\\\\<sen>\\\\AppData\\\\Local\\\\Android\\\\Sdk ekle.", "https://developer.android.com/tools/variables"),
 ("web sitesi iceriyor", "ZIP icinde saf HTML var. En kolay yol: 'bubblewrap' (Google) ile TWA veya Capacitor: npm i -g @capacitor/cli && npx cap add android. Ben web/assets icerigini Cordova sablonuna sarabilirim, devam edeyim mi?", "https://capacitorjs.com"),
 ("Tanimlanamayan proje", "ZIP kokunde tek klasor olmali ve icinde AndroidManifest.xml / build.gradle / apktool.yml bulunmali. Bana proje yapisini (tree ciktisini) yapistir, hangi tip oldugunu soyleyeyim.", None),
]

def analyze(log_text: str) -> str:
    out = ["### APKForge AI Analizi\n"]
    low = log_text.lower()
    hit = False
    for key, fix, link in RULES:
        if key.lower() in low:
            hit = True
            out.append(f"- **Sorun:** {key}\n  **Cozum:** {fix}" + (f"\n  Kaynak: {link}" if link else ""))
    if not hit:
        m = re.search(r"HATA: (.+)", log_text)
        out.append("Bu hata ozel kurallarimda yok. Log dosyasini analiz etmemi ister misin? "
                   "Asagidaki 'API' sekmesinden anahtarini gir, logu ekleyip gondereyim.")
    out.append("\nOnerilen sonraki adim: hata duzeldikten sonra ayni ZIP'i tekrar at.")
    return "\n".join(out)

def chat_with_api(api_key: str, model: str, log_text: str, base_url="https://api.moonshot.cn/v1"):
    """OpenAI uyumlu endpoint'e log dosyasini ek olarak gonderir."""
    import json, urllib.request
    msg = ("Asagidaki Android build hata logunu analiz et. Turkce, adim adim cozum oner. "
           "Gerekli komutlari ver. Log:\n\n" + log_text[-8000:])
    req = urllib.request.Request(base_url + "/chat/completions",
        data=json.dumps({"model": model, "messages": [{"role": "user", "content": msg}]}).encode(),
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]

def read_log():
    p = Path(ERR_LOG)
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
