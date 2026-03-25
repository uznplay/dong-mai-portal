import http.server
import socketserver
import os
import sys
import importlib.util
import json
import re

# Load .env before importing API modules
from dotenv import load_dotenv
load_dotenv()

# Debug output
print("Starting server...", flush=True)

# Ensure current directory is in sys.path
sys.path.append(os.getcwd())
print(f"CWD: {os.getcwd()}", flush=True)

# Import API handlers dynamically to avoid import errors if deps are missing (handled by main script try/except)
try:
    import api.chatbot
    print("chatbot imported", flush=True)
    import api.feedback
    print("feedback imported", flush=True)
    import api.security_config
    print("security_config imported", flush=True)
    import api.config
    print("config imported", flush=True)
    import api.news
    print("news imported", flush=True)

except Exception as e:
    print(f"Error importing API modules: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("All API modules loaded successfully", flush=True)

PORT = 8000

# Security config cache
_security_config_cache = None

def get_security_config():
    """Get security config for injection"""
    global _security_config_cache
    if _security_config_cache is None:
        _security_config_cache = api.security_config.config.get_config()
    return _security_config_cache

def inject_security_config_into_html(html_content):
    """Inject security config into HTML as inline JS"""
    config_json = json.dumps(get_security_config())
    # Replace the placeholder with actual config (dùng [\s\S]*? vì JSON có thể chứa dấu / trong URL)
    pattern = r'/\*INJECT_SECURITY_CONFIG\*/[\s\S]*?/\*END_INJECT\*/'
    replacement = f'/*INJECT_SECURITY_CONFIG*/{config_json}/*END_INJECT*/'
    html_content = re.sub(pattern, replacement, html_content)

    # Also inject SERVER_ENV (SCAN_API_URL and other client-side env vars)
    server_env = {
        k[10:]: v  # strip "SERVER_ENV_" prefix
        for k, v in os.environ.items()
        if k.startswith("SERVER_ENV_") and v
    }
    env_json = json.dumps(server_env)
    env_pattern = r'/\*INJECT_SERVER_ENV\*/[\s\S]*?/\*END_INJECT\*/'
    env_replacement = f'/*INJECT_SERVER_ENV*/window.SERVER_ENV={env_json};/*END_INJECT*/'
    html_content = re.sub(env_pattern, env_replacement, html_content)
    return html_content


class UnifiedHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        # Route API requests
        if self.path == '/api/chatbot':
            print(f"Routing POST {self.path} to api.chatbot")
            # Call the do_POST method of the chatbot handler, passing 'self'
            # effective monkey-patching / mixin behavior
            api.chatbot.handler.do_POST(self)
            return
            
        if self.path == '/api/feedback':
            print(f"Routing POST {self.path} to api.feedback")
            api.feedback.handler.do_POST(self)
            return

        if self.path == '/api/security-config/update':
            print(f"Routing POST {self.path} to api.security_config")
            api.security_config.handler.do_POST(self)
            return

        if self.path == '/api/news':
            print(f"Routing POST {self.path} to api.news")
            api.news.python_do_POST(self)
            return

    def do_OPTIONS(self):
        if self.path == '/api/news':
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            return
        super().do_OPTIONS()

    def do_GET(self):
        # Route API requests (if any GET endpoints exist)
        if self.path == '/api/chatbot':
             api.chatbot.handler.do_GET(self)
             return

        if self.path == '/api/feedback':
             api.feedback.handler.do_GET(self)
             return

        if self.path == '/api/security-config':
             api.security_config.handler.do_GET(self)
             return

        if self.path == '/api/config':
             api.config.handler.do_GET(self)
             return

        # Check if requesting index.html - inject security config
        if self.path == '/' or self.path == '/index.html':
            filepath = os.path.join(os.getcwd(), 'index.html')
            if self.serve_html_with_config(filepath):
                return

        # Check if it's an HTML file - inject security config for ALL HTML files
        if self.path.endswith('.html'):
            filepath = os.path.join(os.getcwd(), self.path.lstrip('/'))
            if os.path.exists(filepath) and filepath.endswith('.html'):
                if self.serve_html_with_config(filepath):
                    return

        # Serve static files
        super().do_GET()

    def end_headers(self):
        # Allow no-cache so html files aren't cached locally during dev
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def translate_path(self, path):
        """Override to handle index.html with config injection"""
        # Get the base path
        result = super().translate_path(path)
        return result
    
    def serve_html_with_config(self, filepath):
        """Serve HTML file with security config injected"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Inject security config + SERVER_ENV nếu có placeholder (PDF miniapp có thể chỉ có SERVER_ENV)
            if '/*INJECT_SECURITY_CONFIG*/' in content or '/*INJECT_SERVER_ENV*/' in content:
                content = inject_security_config_into_html(content)
                print(f"[Config] Injected security/env into {filepath}")
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
            return True
        except Exception as e:
            print(f"Error serving HTML: {e}")
            return False

class UnifiedServer(socketserver.TCPServer):
    allow_reuse_address = True

print(f"Starting server at http://localhost:{PORT}")
print("Serving static files and API endpoints...")

with UnifiedServer(("", PORT), UnifiedHandler) as httpd:
    httpd.serve_forever()
