import json
import os
import base64
from http.server import BaseHTTPRequestHandler

env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    from dotenv import load_dotenv
    load_dotenv(env_path)
else:
    from dotenv import load_dotenv
    load_dotenv()

from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Rate limiting (in-memory)
_rate_map = {}

# Table whitelist
ALLOWED_TABLES = ["featured_news", "admin_users"]

import time as _time


def _rate_limit(ip):
    now = int(_time.time())
    WINDOW = 10
    MAX = 30
    entry = _rate_map.get(ip)
    if entry:
        start, count = entry
        if now - start < WINDOW:
            if count >= MAX:
                return False
            _rate_map[ip] = (start, count + 1)
        else:
            _rate_map[ip] = (now, 1)
    else:
        _rate_map[ip] = (now, 1)
    return True


def _send(handler, status, data):
    handler.send_response(status)
    handler.send_header('Content-type', 'application/json')
    handler.send_header('Cache-Control', 'no-store')
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.end_headers()
    handler.wfile.write(json.dumps(data).encode('utf-8'))


class handler(BaseHTTPRequestHandler):
    """Vercel/serverless: Standard BaseHTTPRequestHandler"""

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        """Standard Vercel POST handler"""
        try:
            client_ip = self.headers.get('X-Forwarded-For', self.client_address[0]).split(',')[0].strip()
        except (AttributeError, IndexError):
            client_ip = 'unknown'

        if not _rate_limit(client_ip):
            _send(self, 429, {'error': 'Too many requests. Please slow down.'})
            return

        if not supabase:
            _send(self, 500, {'error': 'Supabase not configured'})
            return

        try:
            content_len = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(content_len)
            body = json.loads(raw.decode('utf-8'))

            # Decode Base64-encoded payload (if any)
            encoded = body.get('payload', '')
            if encoded:
                decoded = base64.b64decode(encoded).decode('utf-8')
                body = json.loads(decoded)

            table = body.get('table', '')
            action = body.get('action', 'select')
            params = body.get('params', {})

            if action != 'auth' and table not in ALLOWED_TABLES:
                _send(self, 403, {'error': 'Table not allowed'})
                return

            if action == 'select':
                query = supabase.table(table).select(params.get('select', '*'))
                for col, val in params.get('eq', {}).items():
                    query = query.eq(col, val)
                for col, val in params.get('neq', {}).items():
                    query = query.neq(col, val)
                
                of = params.get('or')
                if of:
                    query = query.or_(of)

                ord_ = params.get('order')
                if ord_:
                    col = ord_.get('column', 'published_at')
                    asc = ord_.get('ascending', False)
                    query = query.order(col, desc=not asc)

                lim = params.get('limit')
                if lim:
                    query = query.limit(lim)

                if params.get('single'):
                    result = query.single().execute()
                else:
                    result = query.execute()
                
                _send(self, 200, {'data': result.data})

            elif action == 'insert':
                result = supabase.table(table).insert(params.get('values')).execute()
                _send(self, 200, {'data': result.data})

            elif action == 'update':
                result = supabase.table(table).update(params.get('values')).eq('id', params.get('id')).execute()
                _send(self, 200, {'data': result.data})

            elif action == 'delete':
                result = supabase.table(table).delete().eq('id', params.get('id')).execute()
                _send(self, 200, {'data': result.data})

            elif action == 'auth':
                method = params.get('method', '')
                creds = params.get('creds', {})
                if method == 'signInWithPassword':
                    try:
                        res = supabase.auth.sign_in_with_password(creds)
                        # Return in a format similar to supabase-js v2
                        # Ensure we convert the session/user objects to dicts
                        session_dict = None
                        if res.session:
                            session_dict = {
                                'access_token': res.session.access_token,
                                'refresh_token': res.session.refresh_token,
                                'expires_in': res.session.expires_in,
                                'token_type': res.session.token_type,
                                'user': {
                                    'id': res.user.id,
                                    'email': res.user.email,
                                }
                            }
                        user_dict = None
                        if res.user:
                            user_dict = {
                                'id': res.user.id,
                                'email': res.user.email,
                            }
                        _send(self, 200, {'data': {'user': user_dict, 'session': session_dict}, 'error': None})
                    except Exception as e:
                        _send(self, 200, {'data': {'user': None, 'session': None}, 'error': {'message': str(e)}})
                else:
                    _send(self, 400, {'error': f'Unknown auth method: {method}'})

            else:
                _send(self, 400, {'error': f'Unknown action: {action}'})

        except Exception as e:
            import traceback
            traceback.print_exc()
            _send(self, 500, {'error': f'Server error: {e}'})


