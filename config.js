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
    // 1. Cấu hình mặc định (Fallback) nếu API lỗi
    var defaultDevtool = {
      enabled: true,
      disableMenu: true,
      disableSelect: false,
      disableCopy: false,
      disableCut: false,
      disablePaste: false,
      detectors: [0, 1, 2, 3, 4, 5, 6, 7],
      interval: 500
    };

    var dd = (data && data.disableDevtool) ? data.disableDevtool : defaultDevtool;
    
    // Nếu không kích hoạt thì thoát
    if (!dd.enabled) return;
    
    // Tránh load lặp lại
    if (document.querySelector('script[src*="disable-devtool"]')) return;

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

      // Cơ chế Proxy Supabase (Bảo mật: Không lộ Key ra Frontend)
      if (cfg && cfg.mode === 'proxy') {
        console.log("[Config] Proxy Mode Enabled. Supabase Key remains on server.");
        
        var ProxyQueryBuilder = function(table) {
          this.table = table;
          this.action = 'select';
          this.params = {};
          this.isSingle = false;
        };

        ProxyQueryBuilder.prototype.select = function(cols) { this.params.select = cols || '*'; return this; };
        ProxyQueryBuilder.prototype.eq = function(col, val) { 
          if (!this.params.eq) this.params.eq = {}; 
          this.params.eq[col] = val; 
          if (col === 'id') this.params.id = val; // Tương thích với api/news.py cũ
          return this; 
        };
        ProxyQueryBuilder.prototype.neq = function(col, val) { 
          if (!this.params.neq) this.params.neq = {}; 
          this.params.neq[col] = val; 
          return this; 
        };
        ProxyQueryBuilder.prototype.order = function(col, opts) {
          this.params.order = { column: col, ascending: opts && opts.ascending !== false };
          return this;
        };
        ProxyQueryBuilder.prototype.limit = function(n) { this.params.limit = n; return this; };
        ProxyQueryBuilder.prototype.single = function() { this.isSingle = true; this.params.single = true; return this; };
        
        ProxyQueryBuilder.prototype.insert = function(values) { this.action = 'insert'; this.params.values = values; return this; };
        ProxyQueryBuilder.prototype.update = function(values) { this.action = 'update'; this.params.values = values; return this; };
        ProxyQueryBuilder.prototype.delete = function() { this.action = 'delete'; return this; };

        // Support then() for async/await
        ProxyQueryBuilder.prototype.then = function(onSuccess, onError) {
          var self = this;
          return fetch('/api/news', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              table: self.table,
              action: self.action,
              params: self.params
            })
          })
          .then(function(r) { return r.json(); })
          .then(function(data) {
            // Trả về định dạng giống Supabase { data, error }
            var result = { data: data.data || (self.isSingle ? null : []), error: data.error ? { message: data.error } : null };
            return onSuccess ? onSuccess(result) : result;
          })
          .catch(function(err) {
            var result = { data: null, error: { message: err.message || err } };
            return onError ? onError(result) : result;
          });
        };

        window.supabase = {
          from: function(table) { return new ProxyQueryBuilder(table); }
        };
        window.supabaseClient = window.supabase;
      } 
      else if (cfg && cfg.url && cfg.key && typeof supabase !== 'undefined' && typeof supabase.createClient === 'function') {
        window.SUPABASE_CONFIG = cfg;
        window.supabaseClient = supabase.createClient(cfg.url, cfg.key);
        window.supabase = window.supabaseClient;
      }

      applyDevTools(sec);
    });

})();
