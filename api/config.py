import json
import os
from http.server import BaseHTTPRequestHandler

# Load .env
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    from dotenv import load_dotenv
    load_dotenv(env_path)
else:
    from dotenv import load_dotenv
    load_dotenv()


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        """Trả về Supabase config (URL + anon key) từ server env"""
        if '/api/config' in self.path:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.end_headers()

            config = {
                'url': os.getenv('SUPABASE_URL', ''),
                'key': os.getenv('SUPABASE_KEY', '')
            }

            self.wfile.write(json.dumps(config).encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()
