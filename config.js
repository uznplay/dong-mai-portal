window.SUPABASE_CONFIG = {
    url: "https://hnwoxfgmkmonwrwutemp.supabase.co",
    key: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhud294Zmdta21vbndyd3V0ZW1wIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk1ODU3OTgsImV4cCI6MjA4NTE2MTc5OH0.IYw90rpWiCVifyeNGH1MZDBC2W7urT4B-q_k52zSE1A"
};

// Initialize Supabase if client library is available
if (typeof supabase !== 'undefined' && typeof supabase.createClient === 'function') {
    window.supabaseClient = supabase.createClient(window.SUPABASE_CONFIG.url, window.SUPABASE_CONFIG.key);
    // Backward compatibility
    window.supabase = window.supabaseClient;
}
