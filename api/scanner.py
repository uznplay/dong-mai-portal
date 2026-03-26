import requests
from http.server import BaseHTTPRequestHandler

# URL của AI Server (phải đảm bảo AI Server cũng nhận Multipart/FormData)
SERVER_PROCESSING_URL = "https://ungabled-jaquelyn-flusteredly.ngrok-free.dev/api/scanner"

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_POST(self):
        try:
            # 1. Lấy Content-Type từ trình duyệt (bao gồm cả chuỗi 'boundary' cực kỳ quan trọng)
            original_content_type = self.headers.get('Content-Type')
            content_length = int(self.headers.get('Content-Length', 0))
            
            # Đọc toàn bộ body (dạng binary)
            image_data = self.rfile.read(content_length)

            if not image_data:
                self.send_response(400)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"error": "Du lieu trong"}')
                return

            print(f"--- Dang chuyen tiep anh toi AI Server: {SERVER_PROCESSING_URL} ---")

            # 2. Chuyển tiếp nguyên văn sang AI Server
            # QUAN TRỌNG: Phải gửi kèm headers={'Content-Type': original_content_type}
            # để AI Server biết đâu là điểm bắt đầu/kết thúc của mỗi file ảnh.
            proxy_headers = {'Content-Type': original_content_type}
            if self.headers.get('Authorization'):
                proxy_headers['Authorization'] = self.headers.get('Authorization')

            response = requests.post(
                SERVER_PROCESSING_URL,
                data=image_data,
                headers=proxy_headers, 
                timeout=300 # Gửi nhiều ảnh xử lý sẽ lâu hơn, tăng timeout lên 5 phút
            )

            # 3. Trả kết quả về cho trình duyệt
            # Lấy Content-Type mà AI Server trả về (thường là application/pdf hoặc image/jpeg)
            return_content_type = response.headers.get('Content-Type', 'application/pdf')
            
            self.send_response(response.status_code)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-type', return_content_type)
            self.end_headers()
            self.wfile.write(response.content)
            print(f"--- Phan hoi tu AI Server: {response.status_code} ---")

        except requests.exceptions.Timeout:
            print(f"Loi Proxy: Timeout khi goi AI Server ({SERVER_PROCESSING_URL})")
            self._send_error(504, "AI Server Timeout - Qua thoi gian xu ly (5 phut)")
        except requests.exceptions.ConnectionError:
            print(f"Loi Proxy: Khong the ket noi toi AI Server ({SERVER_PROCESSING_URL})")
            self._send_error(502, "AI Server Offline - Khong the ket noi toi may chu scan")
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = str(e).encode('utf-8').decode('ascii', 'ignore')
            print(f"Loi Proxy: {error_msg}")
            self._send_error(500, f"Internal Proxy Error: {error_msg}")

    def _send_error(self, code, message):
        try:
            self.send_response(code)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(message.encode('utf-8'))
        except:
            pass # Connection might already be closed

if __name__ == "__main__":
    from http.server import HTTPServer
    server = HTTPServer(('0.0.0.0', 8080), handler)
    print("Proxy ho tro MULTIPLE FILES dang chay tai: http://localhost:8080")
    server.serve_forever()

if __name__ == "__main__":
    server = HTTPServer(('0.0.0.0', 8080), handler)
    print("Proxy ho tro MULTIPLE FILES dang chay tai: http://localhost:8080")
    server.serve_forever()