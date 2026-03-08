from http.server import BaseHTTPRequestHandler
import json
import os
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
ADMIN_SECRET = os.getenv("ADMIN_CREATION_SECRET")  # secret token cần có để tạo admin

# Chỉ cho phép domain của portal gọi API này
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "https://phuongdongmai.vercel.app")

# Rate limiting đơn giản: lưu IP và thời gian request gần nhất
_rate_limit_store: dict[str, list[float]] = {}
RATE_LIMIT_MAX = 3        # tối đa 3 lần / cửa sổ thời gian
RATE_LIMIT_WINDOW = 300   # 5 phút (giây)


def check_rate_limit(ip: str) -> bool:
    """Trả về True nếu còn trong giới hạn, False nếu đã vượt quá."""
    now = time.time()
    bucket = _rate_limit_store.get(ip, [])
    # Loại bỏ các request cũ ngoài cửa sổ
    bucket = [t for t in bucket if now - t < RATE_LIMIT_WINDOW]
    if len(bucket) >= RATE_LIMIT_MAX:
        return False
    bucket.append(now)
    _rate_limit_store[ip] = bucket
    return True


class handler(BaseHTTPRequestHandler):

    # ------------------------------------------------------------------
    # Ghi log ra stderr (console server), không lộ ra client
    # ------------------------------------------------------------------
    def log_message(self, format, *args):
        print(f"[create-admin] {self.address_string()} - {format % args}")

    # ------------------------------------------------------------------
    # Helper: gửi JSON response
    # ------------------------------------------------------------------
    def _send_json(self, status: int, body: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    # ------------------------------------------------------------------
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    # ------------------------------------------------------------------
    def do_POST(self):
        """Create new admin user – yêu cầu ADMIN_CREATION_SECRET hợp lệ"""
        try:
            # --- 1. Rate limiting ---
            client_ip = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()
            if not check_rate_limit(client_ip):
                self._send_json(429, {"error": "Quá nhiều yêu cầu. Vui lòng thử lại sau 5 phút."})
                return

            # --- 2. Xác thực server config ---
            if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
                print("[create-admin] ERROR: Missing Supabase env vars")
                self._send_json(500, {"error": "Lỗi cấu hình server."})
                return

            if not ADMIN_SECRET:
                print("[create-admin] ERROR: ADMIN_CREATION_SECRET not set")
                self._send_json(500, {"error": "Lỗi cấu hình server."})
                return

            # --- 3. Parse body ---
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)

            # --- 4. Xác thực secret token (Authorization header) ---
            auth_header = self.headers.get("Authorization", "")
            provided_secret = auth_header.replace("Bearer ", "").strip()
            if not provided_secret or provided_secret != ADMIN_SECRET:
                self._send_json(403, {"error": "Không có quyền thực hiện hành động này."})
                return

            # --- 5. Validate input ---
            email    = data.get("email", "").strip()
            password = data.get("password", "")
            full_name = data.get("full_name", "").strip()

            if not email or not password:
                self._send_json(400, {"error": "Email và mật khẩu là bắt buộc."})
                return

            if len(password) < 8:
                self._send_json(400, {"error": "Mật khẩu phải có ít nhất 8 ký tự."})
                return

            # --- 6. Tạo user qua Supabase Admin API ---
            admin_url = f"{SUPABASE_URL}/auth/v1/admin/users"
            payload = {
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": full_name,
                    "role": "admin"
                }
            }

            req = Request(
                admin_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                    "Content-Type": "application/json",
                    "apikey": SUPABASE_SERVICE_KEY,
                },
                method="POST",
            )

            try:
                with urlopen(req) as response:
                    response_data = json.loads(response.read().decode("utf-8"))
                    self._send_json(200, {
                        "success": True,
                        "user": {
                            "id":         response_data.get("id"),
                            "email":      response_data.get("email"),
                            "created_at": response_data.get("created_at"),
                        },
                    })

            except HTTPError as e:
                error_body  = e.read().decode("utf-8")
                try:
                    error_data = json.loads(error_body)
                    msg = error_data.get("msg", "Không thể tạo tài khoản.")
                except Exception:
                    msg = "Không thể tạo tài khoản."
                print(f"[create-admin] Supabase error {e.code}: {error_body}")
                self._send_json(e.code or 400, {"error": msg})

        except json.JSONDecodeError:
            self._send_json(400, {"error": "Dữ liệu gửi lên không hợp lệ (JSON lỗi)."})

        except Exception:
            import traceback
            print("[create-admin] Unhandled exception:")
            traceback.print_exc()
            self._send_json(500, {"error": "Lỗi máy chủ nội bộ."})
