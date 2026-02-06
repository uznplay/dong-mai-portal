from http.server import BaseHTTPRequestHandler
import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_POST(self):
        """Create new admin user"""
        try:
            # CORS headers
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Validate environment variables
            if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
                self.wfile.write(json.dumps({
                    'error': 'Server configuration error: Missing Supabase credentials'
                }).encode())
                return
            
            # Parse request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            
            email = data.get('email')
            password = data.get('password')
            full_name = data.get('full_name', '')
            
            # Validate input
            if not email or not password:
                self.wfile.write(json.dumps({
                    'error': 'Email and password are required'
                }).encode())
                return
            
            if len(password) < 6:
                self.wfile.write(json.dumps({
                    'error': 'Password must be at least 6 characters'
                }).encode())
                return
            
            # Create user via Supabase Admin API
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
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
                    'Content-Type': 'application/json',
                    'apikey': SUPABASE_SERVICE_KEY
                },
                method='POST'
            )
            
            try:
                with urlopen(req) as response:
                    response_data = json.loads(response.read().decode('utf-8'))
                    
                    self.wfile.write(json.dumps({
                        'success': True,
                        'user': {
                            'id': response_data.get('id'),
                            'email': response_data.get('email'),
                            'created_at': response_data.get('created_at')
                        }
                    }).encode())
                    
            except HTTPError as e:
                error_body = e.read().decode('utf-8')
                error_data = json.loads(error_body)
                
                self.wfile.write(json.dumps({
                    'error': error_data.get('msg', 'Failed to create user'),
                    'details': error_data
                }).encode())
                
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'Invalid JSON in request body'
            }).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': f'Internal server error: {str(e)}'
            }).encode())
