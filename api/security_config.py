import json
import os
from http.server import BaseHTTPRequestHandler

# Load .env explicitly
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    from dotenv import load_dotenv
    load_dotenv(env_path)
else:
    from dotenv import load_dotenv
    load_dotenv()


def _env_bool(key: str, default: str = "false") -> bool:
    """Đọc bool từ .env — chấp nhận true/false có hoặc không có ngoặc kép."""
    raw = os.getenv(key, default)
    if raw is None:
        raw = default
    s = str(raw).strip().strip('"').strip("'").lower()
    return s in ("true", "1", "yes", "on")


def _env_int(key: str, default: int = 200) -> int:
    raw = os.getenv(key, str(default))
    if raw is None:
        return default
    try:
        return int(str(raw).strip().strip('"').strip("'"))
    except ValueError:
        return default


def _env_detectors() -> list:
    raw = os.getenv("DISABLE_DEVTOOL_DETECTORS", "0 1 2 3 4 5 6 7")
    parts = str(raw).replace(",", " ").split()
    out = []
    for p in parts:
        p = p.strip().strip('"').strip("'")
        if not p:
            continue
        try:
            out.append(int(p))
        except ValueError:
            continue
    return out if out else [0, 1, 2, 3, 4, 5, 6, 7]


class SecurityConfig:
    """Quản lý cấu hình bảo mật từ phía server"""
    
    @staticmethod
    def get_config():
        """
        Lấy cấu hình bảo mật từ server.
        Người dùng không thể bypass vì config được server quản lý.
        """
        return {
            # Cấu hình disable-devtool
            "disableDevtool": {
                "enabled": _env_bool("DISABLE_DEVTOOL_ENABLED", "true"),
                "disableMenu": _env_bool("DISABLE_DEVTOOL_DISABLE_MENU", "true"),
                "disableSelect": _env_bool("DISABLE_DEVTOOL_DISABLE_SELECT", "false"),
                "disableCopy": _env_bool("DISABLE_DEVTOOL_DISABLE_COPY", "false"),
                "disableCut": _env_bool("DISABLE_DEVTOOL_DISABLE_CUT", "false"),
                "disablePaste": _env_bool("DISABLE_DEVTOOL_DISABLE_PASTE", "false"),
                "detectors": _env_detectors(),
                "interval": _env_int("DISABLE_DEVTOOL_INTERVAL", 200),
            },
            # Các cấu hình bảo mật khác có thể thêm sau
            "security": {
                "enabled": _env_bool("SECURITY_ENABLED", "true"),
            }
        }


# Singleton instance
config = SecurityConfig()


class handler(BaseHTTPRequestHandler):
    """API Handler cho cấu hình bảo mật"""
    
    def do_GET(self):
        """Trả về cấu hình bảo mật (để admin dashboard có thể xem)"""
        # On Vercel, self.path might be different based on rewrites
        if '/api/security-config' in self.path:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.end_headers()
            
            # Trả về config
            self.wfile.write(json.dumps(config.get_config()).encode('utf-8'))
            return
        
        # 404 for other paths
        self.send_response(404)
        self.end_headers()
    
    def do_POST(self):
        """API để cập nhật cấu hình (cần auth - chỉ admin mới dùng được)"""
        if self.path == '/api/security-config/update':
            # TODO: Thêm authentication check
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                # Cập nhật vào .env hoặc database
                for key, value in data.items():
                    os.environ[key] = str(value)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "message": "Config updated. Restart server to apply."}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return
        
        self.send_response(404)
        self.end_headers()
