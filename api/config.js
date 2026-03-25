export default function handler(req, res) {
  // Trả URL + KEY cho admin auth (client-side Supabase auth)
  // Public news queries KHÔNG dùng Supabase client nữa — qua /api/news proxy
  const supabaseConfig = {
    url: process.env.SUPABASE_URL || '',
    key: process.env.SUPABASE_KEY || ''   // Dùng cho admin auth (signInWithPassword)
  };

  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 'no-store');
  return res.status(200).json(supabaseConfig);
}
