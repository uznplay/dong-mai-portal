export default function handler(req, res) {
  // Chỉ những biến PUBLIC mới được thêm vào đây
  // Tuyệt đối KHÔNG thêm: OPENROUTER_KEY, SUPABASE_SERVICE_ROLE_KEY, etc.
  const publicEnvMappings = [
    ['SCAN_API_URL', 'scanApiUrl'],
    // Các biến public khác thêm vào đây
    // Format: ['TEN_BIEN_TRONG_ENV', 'tenKeyTraVeClient']
  ];

  const publicEnv = {};

  for (const [envName, jsonKey] of publicEnvMappings) {
    if (process.env[envName] !== undefined) {
      publicEnv[jsonKey] = process.env[envName];
    }
  }

  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 'no-store');
  return res.status(200).json({ env: publicEnv });
}
