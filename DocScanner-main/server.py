"""
Simple HTTP server to serve DocScanner web app + ONNX model.
Adds COOP/COEP headers so the browser becomes crossOriginIsolated,
enabling WebAssembly multi-threading (SharedArrayBuffer).

Run: python server.py
Then open: http://localhost:8765
  (Cổng có thể đổi: set PORT=5000 trước khi chạy)
"""

import http.server
import socketserver
import os
from urllib.parse import urlparse

# Mặc định 8765 tránh xung đột với nhiều tiến trình cũ trên 5000
PORT = int(os.environ.get("PORT", "8765"))

WEB_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(WEB_DIR)


class COOPCOEPHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that adds COOP/COEP headers for crossOriginIsolated mode."""

    extensions_map = {
        '.html': 'text/html',
        '.js': 'application/javascript',
        '.mjs': 'application/javascript',
        '.wasm': 'application/wasm',
        '.onnx': 'application/octet-stream',
        '.ot': 'application/octet-stream',
    }

    def end_headers(self):
        # COEP: blocks cross-origin resources that don't opt-in via CORS/CRP
        # COOP: isolates browsing context to prevent cross-origin access
        # Together they enable crossOriginIsolated = true → SharedArrayBuffer
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        super().end_headers()

    def do_GET(self):
        # Tránh 404 + log_error làm crash log_message cũ; trình duyệt vẫn hay gọi favicon
        if urlparse(self.path).path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        super().do_GET()

    def log_message(self, format, *args):
        # Giống thư viện chuẩn: log_error() gọi với ít hơn 3 tham số (vd. 404)
        line = format % args if args else format
        print(f"  {line}")


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    with ReusableTCPServer(("", PORT), COOPCOEPHandler) as httpd:
        print("=" * 55)
        print("  DOCSCANNER WEB  (crossOriginIsolated mode)")
        print("=" * 55)
        print(f"  Open: http://localhost:{PORT}")
        print(f"  On mobile (same WiFi): http://<YOUR-IP>:{PORT}")
        print("=" * 55)
        httpd.serve_forever()
