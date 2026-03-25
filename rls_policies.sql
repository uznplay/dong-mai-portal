-- ==============================================================================
-- DONG MAI PORTAL - RLS POLICIES SCRIPT
-- Chạy toàn bộ script này trong Supabase SQL Editor
-- Script an toàn: chỉ apply RLS/policy nếu bảng TỒN TẠI trong database
-- ==============================================================================

DO $$
DECLARE
    tbl text;
BEGIN

-- ============================================
-- PHẦN 1: ENABLE RLS - chỉ bật nếu bảng tồn tại
-- ============================================

-- featured_news
IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'featured_news') THEN
    ALTER TABLE featured_news ENABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS enabled on featured_news';
END IF;

-- admin_users
IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'admin_users') THEN
    ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS enabled on admin_users';
END IF;

-- media
IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'media') THEN
    ALTER TABLE media ENABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS enabled on media';
END IF;

-- admin_activity_logs
IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'admin_activity_logs') THEN
    ALTER TABLE admin_activity_logs ENABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS enabled on admin_activity_logs';
END IF;

-- chat_history
IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'chat_history') THEN
    ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS enabled on chat_history';
END IF;

-- qa_cache
IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'qa_cache') THEN
    ALTER TABLE qa_cache ENABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS enabled on qa_cache';
END IF;

-- api_rate_limits
IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'api_rate_limits') THEN
    ALTER TABLE api_rate_limits ENABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS enabled on api_rate_limits';
END IF;

-- model_health
IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'model_health') THEN
    ALTER TABLE model_health ENABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS enabled on model_health';
END IF;

END $$;

-- ============================================
-- PHẦN 2: HELPER FUNCTIONS (tránh RLS recursion)
-- ============================================
-- SECURITY DEFINER = chạy với quyền owner, không bị chặn bởi RLS
-- STABLE = kết quả không đổi trong 1 transaction

CREATE OR REPLACE FUNCTION auth_is_admin()
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
  SELECT EXISTS (
    SELECT 1 FROM admin_users
    WHERE id = auth.uid()
    AND is_active = true
  );
$$;

CREATE OR REPLACE FUNCTION auth_is_super_admin()
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
  SELECT EXISTS (
    SELECT 1 FROM admin_users
    WHERE id = auth.uid()
    AND role = 'super_admin'
    AND is_active = true
  );
$$;

CREATE OR REPLACE FUNCTION auth_is_editor()
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
  SELECT EXISTS (
    SELECT 1 FROM admin_users
    WHERE id = auth.uid()
    AND role IN ('super_admin', 'admin', 'editor')
    AND is_active = true
  );
$$;

-- ============================================
-- PHẦN 3: admin_users POLICIES
-- ============================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'admin_users') THEN
        RAISE NOTICE 'Bảng admin_users không tồn tại, bỏ qua policies';
        RETURN;
    END IF;

    DROP POLICY IF EXISTS "View own profile" ON admin_users;
    DROP POLICY IF EXISTS "Manage users"     ON admin_users;

    CREATE POLICY "View own profile" ON admin_users FOR SELECT
      USING (auth.uid() = id OR auth_is_admin());

    CREATE POLICY "Manage users" ON admin_users FOR ALL
      USING (auth_is_super_admin())
      WITH CHECK (auth_is_super_admin());

    RAISE NOTICE 'Policies created for admin_users';
END $$;

-- ============================================
-- PHẦN 4: featured_news POLICIES
-- ============================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'featured_news') THEN
        RAISE NOTICE 'Bảng featured_news không tồn tại, bỏ qua policies';
        RETURN;
    END IF;

    DROP POLICY IF EXISTS "Public can read published news" ON featured_news;
    DROP POLICY IF EXISTS "Admins view all news"           ON featured_news;
    DROP POLICY IF EXISTS "Editors manage news"           ON featured_news;

    -- Ai cũng đọc được bài đã publish (không cần đăng nhập)
    CREATE POLICY "Public can read published news" ON featured_news FOR SELECT
      USING (status = 'published');

    -- Admin/Editor xem được tất cả bài (kể cả draft)
    CREATE POLICY "Admins view all news" ON featured_news FOR SELECT
      USING (auth_is_admin());

    -- Admin/Editor tạo/sửa/xoá bài viết
    CREATE POLICY "Editors manage news" ON featured_news FOR ALL
      USING (auth_is_editor())
      WITH CHECK (auth_is_editor());

    RAISE NOTICE 'Policies created for featured_news';
