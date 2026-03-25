from http.server import BaseHTTPRequestHandler, HTTPServer
import requests

from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

# URL của AI Server (phải đảm bảo AI Server cũng nhận Multipart/FormData)
SERVER_PROCESSING_URL = "http://localhost:8000/api/scanner"

class handler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        # CORS Headers - Cho phép frontend gọi vào
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-type', content_type)
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_POST(self):
        try:
            # 1. Lấy Content-Type từ trình duyệt (bao gồm cả chuỗi 'boundary' cực kỳ quan trọng)
            original_content_type = self.headers.get('Content-Type')
            content_length = int(self.headers.get('Content-Length', 0))
            
            # Đọc toàn bộ body (dạng binary)
            image_data = self.rfile.read(content_length)

            if not image_data:
                self._set_headers(400)
                self.wfile.write(b'{"error": "Du lieu trong"}')
                return

            print(f"--- Dang chuyen tiep anh toi AI Server ---")

            # 2. Chuyển tiếp nguyên văn sang AI Server
            # QUAN TRỌNG: Phải gửi kèm headers={'Content-Type': original_content_type}
            # để AI Server biết đâu là điểm bắt đầu/kết thúc của mỗi file ảnh.
            response = requests.post(
                SERVER_PROCESSING_URL,
                data=image_data,
                headers={'Content-Type': original_content_type}, 
                timeout=300 # Gửi nhiều ảnh xử lý sẽ lâu hơn, tăng timeout lên 5 phút
            )

            # 3. Trả kết quả về cho trình duyệt
            # Lấy Content-Type mà AI Server trả về (thường là application/pdf hoặc image/jpeg)
            return_content_type = response.headers.get('Content-Type', 'application/pdf')
            
            self._set_headers(response.status_code, return_content_type)
            self.wfile.write(response.content)
            print(f"--- Phan hoi tu AI Server: {response.status_code} ---")

        except Exception as e:
            # Fix lỗi 'latin-1' bằng cách encode utf-8 trước khi in hoặc gửi
            error_msg = str(e).encode('utf-8').decode('ascii', 'ignore')
            print(f"Loi Proxy: {error_msg}")
            
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(f"Internal Proxy Error: {error_msg}".encode('utf-8'))

if __name__ == "__main__":
    server = HTTPServer(('0.0.0.0', 8080), handler)
    print("Proxy ho tro MULTIPLE FILES dang chay tai: http://localhost:8080")
    server.serve_forever()