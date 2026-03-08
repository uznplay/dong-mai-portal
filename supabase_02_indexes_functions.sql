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

-- ============================================
-- FUNCTIONS
-- ============================================

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


