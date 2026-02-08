-- ============================================
-- PART 4: TẠO ADMIN ĐẦU TIÊN
-- ============================================

-- Lưu ý: Chạy sau khi đã chạy PART 1, 2, 3
-- Password mặc định: admin123

-- Tạo admin đầu tiên
INSERT INTO admin_users (email, password_hash, full_name, role, is_active, permissions)
VALUES (
    'admin@dongmai.gov.vn',
    '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZRGdjGj/nMskyBPMa6KCdXjQGpQla',
    'Quản trị viên hệ thống',
    'super_admin',
    true,
    '{"manage_users": true, "manage_news": true, "manage_settings": true, "view_stats": true}'
);

-- ============================================
-- KIỂM TRA
-- ============================================

-- Xác nhận admin đã được tạo
SELECT 
    id, 
    email, 
    full_name, 
    role, 
    is_active, 
    created_at 
FROM admin_users 
WHERE email = 'admin@dongmai.gov.vn';

-- ============================================
-- NẾU CẦN ĐỔI PASSWORD
-- ============================================

-- Password: admin123 
-- Hash: $2a$10$N9qo8uLOickgx2ZMRZoMyeIjZRGdjGj/nMskyBPMa6KCdXjQGpQla

-- Chạy lệnh sau để đổi password:
-- UPDATE admin_users SET password_hash = '$2a$10$NEW_HASH_HERE' WHERE email = 'admin@dongmai.gov.vn';



