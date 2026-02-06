# Đông Mai Số - Hành chính phục vụ

Hệ thống chuyển đổi số hành chính công phường Đông Mai, tỉnh Quảng Ninh.

## Cấu trúc dự án

```
dong-mai-portal-main/
├── index.html                    # Giao diện chính
├── api/                          # API Serverless (Python)
├── chatbot.js                    # Logic Chatbot AI
├── vercel.json                  # Cấu hình Vercel
├── admin/                       # Hệ thống admin
│   ├── login.html
│   ├── admin-dashboard.html
│   ├── admin-news.html
│   ├── admin-news-edit.html
│   ├── admin-users.html
│   ├── hash-password.html       # Tool tạo password hash
│   └── README_ADMIN.md          # Hướng dẫn chi tiết
└── supabase/
    ├── supabase_01_tables.sql           # Tạo bảng
    ├── supabase_02_indexes_functions.sql # Index & Functions
    ├── supabase_03_rls_policies.sql     # RLS Policies
    └── supabase_04_create_admin.sql      # Tạo admin đầu tiên
```

## Hướng dẫn cài đặt chi tiết

### Bước 1: Tạo project Supabase

1. Truy cập https://supabase.com và đăng nhập
2. Tạo project mới (đặt tên: dong-mai-portal)
3. Lấy URL và ANON KEY từ Settings > API

### Bước 2: Chạy SQL theo thứ tự

Vào Supabase Dashboard > SQL Editor và chạy **THEO THỨ TỰ**:

```
1. Mở supabase_01_tables.sql → Copy → Run
2. Mở supabase_02_indexes_functions.sql → Copy → Run
3. Mở supabase_03_rls_policies.sql → Copy → Run
4. Mở supabase_04_create_admin.sql → Copy → Run
```

**Kiểm tra:** Sau bước 4, chạy:
```sql
SELECT * FROM admin_users;
```
Phải thấy 1 dòng với email: `admin@dongmai.gov.vn`

### Bước 3: Cấu hình Storage

1. Supabase Dashboard > Storage
2. Tạo bucket mới:
   - Name: `media`
   - Public bucket: ✅ ON

### Bước 4: Cấu hình trong file HTML

Thay thế URL và KEY trong **MỖI FILE** admin:

```javascript
// Thay thế bằng credentials của bạn
window.supabase = supabase.createClient(
    'https://YOUR_PROJECT.supabase.co',
    'YOUR_SUPABASE_ANON_KEY'
);
```

**Các file cần cấu hình:**
- `admin/login.html`
- `admin/admin-dashboard.html`
- `admin/admin-news.html`
- `admin/admin-news-edit.html`
- `admin/admin-users.html`
- `index.html`

### Bước 5: Đăng nhập Admin

1. Truy cập: `http://localhost:3000/admin/login.html`
2. Đăng nhập:
   - **Email:** `admin@dongmai.gov.vn`
   - **Password:** `admin123`

### Bước 6: Đổi Password (quan trọng!)

Sau khi đăng nhập lần đầu:
1. Vào "Quản lý Admin"
2. Chọn tài khoản của bạn
3. Nhập password mới
4. Lưu thay đổi

## Tính năng Editor Notion-like

### Các loại block:
- **/** → Hiển thị menu chọn block
- **H1/H2/H3** → Tiêu đề các cấp
- **Paragraph** → Văn bản thường
- **List** → Danh sách (có/không thứ tự)
- **Quote** → Trích dẫn
- **Callout** → Hộp thông báo
- **Code** → Đoạn code
- **Divider** → Dấu phân cách
- **Image** → Hình ảnh (kéo thả)

### Thao tác:
- **Enter** → Tạo block mới
- **Backspace** → Xóa block (khi rỗng)
- **↑/↓** → Di chuyển giữa các block
- **Kéo thả ảnh** → Upload ảnh

## Vai trò & Quyền hạn

| Vai trò | Quản lý user | Quản lý tin | Xem stats | Cài đặt |
|---------|--------------|-------------|-----------|---------|
| Super Admin | ✅ | ✅ | ✅ | ✅ |
| Admin | ❌ | ✅ | ✅ | ❌ |
| Editor | ❌ | ✅ | ❌ | ❌ |
| Viewer | ❌ | ❌ | ✅ | ❌ |

## Công nghệ

- **Frontend:** HTML, Tailwind CSS, Vanilla JS
- **Database:** Supabase (PostgreSQL + UUID)
- **Storage:** Supabase Storage
- **Auth:** Supabase Auth

## Triển khai Vercel

1. Push code lên GitHub
2. Kết nối với Vercel
3. Thêm Environment Variables:
   ```
   SUPABASE_URL=your-url
   SUPABASE_KEY=your-anon-key
   ```

## Xử lý lỗi

### Lỗi "operator does not exist: bigint = uuid"
**Nguyên nhân:** Schema dùng bigint thay vì UUID
**Cách sửa:** Đã cập nhật sang UUID. Chạy lại SQL theo thứ tự.

### Lỗi "password hash mismatch"
**Nguyên nhân:** Password hash không đúng
**Cách sửa:** Sử dụng hash chuẩn hoặc tạo mới:
```sql
UPDATE admin_users 
SET password_hash = '$2a$10$NEW_HASH' 
WHERE email = 'admin@dongmai.gov.vn';
```

### Lỗi "row level security"
**Nguyên nhân:** Chưa chạy RLS policies
**Cách sửa:** Chạy supabase_03_rls_policies.sql

## Liên hệ

Email: dongmai@bacninh.gov.vn

---

© 2026 UBND Phường Đông Mai
