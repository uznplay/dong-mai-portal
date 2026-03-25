(function() {
  'use strict';

  var API_BASE = window.API_BASE || '';

  function fetchConfig() {
    var url = API_BASE + '/api/config';
    return fetch(url, { cache: 'no-store' })
      .then(function(r) { return r ? r.json() : null; })
      .catch(function() { return null; });
  }

  function fetchSecurityConfig() {
    var url = API_BASE + '/api/security-config';
    return fetch(url, { cache: 'no-store' })
      .then(function(r) { return r ? r.json() : null; })
      .catch(function() { return null; });
  }

  function applyDevTools(data) {
    if (!data || !data.disableDevtool || !data.disableDevtool.enabled) return;
    if (document.querySelector('script[src*="disable-devtool"]')) return;

    var dd = data.disableDevtool;
    var script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/disable-devtool';
    script.onload = function() {
      if (typeof DisableDevtool === 'function') {
        DisableDevtool({
          disableMenu: dd.disableMenu !== false,
          disableSelect: dd.disableSelect === true,
          disableCopy: dd.disableCopy === true,
          disableCut: dd.disableCut === true,
          disablePaste: dd.disablePaste !== false,
          detectors: dd.detectors || [0, 1, 2, 3, 4, 5, 6, 7],
          interval: dd.interval || 200
        });
      }
    };
    document.head.appendChild(script);
  }

  Promise.all([fetchConfig(), fetchSecurityConfig()])
    .then(function(results) {
      var cfg = results[0];
      var sec = results[1];

      if (cfg && cfg.url && cfg.key && typeof supabase !== 'undefined' && typeof supabase.createClient === 'function') {
        window.SUPABASE_CONFIG = cfg;
        window.supabaseClient = supabase.createClient(cfg.url, cfg.key);
        window.supabase = window.supabaseClient;
      }

      applyDevTools(sec);
    });

})();
