(function() {
  var config = window.SERVER_SECURITY_CONFIG;
  
  const applyConfig = (ddConfig) => {
    if (!ddConfig || !ddConfig.enabled) {
      console.log('[Security] DevTools protection is disabled by server');
      return;
    }
    console.log('[Security] Loading DevTools protection with config:', ddConfig);
    
    // Check if script already exists to avoid duplication
    if (document.querySelector('script[src*="disable-devtool"]')) return;

    var script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/disable-devtool';
    script.onload = function() {
      if (typeof DisableDevtool === 'function') {
        DisableDevtool({
          disableMenu: ddConfig.disableMenu !== false,
          disableSelect: ddConfig.disableSelect === true,
          disableCopy: ddConfig.disableCopy === true,
          disableCut: ddConfig.disableCut === true,
          disablePaste: ddConfig.disablePaste !== false,
          detectors: ddConfig.detectors || [0, 1, 2, 3, 4, 5, 6, 7],
          interval: ddConfig.interval || 200,
          ondevtoolopen: function(type, next) {
            console.warn('[Security] DevTools detected! Type:', type);
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
        console.log('[Security] DevTools protection activated');
      }
    };
    script.onerror = function() {
      console.error('[Security] Failed to load disable-devtool');
    };
    document.head.appendChild(script);
  };

  if (config) {
    applyConfig(config.disableDevtool);
  } else {
    // Fallback for environment without injection
    fetch('/api/security-config')
      .then(r => r.json())
      .then(data => {
        if (data && data.disableDevtool) {
          applyConfig(data.disableDevtool);
        }
      })
      .catch(e => {
        console.warn('[Security] Could not fetch server config, using local defaults', e);
        // Default: Enable protection by default if we can't reach server
        applyConfig({enabled: true});
      });
  }
})();
