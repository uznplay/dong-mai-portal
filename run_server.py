
import http.server
import socketserver
import os
import sys
import importlib.util

# Ensure current directory is in sys.path
sys.path.append(os.getcwd())

# Import API handlers dynamically to avoid import errors if deps are missing (handled by main script try/except)
try:
    import api.chatbot
    import api.feedback
except ImportError as e:
    print(f"Error importing API modules: {e}")
    print("Make sure you have installed requirements.txt")
    sys.exit(1)

PORT = 8000

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

        # Serve static files
        super().do_GET()

class UnifiedServer(socketserver.TCPServer):
    allow_reuse_address = True

print(f"Starting server at http://localhost:{PORT}")
print("Serving static files and API endpoints...")

with UnifiedServer(("", PORT), UnifiedHandler) as httpd:
    httpd.serve_forever()
