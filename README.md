# APKForge v1.0

ZIP icerigini tanir ve APK uretir: Gradle projesi -> assembleDebug | apktool projesi -> apktool b | ham manifest+res -> aapt2. Sonra apksigner/jarsigner ile imzalar. Hata olursa kural tabanli AI analizi yapar; API anahtari girersen logu ekleyip gonderir. Quick Share = QR + yerel sunucu.

## Kurulum
    pip install qrcode            # QR icin (opsiyonel)
    # Windows/Mac: Android Studio + JDK 17 + apktool (apktool projeleri icin)

## Calistirma
    python -m apkforge.main                 # GUI (PC)
    python -m apkforge.main uygulama.zip    # CLI
    python -m apkforge.main uygulama.zip --share

## Mobil (Termux)
    pkg install python openjdk-17
    pip install qrcode
    python -m apkforge.main proje.zip --share

## Not
ZIP -> "apk dosyasi" donusumu ancak ZIP icinde gercek Android proje parcalari varsa mumkundur. Icinde sadece HTML varsa uygulama bunu soyler ve Capacitor/Cordova yolunu AI analizinde anlatir.