END $$;

-- ============================================
-- PHẦN 5: media POLICIES
-- ============================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'media') THEN
        RAISE NOTICE 'Bảng media không tồn tại, bỏ qua policies';
        RETURN;
    END IF;

    DROP POLICY IF EXISTS "Public can read media" ON media;
    DROP POLICY IF EXISTS "Admins manage media"  ON media;

    -- Ai cũng đọc được media (ảnh, file công khai)
    CREATE POLICY "Public can read media" ON media FOR SELECT
      USING (true);

    -- Admin/Editor upload/quản lý media
    CREATE POLICY "Admins manage media" ON media FOR ALL
      USING (auth_is_editor())
      WITH CHECK (auth_is_editor());

    RAISE NOTICE 'Policies created for media';
END $$;

-- ============================================
-- PHẦN 6: admin_activity_logs POLICIES
-- ============================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'admin_activity_logs') THEN
        RAISE NOTICE 'Bảng admin_activity_logs không tồn tại, bỏ qua policies';
        RETURN;
    END IF;

    DROP POLICY IF EXISTS "Admins view logs"   ON admin_activity_logs;
    DROP POLICY IF EXISTS "Admins create logs" ON admin_activity_logs;

    -- Chỉ admin mới xem được logs
    CREATE POLICY "Admins view logs" ON admin_activity_logs FOR SELECT
      USING (auth_is_admin());

    -- Chỉ admin mới tạo được logs
    CREATE POLICY "Admins create logs" ON admin_activity_logs FOR INSERT
      WITH CHECK (auth_is_admin());

    RAISE NOTICE 'Policies created for admin_activity_logs';
END $$;

-- ============================================
-- PHẦN 7: chat_history POLICIES
-- ============================================
-- Bảng này gọi từ browser qua anon key. Dữ liệu tạm, tự dọn sau 10 phút.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'chat_history') THEN
        RAISE NOTICE 'Bảng chat_history không tồn tại, bỏ qua policies';
        RETURN;
    END IF;

    DROP POLICY IF EXISTS "Public can read chat history" ON chat_history;
    DROP POLICY IF EXISTS "Public can insert chat"      ON chat_history;
    DROP POLICY IF EXISTS "Public can delete chat"      ON chat_history;

    CREATE POLICY "Public can read chat history" ON chat_history FOR SELECT
      USING (true);

    CREATE POLICY "Public can insert chat" ON chat_history FOR INSERT
      WITH CHECK (true);

    CREATE POLICY "Public can delete chat" ON chat_history FOR DELETE
      USING (true);

    RAISE NOTICE 'Policies created for chat_history';
END $$;

-- ============================================
-- PHẦN 8: qa_cache POLICIES
-- ============================================
-- Cache chatbot, không nhạy cảm.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'qa_cache') THEN
        RAISE NOTICE 'Bảng qa_cache không tồn tại, bỏ qua policies';
        RETURN;
    END IF;

    DROP POLICY IF EXISTS "Public can read cache"  ON qa_cache;
    DROP POLICY IF EXISTS "Public can write cache" ON qa_cache;
    DROP POLICY IF EXISTS "Public can update cache" ON qa_cache;

    CREATE POLICY "Public can read cache" ON qa_cache FOR SELECT
      USING (true);

    CREATE POLICY "Public can write cache" ON qa_cache FOR INSERT
      WITH CHECK (true);

    CREATE POLICY "Public can update cache" ON qa_cache FOR UPDATE
      USING (true)
      WITH CHECK (true);

    RAISE NOTICE 'Policies created for qa_cache';
END $$;

