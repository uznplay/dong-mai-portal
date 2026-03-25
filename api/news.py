import json
import os
import base64

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
ALLOWED_TABLES = ["featured_news"]

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


class handler:
    """Vercel/serverless: export default async function(req, res)"""

    @staticmethod
    def handle_event(event, context=None):
        """Vercel serverless function signature"""
        import urllib.request
        import urllib.error

        req = event
        if hasattr(req, 'method'):
            method = req.get('method', 'GET')
        else:
            method = 'GET'

        if method == 'OPTIONS':
            return {'statusCode': 200,
                    'headers': {'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                                'Access-Control-Allow-Headers': 'Content-Type'}}

        if method != 'POST':
            return {'statusCode': 405, 'body': json.dumps({'error': 'Method not allowed'})}

        body = {}
        if hasattr(req, 'get') and callable(req.get):
            body = req.get('body') or {}
        elif hasattr(req, 'body'):
            body = req.get('body', {}) if hasattr(req, 'get') else (req.body or {})

        if isinstance(body, str):
            body = json.loads(body)
        encoded = body.get('payload', '') if isinstance(body, dict) else ''
        if encoded:
            decoded = base64.b64decode(encoded).decode('utf-8')
            body = json.loads(decoded)

        ip = 'unknown'
        if hasattr(req, 'get'):
            ip = req.get('headers', {}).get('x-forwarded-for', 'unknown')
            if isinstance(ip, str) and ',' in ip:
                ip = ip.split(',')[0].strip()

        if not _rate_limit(ip):
            return {'statusCode': 429, 'body': json.dumps({'error': 'Too many requests'})}

        if not supabase:
            return {'statusCode': 500, 'body': json.dumps({'error': 'Supabase not configured'})}

        table = body.get('table', '')
        action = body.get('action', '')
        params = body.get('params', {})

        if table not in ALLOWED_TABLES:
            return {'statusCode': 403, 'body': json.dumps({'error': 'Table not allowed'})}

        try:
            query = supabase.table(table).select(params.get('select', '*'))

            for col, val in params.get('eq', {}).items():
                query = query.eq(col, val)
            for col, val in params.get('neq', {}).items():
                query = query.neq(col, val)

            # not filter không tương thích với supabase-py v2
            # RLS policy lọc tag "hướng dẫn" ở database

            of = params.get('or')
            if of:
                query = query.or_(of)

            ord = params.get('order')
            if ord:
                col = ord.get('column', 'published_at')
                asc = ord.get('ascending', False)
                query = query.order(col, desc=not asc)

            lim = params.get('limit')
            if lim:
                query = query.limit(lim)

            if params.get('single'):
                result = query.single().execute()
            else:
                result = query.execute()

            # supabase-py v2 dùng try/except, không có .error attribute
            return {'statusCode': 200,
                    'body': json.dumps({'data': result.data}),
                    'headers': {'Content-Type': 'application/json',
                                'Cache-Control': 'no-store',
                                'Access-Control-Allow-Origin': '*'}}

        except Exception as e:
            return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}


# Python HTTP Server: called by UnifiedHandler in run_server.py
def python_do_POST(handler):
    """Called by run_server.py: api.news.python_do_POST(self)"""
    from http.server import BaseHTTPRequestHandler

    if not hasattr(handler, 'path') or handler.path != '/api/news':
        return False  # Not handled, pass through

    try:
        ip = getattr(handler, 'client_address', ('0.0.0.0', 0))[0]
    except Exception:
        ip = 'unknown'

    if not _rate_limit(ip):
        _send(handler, 429, {'error': 'Too many requests. Please slow down.'})
        return True

    if not supabase:
        _send(handler, 500, {'error': 'Supabase not configured'})
        return True

    try:
        content_len = int(handler.headers.get('Content-Length', 0))
        raw = handler.rfile.read(content_len)
        body = json.loads(raw.decode('utf-8'))

        # Decode Base64-encoded payload
        encoded = body.get('payload', '')
        if encoded:
            decoded = base64.b64decode(encoded).decode('utf-8')
            body = json.loads(decoded)

        table = body.get('table', '')
        params = body.get('params', {})

        if table not in ALLOWED_TABLES:
            _send(handler, 403, {'error': 'Table not allowed'})
            return True

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

        _send(handler, 200, {'data': result.data})

    except Exception as e:
        import traceback
        traceback.print_exc()
        _send(handler, 500, {'error': f'Server error: {e}'})

    return True
