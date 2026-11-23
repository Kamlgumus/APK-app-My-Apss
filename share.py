"""Quick Share: yerel HTTP sunucu + QR. Telefon ayni Wi-Fi'dan indirir."""
import socket, threading, http.server, functools, webbrowser, os, subprocess

def _ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80)); return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()

def qr_ascii(data: str) -> str:
    try:
        import qrcode
        return qrcode.QRCode(border=1).add_data(data).make_ascii_art()  # type: ignore
    except Exception:
        return "(pip install qrcode) ya da adresi elle gir: " + data

def share(path: str, port=8077):
    path = os.path.abspath(path)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=os.path.dirname(path))
    httpd = http.server.ThreadingHTTPServer(("0.0.0.0", port), handler)
    url = f"http://{_ip()}:{port}/{os.path.basename(path)}"
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    print("SUNUCU ACIK:", url)
    print(qr_ascii(url))
    # Android'de (Termux) paylasim sayfasi ac
    for cmd in (["termux-open", url], ["am", "start", "-a", "android.intent.action.VIEW", "-d", url],
                ["xdg-open", url]):
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            break
        except FileNotFoundError:
            continue
    return url, httpd
