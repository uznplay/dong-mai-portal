import json
import os
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    """API handler to return public environment variables"""
    def do_GET(self):
        # Only PUBLIC variables should be added here
        # Format: (ENV_NAME_IN_SERVER, KEY_NAME_FOR_CLIENT)
        public_env_mappings = [
            ('SCAN_API_URL', 'scanApiUrl'),
        ]
        
        public_env = {}
        for env_name, json_key in public_env_mappings:
            # Check both name and SERVER_ENV_ prefix (fallback for local run_server.py)
            val = os.getenv(env_name) or os.getenv(f"SERVER_ENV_{env_name}")
            if val is not None:
                public_env[json_key] = val
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        
        self.wfile.write(json.dumps({"env": public_env}).encode('utf-8'))
