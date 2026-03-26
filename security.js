(function() {
  'use strict';

  var LOCAL_SCRIPT = '/js/portal-security.js';
  var initialized = false;

  function init(config) {
    if (initialized) return;
    if (!config || config.enabled === false) return;
    
    var fn = typeof DisableDevtool !== 'undefined' ? DisableDevtool
           : (typeof window.disableDevtool === 'function' ? window.disableDevtool : null);
    
    if (typeof fn === 'function') {
      initialized = true;
      fn({
        disableMenu: config.disableMenu !== false,
        disableSelect: config.disableSelect === true,
        disableCopy: config.disableCopy === true,
        disableCut: config.disableCut === true,
        disablePaste: config.disablePaste !== false,
        detectors: config.detectors || [0, 1, 2, 3, 4, 5, 6, 7],
        interval: config.interval || 200,
        ondevtoolopen: function(type, next) {
          console.warn('[Security] DevTools detected:', type);
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
    }
  }

  function loadAndInit(data) {
    if (document.querySelector('script[src*="disable-devtool"]')) {
      init(data.disableDevtool);
      return;
    }

    var script = document.createElement('script');
    script.src = LOCAL_SCRIPT;
    script.onload = function() {
      init(data.disableDevtool);
    };
    script.onerror = function() {
      console.error('[Security] Critical: Local security script blocked. Activating High-Level Native Protection.');
      
      // 1. Chặn chuột phải
      document.addEventListener('contextmenu', function(e) { e.preventDefault(); }, true);
      
      // 2. Chặn phím tắt (F12, Ctrl+Shift+I, Ctrl+Shift+C, Ctrl+U)
      document.addEventListener('keydown', function(e) {
        if (
          e.keyCode === 123 || // F12
          (e.ctrlKey && e.shiftKey && (e.keyCode === 73 || e.keyCode === 67 || e.keyCode === 74)) || // Ctrl+Shift+I/C/J
          (e.ctrlKey && e.keyCode === 85) // Ctrl+U
        ) {
          e.preventDefault();
          return false;
        }
      }, true);

      // 3. Chặn bôi đen và copy
      document.addEventListener('selectstart', function(e) { e.preventDefault(); }, true);
      document.addEventListener('copy', function(e) { e.preventDefault(); }, true);
      document.addEventListener('cut', function(e) { e.preventDefault(); }, true);
      
      // 4. Liên tục xóa console (nếu devtool vẫn mở được)
      setInterval(function() {
        console.clear();
      }, 1000);
    };
    document.head.appendChild(script);
  }

  // 1) Ưu tiên dùng config đã được inject sẵn vào window
  if (window.SERVER_SECURITY_CONFIG && window.SERVER_SECURITY_CONFIG.disableDevtool) {
    loadAndInit(window.SERVER_SECURITY_CONFIG);
  } else {
    // 2) Nếu không có thì fetch từ API
    fetch('/api/security-config')
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data && data.disableDevtool) {
          loadAndInit(data);
        } else {
          throw new Error('Invalid config');
        }
      })
      .catch(function(err) {
        console.warn('[Security] API Failure. Activating High-Level Fallback.');
        loadAndInit({
          disableDevtool: { enabled: true, disableMenu: true }
        });
      });
  }
})();
