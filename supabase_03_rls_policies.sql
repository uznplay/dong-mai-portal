-- ============================================
-- PART 3: ROW LEVEL SECURITY POLICIES
-- ============================================

-- Enable RLS cho tất cả bảng
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE featured_news ENABLE ROW LEVEL SECURITY;
ALTER TABLE media ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_activity_logs ENABLE ROW LEVEL SECURITY;

-- ============================================
-- ADMIN USERS POLICIES
-- ============================================

-- Cho phép user đã đăng nhập xem tất cả admin
DROP POLICY IF EXISTS "Admin users can view all" ON admin_users;
CREATE POLICY "Admin users can view all" ON admin_users FOR SELECT USING (
    auth.uid() IS NOT NULL
);

-- Chỉ super_admin mới có thể quản lý users
DROP POLICY IF EXISTS "Super admin can manage users" ON admin_users;
CREATE POLICY "Super admin can manage users" ON admin_users FOR ALL USING (
    EXISTS (
        SELECT 1 FROM admin_users 
        WHERE id = auth.uid() 
        AND role = 'super_admin'
        AND is_active = true
    )
);

-- ============================================
-- FEATURED NEWS POLICIES
-- ============================================

-- Bài viết đã publish thì ai cũng xem được
DROP POLICY IF EXISTS "Published news is public" ON featured_news;
CREATE POLICY "Published news is public" ON featured_news FOR SELECT USING (
    status = 'published'
);

-- Admin/Editor có thể xem tất cả bài viết
DROP POLICY IF EXISTS "Admins can view all news" ON featured_news;
CREATE POLICY "Admins can view all news" ON featured_news FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM admin_users 
        WHERE id = auth.uid() 
        AND is_active = true
    )
);

-- Admin/Editor có thể quản lý bài viết
DROP POLICY IF EXISTS "Editors can manage news" ON featured_news;
CREATE POLICY "Editors can manage news" ON featured_news FOR ALL USING (
    EXISTS (
        SELECT 1 FROM admin_users 
        WHERE id = auth.uid() 
        AND role IN ('super_admin', 'admin', 'editor')
        AND is_active = true
    )
);

-- ============================================
-- MEDIA POLICIES
-- ============================================

-- Ai cũng xem được media
DROP POLICY IF EXISTS "Media public read" ON media;
CREATE POLICY "Media public read" ON media FOR SELECT USING (true);

-- Admin/Editor có thể quản lý media
DROP POLICY IF EXISTS "Admins can manage media" ON media;
CREATE POLICY "Admins can manage media" ON media FOR ALL USING (
    EXISTS (
        SELECT 1 FROM admin_users 
        WHERE id = auth.uid() 
        AND role IN ('super_admin', 'admin', 'editor')
        AND is_active = true
    )
);

-- ============================================
-- ACTIVITY LOGS POLICIES
-- ============================================

-- Admin/Super Admin có thể xem logs
DROP POLICY IF EXISTS "Admins can view activity logs" ON admin_activity_logs;
CREATE POLICY "Admins can view activity logs" ON admin_activity_logs FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM admin_users 
        WHERE id = auth.uid() 
        AND role IN ('super_admin', 'admin')
        AND is_active = true
    )
);

-- Admin có thể tạo logs
DROP POLICY IF EXISTS "Admins can create activity logs" ON admin_activity_logs;
CREATE POLICY "Admins can create activity logs" ON admin_activity_logs FOR INSERT WITH CHECK (
    EXISTS (
        SELECT 1 FROM admin_users 
        WHERE id = auth.uid() 
        AND is_active = true
    )
);








