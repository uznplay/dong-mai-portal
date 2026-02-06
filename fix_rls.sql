-- SCRIPT SỬA LỖI 500 (RLS RECURSION)
-- Chạy script này để khắc phục lỗi không login được do vòng lặp vô hạn quyền truy cập

-- 1. Tạo function kiểm tra quyền an toàn (bypass RLS loop)
-- Function này chạy với quyền Owner (Security Definer) nên không bị chặn bởi RLS
CREATE OR REPLACE FUNCTION auth_is_admin()
RETURNS boolean AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM admin_users
    WHERE id = auth.uid()
    AND is_active = true
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION auth_is_super_admin()
RETURNS boolean AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM admin_users
    WHERE id = auth.uid()
    AND role = 'super_admin'
    AND is_active = true
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION auth_is_editor()
RETURNS boolean AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM admin_users
    WHERE id = auth.uid()
    AND role IN ('super_admin', 'admin', 'editor')
    AND is_active = true
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 2. Sửa lại Policies của admin_users
DROP POLICY IF EXISTS "Admin users can view all" ON admin_users;
DROP POLICY IF EXISTS "Super admin can manage users" ON admin_users;

-- Cho phép tự xem thông tin bản thân HOẶC Admin xem tất cả
CREATE POLICY "View users" ON admin_users FOR SELECT USING (
   auth.uid() = id
   OR
   auth_is_admin()
);

-- Chỉ Super Admin được sửa đổi
CREATE POLICY "Manage users" ON admin_users FOR ALL USING (
    auth_is_super_admin()
);

-- 3. Sửa Policies của featured_news
DROP POLICY IF EXISTS "Admins can view all news" ON featured_news;
DROP POLICY IF EXISTS "Editors can manage news" ON featured_news;

CREATE POLICY "Admins view news" ON featured_news FOR SELECT USING (
    auth_is_admin()
);

CREATE POLICY "Editors manage news" ON featured_news FOR ALL USING (
    auth_is_editor()
);

-- 4. Sửa Policies của media
DROP POLICY IF EXISTS "Admins can manage media" ON media;
CREATE POLICY "Admins manage media" ON media FOR ALL USING (
    auth_is_editor()
);

-- 5. Sửa Policies của activity logs
DROP POLICY IF EXISTS "Admins can view activity logs" ON admin_activity_logs;
DROP POLICY IF EXISTS "Admins can create activity logs" ON admin_activity_logs;

CREATE POLICY "Admins view logs" ON admin_activity_logs FOR SELECT USING (
    auth_is_admin()
);

CREATE POLICY "Admins create logs" ON admin_activity_logs FOR INSERT WITH CHECK (
    auth_is_admin()
);
