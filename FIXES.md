# Sửa lỗi Toolbar và Menu trong Editor

## 📋 Tóm tắt lỗi

### Vấn đề 1: Nút Code và Link không hoạt động
**Nguyên nhân:** Khi click vào nút trên toolbar, event `selectionchange` fire trước khi click handler chạy, làm mất vùng chọn văn bản trước khi `document.execCommand` được thực thi.

### Vấn đề 2: Menu Slash không phản hồi khi click
**Nguyên nhân:** Global click handler ẩn menu ngay cả khi click vào các nút toolbar hoặc dropdown menus.

### Vấn đề 3: Code trùng lặp
**Có 2 hàm `formatText` trùng lặp** trong file HTML gây xung đột.

---

## ✅ Các lỗi đã được sửa

### 1. Sửa `initTextToolbar()` và `updateToolbarPosition()` trong `notion-features.js`
- Thêm biến `isClickingToolbar` để theo dõi khi click vào toolbar
- Cập nhật logic để KHÔNG ẩn toolbar khi đang click vào toolbar buttons
- Ngăn chặn việc mất selection khi click vào nút

### 2. Sửa global click handler
- Thêm kiểm tra để KHÔNG ẩn menu khi click vào:
  - `#textToolbar` (toolbar chính)
  - `.toolbar-btn` (các nút trên toolbar)
  - `.toolbar-dropdown-menu` (menu dropdown)
  - `.block-add-btn` (nút thêm block)
- Đảm bảo menu chỉ ẩn khi click ra ngoài các vùng này

### 3. Cải thiện hàm `formatText()`
- Thêm kiểm tra selection hợp lệ trước khi thực thi lệnh
- Thêm alert khi user chưa chọn text mà đã bấm tạo link
- Cải thiện logic restore focus sau khi format
- Tự động style link sau khi tạo (target=_blank, màu xanh, gạch chân)

### 4. Xóa code trùng lặp
- Xóa 2 hàm `formatText()` trùng lặp trong `admin-news-edit.html`
- Xóa các hàm `toggleDropdown()`, `setBlockType()`, `setAlignment()`, `setColor()` trùng lặp
- Giờ chỉ dùng các hàm từ `notion-features.js` (đã được expose global)

---

## 📁 Files đã được sửa

1. **`dong-mai-portal-main/admin/notion-features.js`**
   - Sửa `initTextToolbar()` (dòng ~265)
   - Sửa `updateToolbarPosition()` (dòng ~277)
   - Sửa global click handler trong `initEditorFeatures()` (dòng ~58)
   - Cải thiện `formatText()` (dòng ~340)

2. **`dong-mai-portal-main/admin/admin-news-edit.html`**
   - Xóa duplicate `formatText()` và related functions (dòng ~902)
   - Xóa duplicate `formatText()` và related functions (dòng ~1000)

---

## 🧪 Cách test

1. Mở file `admin/admin-news-edit.html?action=new`
2. **Test Code button:**
   - Bôi đen một đoạn văn bản trong editor
   - Click vào nút Code (</>) trên toolbar
   - Văn bản sẽ được format thành code block
3. **Test Link button:**
   - Bôi đen một đoạn văn bản
   - Click vào nút Link (🔗) trên toolbar
   - Nhập URL khi được hỏi
   - Link sẽ được tạo với màu xanh và gạch chân
4. **Test Slash Menu:**
   - Gõ `/` trong một block trống
   - Menu sẽ hiện ra
   - Click vào các options trong menu
   - Menu sẽ đóng và block mới sẽ được thêm
5. **Test Toolbar buttons khi menu đang mở:**
   - Mở menu (bằng cách gõ `/`)
   - Click vào toolbar buttons
   - Toolbar KHÔNG bị ẩn, buttons hoạt động bình thường

---

## 🔧 Technical Details

### Vấn đề gốc:
```javascript
// Event firing order:
// 1. mousedown on toolbar button - selection starts to change
// 2. selectionchange fires - toolbar hides because no valid selection
// 3. click handler fires - too late, toolbar already hidden
```

### Giải pháp:
```javascript
// Track toolbar clicks
let isClickingToolbar = false;

// In mousedown handler:
textToolbar.addEventListener('mousedown', (e) => {
    e.preventDefault(); // Prevent selection change
    isClickingToolbar = true;
});

// In updateToolbarPosition:
function updateToolbarPosition() {
    // Don't hide if clicking on toolbar
    if (!isClickingToolbar && textToolbar) {
        textToolbar.classList.remove('active');
    }
    // ...
}
```

---

## ✨ Kết quả

✅ Nút Code và Link hoạt động đúng  
✅ Menu Slash phản hồi tốt khi click  
✅ Không còn xung đột code trùng lặp  
✅ UI/UX được cải thiện  
✅ Code được tổ chức tốt hơn







