// Rate limiting — in-memory store (resets on cold start / serverless)
// For production with multiple instances, use Redis or Supabase table.
const rateLimitMap = new Map();

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Cache-Control', 'no-store');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // --- RATE LIMITING ---
  const clientIp = req.headers['x-forwarded-for']?.split(',')[0]?.trim()
                 || req.headers['x-real-ip']
                 || 'unknown';
  const now = Date.now();
  const WINDOW_MS = 10_000;   // 10 seconds
  const MAX_REQUESTS = 30;     // 30 requests per 10 seconds per IP

  const entry = rateLimitMap.get(clientIp);
  if (entry && now - entry.start < WINDOW_MS) {
    if (entry.count >= MAX_REQUESTS) {
      return res.status(429).json({ error: 'Too many requests. Please slow down.' });
    }
    entry.count++;
  } else {
    rateLimitMap.set(clientIp, { start: now, count: 1 });
  }

  // Periodic cleanup of stale entries (every ~100 requests)
  if (Math.random() < 0.01) {
    for (const [ip, v] of rateLimitMap.entries()) {
      if (now - v.start > WINDOW_MS) rateLimitMap.delete(ip);
    }
  }

  try {
    let body = req.body;
    if (typeof body === 'string') {
      body = JSON.parse(body);
    }
    if (body && body.payload) {
      const decoded = Buffer.from(String(body.payload), 'base64').toString('utf8');
      body = JSON.parse(decoded);
    }
    const { table, action, params } = body || {};

    // Validate table - only allow specific tables
    const allowedTables = ['featured_news'];
    if (!allowedTables.includes(table)) {
      return res.status(403).json({ error: 'Table not allowed' });
    }

    // Import Supabase client SERVER-SIDE only
    // Key stays on server, never sent to browser
    const { createClient } = await import('@supabase/supabase-js');
    const supabase = createClient(
      process.env.SUPABASE_URL,
      process.env.SUPABASE_KEY  // server-side key (not sent to browser)
    );

    let result;

    switch (action) {
      case 'select': {
        let query = supabase.from(table).select(params.select || '*');

        // Apply filters
        if (params.eq) {
          for (const [col, val] of Object.entries(params.eq)) {
            query = query.eq(col, val);
          }
        }
        if (params.neq) {
          for (const [col, val] of Object.entries(params.neq)) {
            query = query.neq(col, val);
          }
        }
        if (params.not && Array.isArray(params.not) && params.not.length >= 3) {
          const [col, op, val] = params.not;
          query = query.not(col, op, val);
        }
        if (params.or) {
          query = query.or(params.or);
        }
        if (params.order) {
          query = query.order(params.order.column || 'published_at', {
            ascending: params.order.ascending !== false
          });
        }
        if (params.limit) {
          query = query.limit(params.limit);
        }
        if (params.single) {
          result = await query.single();
        } else {
          result = await query;
        }
        break;
      }

      case 'insert': {
        result = await supabase.from(table).insert(params.values).select().single();
        break;
      }

      case 'update': {
        result = await supabase.from(table).update(params.values).eq('id', params.id).select().single();
        break;
      }

      case 'delete': {
        result = await supabase.from(table).delete().eq('id', params.id);
        break;
      }

      default:
        return res.status(400).json({ error: 'Unknown action' });
    }

    if (result.error) {
      return res.status(400).json({ error: result.error.message });
    }

    return res.status(200).json({ data: result.data });

  } catch (err) {
    console.error('News API error:', err);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