-- ============================================
-- PHẦN 9: api_rate_limits POLICIES
-- ============================================
-- Rate limiting theo IP, không nhạy cảm.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'api_rate_limits') THEN
        RAISE NOTICE 'Bảng api_rate_limits không tồn tại, bỏ qua policies';
        RETURN;
    END IF;

    DROP POLICY IF EXISTS "Public can read rate limits"  ON api_rate_limits;
    DROP POLICY IF EXISTS "Public can write rate limits" ON api_rate_limits;
    DROP POLICY IF EXISTS "Public can update rate limits" ON api_rate_limits;

    CREATE POLICY "Public can read rate limits" ON api_rate_limits FOR SELECT
      USING (true);

    CREATE POLICY "Public can write rate limits" ON api_rate_limits FOR INSERT
      WITH CHECK (true);

    CREATE POLICY "Public can update rate limits" ON api_rate_limits FOR UPDATE
      USING (true)
      WITH CHECK (true);

    RAISE NOTICE 'Policies created for api_rate_limits';
END $$;

-- ============================================
-- PHẦN 10: model_health POLICIES
-- ============================================
-- Blacklist tạm thời của model AI, không nhạy cảm.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'model_health') THEN
        RAISE NOTICE 'Bảng model_health không tồn tại, bỏ qua policies';
        RETURN;
    END IF;

    DROP POLICY IF EXISTS "Public can read model health"  ON model_health;
    DROP POLICY IF EXISTS "Public can write model health" ON model_health;
    DROP POLICY IF EXISTS "Public can update model health" ON model_health;

    CREATE POLICY "Public can read model health" ON model_health FOR SELECT
      USING (true);

    CREATE POLICY "Public can write model health" ON model_health FOR INSERT
      WITH CHECK (true);

    CREATE POLICY "Public can update model health" ON model_health FOR UPDATE
      USING (true)
      WITH CHECK (true);

    RAISE NOTICE 'Policies created for model_health';
END $$;

-- ============================================
-- PHẦN 11: STORAGE BUCKET (media)
-- ============================================
DO $$
BEGIN
    -- Chỉ tạo storage policies nếu bucket 'media' tồn tại
    IF EXISTS (SELECT 1 FROM storage.buckets WHERE id = 'media') THEN

        DROP POLICY IF EXISTS "Public read media files" ON storage.objects;
        DROP POLICY IF EXISTS "Admins upload media"    ON storage.objects;
        DROP POLICY IF EXISTS "Admins update media"     ON storage.objects;
        DROP POLICY IF EXISTS "Admins delete media"     ON storage.objects;

        -- Ai cũng đọc file trong bucket media
        CREATE POLICY "Public read media files" ON storage.objects
          FOR SELECT USING (bucket_id = 'media');

        -- Ai đã đăng nhập cũng upload được
        CREATE POLICY "Admins upload media" ON storage.objects
          FOR INSERT WITH CHECK (
            bucket_id = 'media'
            AND (auth.uid() IS NOT NULL)
          );

        -- Chỉ editor mới update/delete
        CREATE POLICY "Admins update media" ON storage.objects
          FOR UPDATE USING (
            bucket_id = 'media'
            AND auth_is_editor()
          );

        CREATE POLICY "Admins delete media" ON storage.objects
          FOR DELETE USING (
            bucket_id = 'media'
            AND auth_is_editor()
          );

        RAISE NOTICE 'Storage policies created for bucket media';
    ELSE
        RAISE NOTICE 'Bucket media không tồn tại, bỏ qua storage policies';
    END IF;
END $$;

-- ============================================
-- PHẦN 12: VERIFY - Kiểm tra sau khi chạy
-- ============================================

-- Kiểm tra RLS đã được bật cho tất cả bảng
SELECT
  schemaname,
  tablename,
  rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN (
  'featured_news', 'admin_users', 'media',
  'admin_activity_logs', 'chat_history',
  'qa_cache', 'api_rate_limits', 'model_health'
)
ORDER BY tablename;

-- Kiểm tra số lượng policies đã tạo
SELECT
  tablename,
  policyname,
  cmd
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, cmd;
