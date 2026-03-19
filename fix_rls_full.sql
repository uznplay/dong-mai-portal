-- Fix RLS Policies for dong-mai-portal
-- Run this in Supabase SQL Editor

-- 1. Disable RLS on api_rate_limits table (or create permissive policy)
ALTER TABLE api_rate_limits DISABLE ROW LEVEL SECURITY;

-- 2. Disable RLS on model_health table
ALTER TABLE model_health DISABLE ROW LEVEL SECURITY;

-- 3. Disable RLS on chat_history table
ALTER TABLE chat_history DISABLE ROW LEVEL SECURITY;

-- 4. Disable RLS on qa_cache table
ALTER TABLE qa_cache DISABLE ROW LEVEL SECURITY;

-- If you want to keep RLS enabled, use these policies instead:
/*
-- Allow public insert/update for api_rate_limits
CREATE POLICY "Allow public access" ON api_rate_limits
FOR ALL USING (true) WITH CHECK (true);

-- Allow public insert/update for model_health  
CREATE POLICY "Allow public access" ON model_health
FOR ALL USING (true) WITH CHECK (true);

-- Allow public insert/update for chat_history
CREATE POLICY "Allow public access" ON chat_history
FOR ALL USING (true) WITH CHECK (true);

-- Allow public insert/update for qa_cache
CREATE POLICY "Allow public access" ON qa_cache
FOR ALL USING (true) WITH CHECK (true);
*/
