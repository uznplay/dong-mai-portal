-- ============================================
-- PART 1: TẠO BẢNG (CHẠY TRƯỚC)
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









