(function() {
  'use strict';

  var cdnLoading = false;
  var CDN = 'https://cdn.jsdelivr.net/npm/disable-devtool@0.3.9/disable-devtool.min.js';

  function fetchWithTimeout(url, timeout) {
    timeout = timeout || 5000;
    return Promise.race([
      fetch(url, { cache: 'no-store' }),
      new Promise(function(_, reject) {
        setTimeout(function() { reject(new Error('timeout')); }, timeout);
      })
    ]);
  }

  function loadScriptAndInit(ddConfig) {
    if (!ddConfig || !ddConfig.enabled) return;
    if (cdnLoading) return;
    if (document.querySelector('script[src*="disable-devtool"]')) return;
    cdnLoading = true;

    var script = document.createElement('script');
    script.src = CDN;
    script.crossOrigin = 'anonymous';
    script.onload = function() {
      var fn = typeof DisableDevtool !== 'undefined' ? DisableDevtool
        : (typeof window.disableDevtool === 'function' ? window.disableDevtool : null);
      if (typeof fn !== 'function') {
        console.warn('[security.js] Không tìm thấy DisableDevtool sau khi tải CDN');
        return;
      }
      fn({
        disableMenu: ddConfig.disableMenu !== false,
        disableSelect: ddConfig.disableSelect === true,
        disableCopy: ddConfig.disableCopy === true,
        disableCut: ddConfig.disableCut === true,
        disablePaste: ddConfig.disablePaste !== false,
        detectors: ddConfig.detectors || [0, 1, 2, 3, 4, 5, 6, 7],
        interval: ddConfig.interval || 200,
        ondevtoolopen: function(type, next) {
          if (navigator.sendBeacon) {
            navigator.sendBeacon('/api/security-log', JSON.stringify({
              event: 'devtool_open',
              type: type,
              timestamp: new Date().toISOString()
            }));
          }
          next();
        }
      });
    };
    script.onerror = function() {
      console.warn('[security.js] Không tải được disable-devtool từ CDN:', CDN);
      // Fallback: Chặn tất cả (chuột phải, select, copy, cut) nhưng cho phép PASTE như user yêu cầu
      console.log('[security.js] Kích hoạt chế độ bảo vệ fallback (Native)');
      
      document.addEventListener('contextmenu', function(e) { e.preventDefault(); }, false);
      document.addEventListener('selectstart', function(e) { e.preventDefault(); }, false);
      document.addEventListener('copy', function(e) { e.preventDefault(); }, false);
      document.addEventListener('cut', function(e) { e.preventDefault(); }, false);
      
      // Paste vẫn được phép (không chặn)
    };
    document.head.appendChild(script);
  }

  function tryApply(data) {
    if (!data || !data.disableDevtool || !data.disableDevtool.enabled) return;
    loadScriptAndInit(data.disableDevtool);
  }

  // 1) Trang có inject (index.html, admin) — áp dụng ngay, không chờ mạng
  if (typeof window !== 'undefined' && window.SERVER_SECURITY_CONFIG) {
    tryApply(window.SERVER_SECURITY_CONFIG);
  }

  // 2) Các trang chỉ có fetch (huong-dan, tin-noi-bat, …) hoặc bổ sung nếu inject = null
  fetchWithTimeout('/api/security-config')
    .then(function(r) {
      if (!r || !r.ok) throw new Error('HTTP ' + (r ? r.status : '?'));
      return r.json();
    })
    .then(function(data) {
      tryApply(data);
    })
    .catch(function(err) {
      if (!cdnLoading && !document.querySelector('script[src*="disable-devtool"]')) {
        console.warn('[security.js] Không lấy được /api/security-config — chạy python run_server.py và mở http://localhost:8000/...', err && err.message ? err.message : err);
      }
    });
})();