# Python HTTP Server: called by UnifiedHandler in run_server.py
def python_do_POST(server_handler):
    """Called by run_server.py: api.news.python_do_POST(self)"""
    if not hasattr(server_handler, 'path') or server_handler.path != '/api/news':
        return False  # Not handled, pass through

    try:
        ip = getattr(server_handler, 'client_address', ('0.0.0.0', 0))[0]
    except Exception:
        ip = 'unknown'

    if not _rate_limit(ip):
        _send(server_handler, 429, {'error': 'Too many requests. Please slow down.'})
        return True

    if not supabase:
        _send(server_handler, 500, {'error': 'Supabase not configured'})
        return True

    try:
        content_len = int(server_handler.headers.get('Content-Length', 0))
        raw = server_handler.rfile.read(content_len)
        body = json.loads(raw.decode('utf-8'))

        # Decode Base64-encoded payload
        encoded = body.get('payload', '')
        if encoded:
            decoded = base64.b64decode(encoded).decode('utf-8')
            body = json.loads(decoded)

        table = body.get('table', '')
        action = body.get('action', 'select') # default to select
        params = body.get('params', {})

        if action != 'auth' and table not in ALLOWED_TABLES:
            _send(server_handler, 403, {'error': 'Table not allowed'})
            return True

        if action == 'select':
            query = supabase.table(table).select(params.get('select', '*'))
            for col, val in params.get('eq', {}).items():
                query = query.eq(col, val)
            for col, val in params.get('neq', {}).items():
                query = query.neq(col, val)
            
            of = params.get('or')
            if of:
                query = query.or_(of)

            ord_ = params.get('order')
            if ord_:
                col = ord_.get('column', 'published_at')
                asc = ord_.get('ascending', False)
                query = query.order(col, desc=not asc)

            lim = params.get('limit')
            if lim:
                query = query.limit(lim)

            if params.get('single'):
                result = query.single().execute()
            else:
                result = query.execute()
            
            _send(server_handler, 200, {'data': result.data})
            
        elif action == 'insert':
            result = supabase.table(table).insert(params.get('values')).execute()
            _send(server_handler, 200, {'data': result.data})
            
        elif action == 'update':
            result = supabase.table(table).update(params.get('values')).eq('id', params.get('id')).execute()
            _send(server_handler, 200, {'data': result.data})
            
        elif action == 'delete':
            result = supabase.table(table).delete().eq('id', params.get('id')).execute()
            _send(server_handler, 200, {'data': result.data})

        elif action == 'auth':
            method = params.get('method', '')
            creds = params.get('creds', {})
            if method == 'signInWithPassword':
                try:
                    res = supabase.auth.sign_in_with_password(creds)
                    session_dict = None
                    if res.session:
                        session_dict = {
                            'access_token': res.session.access_token,
                            'refresh_token': res.session.refresh_token,
                            'expires_in': res.session.expires_in,
                            'token_type': res.session.token_type,
                            'user': {
                                'id': res.user.id,
                                'email': res.user.email,
                            }
                        }
                    user_dict = None
                    if res.user:
                        user_dict = {
                            'id': res.user.id,
                            'email': res.user.email,
                        }
                    _send(server_handler, 200, {'data': {'user': user_dict, 'session': session_dict}, 'error': None})
                except Exception as e:
                    _send(server_handler, 200, {'data': {'user': None, 'session': None}, 'error': {'message': str(e)}})
            else:
                _send(server_handler, 400, {'error': f'Unknown auth method: {method}'})

    except Exception as e:
        import traceback
        traceback.print_exc()
        _send(server_handler, 500, {'error': f'Server error: {e}'})

    return True
