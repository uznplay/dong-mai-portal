
import http.server
import socketserver
import os
import sys
import importlib.util

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

except Exception as e:
    print(f"Error importing API modules: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("All API modules loaded successfully", flush=True)

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

    def end_headers(self):
        # Allow no-cache so html files aren't cached locally during dev
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

class UnifiedServer(socketserver.TCPServer):
    allow_reuse_address = True

print(f"Starting server at http://localhost:{PORT}")
print("Serving static files and API endpoints...")

with UnifiedServer(("", PORT), UnifiedHandler) as httpd:
    httpd.serve_forever()
