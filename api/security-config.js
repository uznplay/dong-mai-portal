// Phải khớp tên biến với api/security_config.py và file .env
function envBool(key, defaultVal) {
  const raw = process.env[key];
  const v = raw === undefined || raw === '' ? String(defaultVal) : String(raw);
  const s = v.trim().replace(/^["']|["']$/g, '').toLowerCase();
  return s === 'true' || s === '1' || s === 'yes' || s === 'on';
}

function envInt(key, def) {
  const raw = process.env[key];
  const v = raw === undefined || raw === '' ? String(def) : String(raw);
  const n = parseInt(v.trim().replace(/^["']|["']$/g, ''), 10);
  return Number.isFinite(n) ? n : def;
}

function envDetectors() {
  const raw = process.env.DISABLE_DEVTOOL_DETECTORS || '0 1 2 3 4 5 6 7';
  const parts = String(raw).replace(/,/g, ' ').split(/\s+/).filter(Boolean);
  const out = [];
  for (const p of parts) {
    const n = parseInt(p.trim().replace(/^["']|["']$/g, ''), 10);
    if (Number.isFinite(n)) out.push(n);
  }
  return out.length ? out : [0, 1, 2, 3, 4, 5, 6, 7];
}

export default function handler(req, res) {
  const securityConfig = {
    disableDevtool: {
      enabled: envBool('DISABLE_DEVTOOL_ENABLED', 'true'),
      disableMenu: envBool('DISABLE_DEVTOOL_DISABLE_MENU', 'true'),
      disableSelect: envBool('DISABLE_DEVTOOL_DISABLE_SELECT', 'false'),
      disableCopy: envBool('DISABLE_DEVTOOL_DISABLE_COPY', 'false'),
      disableCut: envBool('DISABLE_DEVTOOL_DISABLE_CUT', 'false'),
      disablePaste: envBool('DISABLE_DEVTOOL_DISABLE_PASTE', 'false'),
      detectors: envDetectors(),
      interval: envInt('DISABLE_DEVTOOL_INTERVAL', 200),
    },
    security: {
      enabled: envBool('SECURITY_ENABLED', 'true'),
    },
  };

  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 'no-store');
  return res.status(200).json(securityConfig);
}
