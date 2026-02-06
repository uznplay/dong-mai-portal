-- ==============================================================================
-- DONG MAI PORTAL - FULL DATABASE SETUP SCRIPT
-- Copy toàn bộ nội dung file này và chạy trong Supabase SQL Editor
-- ==============================================================================

-- ============================================
-- PART 1: TẠO BẢNG
-- ============================================

-- 1. Bảng quản lý tài khoản admin
CREATE TABLE IF NOT EXISTS admin_users (
    id uuid primary key default gen_random_uuid(),
    email text unique not null,
    password_hash text not null,
    full_name text not null,
    role text default 'admin' check (role in ('super_admin', 'admin', 'editor', 'viewer')),
    avatar_url text,
    is_active boolean default true,
    permissions jsonb default '{}',
    last_login_at timestamp with time zone,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 2. Bảng tin nổi bật (Featured News)
CREATE TABLE IF NOT EXISTS featured_news (
    id uuid primary key default gen_random_uuid(),
    title text not null,
    slug text unique not null,
    thumbnail_url text,
    summary text,
    content jsonb not null,
    content_html text,
    status text default 'draft' check (status in ('draft', 'published', 'archived', 'scheduled')),
    is_featured boolean default false,
    is_pinned boolean default false,
    view_count bigint default 0,
    author_id uuid references admin_users(id) on delete set null,
    published_at timestamp with time zone,
    scheduled_at timestamp with time zone,
    category text,
    tags text[],
    seo_title text,
    seo_description text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 3. Bảng media
CREATE TABLE IF NOT EXISTS media (
    id uuid primary key default gen_random_uuid(),
    filename text not null,
    original_name text not null,
    mime_type text not null,
    size bigint not null,
    url text not null,
    storage_path text not null,
    uploaded_by uuid references admin_users(id) on delete set null,
    used_in uuid[],
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 4. Bảng logs hoạt động admin
CREATE TABLE IF NOT EXISTS admin_activity_logs (
    id uuid primary key default gen_random_uuid(),
    admin_id uuid references admin_users(id) on delete set null,
    action text not null,
    entity_type text,
    entity_id uuid,
    details jsonb default '{}',
    ip_address text,
    user_agent text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- ============================================
-- PART 2: TẠO INDEXES VÀ FUNCTIONS
-- ============================================

-- Index cho bảng admin_users
CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users(email);
CREATE INDEX IF NOT EXISTS idx_admin_users_role ON admin_users(role);

-- Index cho bảng featured_news
CREATE INDEX IF NOT EXISTS idx_featured_news_slug ON featured_news(slug);
CREATE INDEX IF NOT EXISTS idx_featured_news_status ON featured_news(status);
CREATE INDEX IF NOT EXISTS idx_featured_news_category ON featured_news(category);
CREATE INDEX IF NOT EXISTS idx_featured_news_is_featured ON featured_news(is_featured);
CREATE INDEX IF NOT EXISTS idx_featured_news_is_pinned ON featured_news(is_pinned);
CREATE INDEX IF NOT EXISTS idx_featured_news_published_at ON featured_news(published_at);
CREATE INDEX IF NOT EXISTS idx_featured_news_author_id ON featured_news(author_id);

-- Index cho bảng media
CREATE INDEX IF NOT EXISTS idx_media_uploaded_by ON media(uploaded_by);

-- Index cho bảng activity logs
CREATE INDEX IF NOT EXISTS idx_admin_activity_logs_admin_id ON admin_activity_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_activity_logs_created_at ON admin_activity_logs(created_at);

-- Function cập nhật timestamp tự động
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger tự động cập nhật updated_at
DROP TRIGGER IF EXISTS update_admin_users_updated_at ON admin_users;
CREATE TRIGGER update_admin_users_updated_at
    BEFORE UPDATE ON admin_users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_featured_news_updated_at ON featured_news;
CREATE TRIGGER update_featured_news_updated_at
    BEFORE UPDATE ON featured_news
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function tạo slug tự động
CREATE OR REPLACE FUNCTION generate_slug(title text)
RETURNS text AS $$
BEGIN
    RETURN LOWER(
        REGEXP_REPLACE(
            REGEXP_REPLACE(
                REGEXP_REPLACE(title, '[^a-zA-Z0-9\s]', '', 'g'),
                '\s+', '-', 'g'
            ),
            '^-|-$', '', 'g'
        )
    ) || '-' || EXTRACT(EPOCH FROM NOW())::text;
END;
$$ LANGUAGE plpgsql;

-- Function đăng bài tự động khi đến thời gian scheduled
CREATE OR REPLACE FUNCTION publish_scheduled_news()
RETURNS void AS $$
BEGIN
    UPDATE featured_news
    SET status = 'published',
    published_at = NOW()
    WHERE status = 'scheduled'
    AND scheduled_at <= NOW();
END;
$$ LANGUAGE plpgsql;

-- Function tăng view count
CREATE OR REPLACE FUNCTION increment_view_count(posts_id uuid)
RETURNS void AS $$
BEGIN
    UPDATE featured_news
    SET view_count = COALESCE(view_count, 0) + 1
    WHERE id = posts_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- PART 3: ROW LEVEL SECURITY POLICIES
-- ============================================

-- Enable RLS cho tất cả bảng
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE featured_news ENABLE ROW LEVEL SECURITY;
ALTER TABLE media ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_activity_logs ENABLE ROW LEVEL SECURITY;

-- ADMIN USERS POLICIES
DROP POLICY IF EXISTS "Admin users can view all" ON admin_users;
CREATE POLICY "Admin users can view all" ON admin_users FOR SELECT USING (
    auth.uid() IS NOT NULL
);

DROP POLICY IF EXISTS "Super admin can manage users" ON admin_users;
CREATE POLICY "Super admin can manage users" ON admin_users FOR ALL USING (
    EXISTS (
        SELECT 1 FROM admin_users 
        WHERE id = auth.uid() 
        AND role = 'super_admin'
        AND is_active = true
    )
);

-- FEATURED NEWS POLICIES
DROP POLICY IF EXISTS "Published news is public" ON featured_news;
CREATE POLICY "Published news is public" ON featured_news FOR SELECT USING (
    status = 'published'
);

DROP POLICY IF EXISTS "Admins can view all news" ON featured_news;
CREATE POLICY "Admins can view all news" ON featured_news FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM admin_users 
        WHERE id = auth.uid() 
        AND is_active = true
    )
);

DROP POLICY IF EXISTS "Editors can manage news" ON featured_news;
CREATE POLICY "Editors can manage news" ON featured_news FOR ALL USING (
    EXISTS (
        SELECT 1 FROM admin_users 
        WHERE id = auth.uid() 
        AND role IN ('super_admin', 'admin', 'editor')
        AND is_active = true
    )
);

-- MEDIA POLICIES
DROP POLICY IF EXISTS "Media public read" ON media;
CREATE POLICY "Media public read" ON media FOR SELECT USING (true);

DROP POLICY IF EXISTS "Admins can manage media" ON media;
CREATE POLICY "Admins can manage media" ON media FOR ALL USING (
    EXISTS (
        SELECT 1 FROM admin_users 
        WHERE id = auth.uid() 
        AND role IN ('super_admin', 'admin', 'editor')
        AND is_active = true
    )
);

-- ACTIVITY LOGS POLICIES
DROP POLICY IF EXISTS "Admins can view activity logs" ON admin_activity_logs;
CREATE POLICY "Admins can view activity logs" ON admin_activity_logs FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM admin_users 
        WHERE id = auth.uid() 
        AND role IN ('super_admin', 'admin')
        AND is_active = true
    )
);

DROP POLICY IF EXISTS "Admins can create activity logs" ON admin_activity_logs;
CREATE POLICY "Admins can create activity logs" ON admin_activity_logs FOR INSERT WITH CHECK (
    EXISTS (
        SELECT 1 FROM admin_users 
        WHERE id = auth.uid() 
        AND is_active = true
    )
);

-- ============================================
-- PART 4: TẠO ADMIN ĐẦU TIÊN
-- ============================================
-- Password mặc định: admin123
INSERT INTO admin_users (email, password_hash, full_name, role, is_active, permissions)
VALUES (
    'admin@dongmai.gov.vn',
    '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZRGdjGj/nMskyBPMa6KCdXjQGpQla',
    'Quản trị viên hệ thống',
    'super_admin',
    true,
    '{"manage_users": true, "manage_news": true, "manage_settings": true, "view_stats": true}'
);
