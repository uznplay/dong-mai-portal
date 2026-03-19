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
    # Replace the placeholder with actual config
    pattern = r'/\*INJECT_SECURITY_CONFIG\*/[^/]+/\*END_INJECT\*/'
    replacement = f'/*INJECT_SECURITY_CONFIG*/{config_json}/*END_INJECT*/'
    return re.sub(pattern, replacement, html_content)


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


        # Default behavior for other POSTs (if any, otherwise 404 or 501)
        super().do_POST()

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
            
            # Check if this HTML needs config injection
            if '/*INJECT_SECURITY_CONFIG*/' in content:
                content = inject_security_config_into_html(content)
                print(f"[Security] Injected config into {filepath}")
            
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
