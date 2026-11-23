"""APKForge - PC & mobil (Termux) calisan ZIP->APK araci. GUI veya CLI."""
import sys, os, threading
from pathlib import Path
from . import builder, signer, ai, share

def convert(zip_path: str, do_sign=True):
    apk = builder.build(zip_path)
    if do_sign and apk.endswith("_unsigned.apk"):
        try:
            apk = signer.sign(apk)
        except Exception as e:
            builder.log("Imzalama HATA: " + str(e))
    return apk

def cli():
    if len(sys.argv) < 2:
        print("Kullanim: python -m apkforge.main dosya.zip [--no-sign] [--share]")
        sys.exit(1)
    z = sys.argv[1]
    do_sign = "--no-sign" not in sys.argv
    try:
        apk = convert(z, do_sign)
        print("BASARILI:", apk)
        if "--share" in sys.argv:
            share.share(apk)
    except Exception:
        report = ai.analyze(ai.read_log())
        print("\n" + report)
        print("\nDetayli log:", os.path.abspath(builder.ERR_LOG))

def gui():
    import tkinter as tk
    from tkinter import filedialog, scrolledtext, messagebox
    r = tk.Tk(); r.title("APKForge - ZIP'i APK'ye cevir"); r.geometry("760x520")
    state = {}
    top = tk.Frame(r); top.pack(fill="x", padx=8, pady=6)
    var = tk.StringVar(value="ZIP secilmedi")
    tk.Label(top, textvariable=var, fg="#555").pack(side="left")
    out = scrolledtext.ScrolledText(r, state="normal"); out.pack(fill="both", expand=True, padx=8)
    def p(s): out.insert("end", s + "\n"); out.see("end"); r.update()
    def pick():
        f = filedialog.askopenfilename(filetypes=[("ZIP", "*.zip")])
        if f: state["zip"] = f; var.set(f); p("Secildi: " + f)
    def go(sign=True):
        if "zip" not in state: return messagebox.showinfo("APKForge", "Once ZIP sec.")
        def job():
            try:
                apk = convert(state["zip"], sign)
                p("BASARILI: " + apk)
                state["apk"] = apk
            except Exception as e:
                p("HATA: " + str(e))
                p(ai.analyze(ai.read_log()))
        threading.Thread(target=job, daemon=True).start()
    def shareit():
        if "apk" in state:
            u, _ = share.share(state["apk"]); p("Indirme adresi (QR icin konsola bak): " + u)
    def askai():
        p("\n--- AI Analiz ---\n" + ai.analyze(ai.read_log()))
    b = tk.Frame(r); b.pack(fill="x", padx=8, pady=6)
    for t, c in [("ZIP Sec", pick), ("Derle + Imzala", lambda: go(True)),
                 ("Sadece Derle", lambda: go(False)), ("Quick Share", shareit), ("AI Analiz", askai)]:
        tk.Button(b, text=t, command=c, width=14).pack(side="left", padx=3)
    r.mainloop()

if __name__ == "__main__":
    gui() if len(sys.argv) == 1 else cli()
