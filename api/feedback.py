import json
import requests
import os
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timedelta, timezone

# Load .env explicitly from current directory
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    from dotenv import load_dotenv
    load_dotenv(env_path)
else:
    from dotenv import load_dotenv
    load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
TARGET_EMAIL = "uznplay@gmail.com"

from supabase import create_client, Client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_ip_rate_limit(ip):
    try:
        now = datetime.now(timezone.utc)
        response = supabase.table("api_rate_limits").select("*").eq("ip", ip).execute()
        
        if response.data:
            record = response.data[0]
            last_request = datetime.fromisoformat(record["last_request_at"].replace('Z', '+00:00'))
            count = record["request_count"]
            
            if now - last_request > timedelta(seconds=60): # 1 minute window for feedback
                supabase.table("api_rate_limits").update({
                    "request_count": 1,
                    "last_request_at": now.isoformat()
                }).eq("ip", ip).execute()
                return True
            
            if count >= 3: # Max 3 feedback per minute
                return False
                
            supabase.table("api_rate_limits").update({
                "request_count": count + 1,
                "last_request_at": last_request.isoformat()
            }).eq("ip", ip).execute()
        else:
            supabase.table("api_rate_limits").insert({
                "ip": ip,
                "request_count": 1,
                "last_request_at": now.isoformat()
            }).execute()
        return True
    except Exception as e:
        print(f"Rate Limit Error: {e}")
        return True

def get_location(ip):
    try:
        if ip in ["127.0.0.1", "::1"]: return "Localhost"
        res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,query", timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "success":
                return f"{data.get('city')}, {data.get('regionName')}, {data.get('country')}"
    except Exception:
        pass
    return "Không xác định"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "active", "message": "Feedback API is running."}).encode('utf-8'))

    def do_POST(self):
        print("DEBUG: feedback_v2_active - No Signature Check")
        try:
            # --- LAYER 0: GEOGRAPHIC BLOCKING (VN Only) ---
            country_code = self.headers.get('x-vercel-ip-country')
            if country_code and country_code.upper() != 'VN':
                print(f"BLOCK: Foreign IP detected ({country_code})")
                self.send_response(403)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "Tính năng này chỉ hỗ trợ người dùng tại Việt Nam. (Foreign IP blocked)",
                    "code": "GEO_BLOCKED"
                }).encode('utf-8'))
                return

            # --- LAYER 1: IP RATE LIMIT (Keep this for basic protection) ---
            client_ip = self.headers.get('X-Forwarded-For', self.client_address[0]).split(',')[0].strip()
            
            if not check_ip_rate_limit(client_ip):
                self.send_response(429)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Bạn gửi phản ánh quá nhanh. Vui lòng đợi 1 phút."}).encode('utf-8'))
                return

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            # Extract data directly from JSON
            topic = data.get("topic", "Khác")
            title = data.get("title", "Không có tiêu đề")
            content = data.get("content", "")
            name = data.get("name", "Ẩn danh")
            phone = data.get("phone", "Không có")
            is_anonymous = data.get("anonymous", False)
            attachments = data.get("attachments", []) # List of {filename, content} base64

            if is_anonymous:
                name = f"{name} (Ẩn danh)"

            # Get Location
            location = get_location(client_ip)

            # Check if API Key exists
            if not RESEND_API_KEY:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Chưa cấu hình RESEND_API_KEY"}).encode('utf-8'))
                return

            # Prepare Email Body (HTML)
            html_content = f"""
            <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: auto; border: 1px solid #eee; padding: 20px; border-radius: 10px;">
                <h2 style="color: #d32f2f; border-bottom: 2px solid #d32f2f; padding-bottom: 10px; margin-top: 0;">📢 Phản ánh kiến nghị mới</h2>
                
                <table style="width: 100%; border-collapse: collapse;">
                    <tr><td style="padding: 8px 0; color: #666;">Lĩnh vực:</td><td style="padding: 8px 0; font-weight: bold;">{topic}</td></tr>
                    <tr><td style="padding: 8px 0; color: #666;">Tiêu đề:</td><td style="padding: 8px 0; font-weight: bold;">{title}</td></tr>
                </table>

                <div style="background: #f9f9f9; padding: 15px; border-radius: 8px; border-left: 4px solid #d32f2f; margin: 20px 0;">
                    <p style="margin: 0; white-space: pre-wrap;">{content}</p>
                </div>

                <div style="background: #fff; border: 1px solid #eee; padding: 15px; border-radius: 8px;">
                    <h3 style="margin-top: 0; font-size: 16px; color: #444; border-bottom: 1px solid #eee; padding-bottom: 5px;">👤 Thông tin người gửi</h3>
                    <p style="margin: 5px 0;"><strong>Họ tên:</strong> {name}</p>
                    <p style="margin: 5px 0;"><strong>SĐT:</strong> {phone}</p>
                </div>

                <div style="background: #e3f2fd; padding: 10px; border-radius: 8px; margin-top: 20px; font-size: 13px;">
                    <p style="margin: 0;"><strong>🌐 Thông tin hệ thống:</strong></p>
                    <p style="margin: 3px 0;">IP: {client_ip}</p>
                    <p style="margin: 3px 0;">Vị trí: {location}</p>
                </div>

                <p style="font-size: 11px; color: #aaa; text-align: center; margin-top: 25px;">
                    Gửi từ Cổng thông tin Đông Mai Số • {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                </p>
            </div>
            """

            # Send via Resend API
            res = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": "DongMaiPortal <onboarding@resend.dev>",
                    "to": [TARGET_EMAIL],
                    "subject": f"[PHẢN ÁNH] {title} - {name}",
                    "html": html_content,
                    "attachments": attachments
                }
            )

            if res.status_code in [200, 201]:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
            else:
                try:
                    error_detail = res.json()
                    error_msg = error_detail.get("message", "Lỗi khi gửi mail qua Resend")
                except:
                    error_msg = f"Lỗi Resend (Status {res.status_code})"
                
                print(f"RESEND ERROR: {error_msg}")
                self.send_response(res.status_code)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": error_msg}).encode('utf-8'))

        except Exception as e:
            print(f"SERVER ERROR: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        return
