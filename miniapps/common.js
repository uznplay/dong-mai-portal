// Shared utilities for all Mini Apps

// Form validation utilities
function validateRequired(value, fieldName) {
    if (!value || value.trim() === '') {
        return `${fieldName} là bắt buộc`;
    }
    return null;
}

function validatePhone(phone) {
    const phoneRegex = /^(0|\+84)[0-9]{9}$/;
    if (!phoneRegex.test(phone.replace(/\s/g, ''))) {
        return 'Số điện thoại không hợp lệ';
    }
    return null;
}

function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        return 'Email không hợp lệ';
    }
    return null;
}

function validateCMND(cmnd) {
    const cmndRegex = /^[0-9]{9,12}$/;
    if (!cmndRegex.test(cmnd)) {
        return 'Số CMND/CCCD không hợp lệ (9-12 số)';
    }
    return null;
}

// Show notification
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-2xl transform transition-all duration-500 ${type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500'
        } text-white font-semibold`;
    notification.innerHTML = `
    <div class="flex items-center gap-3">
      <i data-lucide="${type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : 'info'}" class="w-6 h-6"></i>
      <span>${message}</span>
    </div>
  `;
    document.body.appendChild(notification);

    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 500);
    }, 3000);
}

// Show loading spinner
function showLoading(button) {
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = `
    <div class="flex items-center justify-center gap-2">
      <div class="spinner"></div>
      <span>Đang xử lý...</span>
    </div>
  `;
    return () => {
        button.disabled = false;
        button.innerHTML = originalText;
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    };
}

// Submit to DichVuCong API (simulated)
async function submitToDichVuCong(endpoint, data) {
    // Simulate API call - in production, this would connect to actual DichVuCong.gov.vn API
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            // Simulate successful submission
            const requestId = 'HS' + Date.now();
            resolve({
                success: true,
                requestId: requestId,
                message: 'Gửi hồ sơ thành công',
                estimatedTime: '3-5 ngày làm việc',
                tracking: `https://dichvucong.gov.vn/tracking/${requestId}`
            });
        }, 2000);
    });
}

// Format date
function formatDate(date) {
    if (!date) return '';
    const d = new Date(date);
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    return `${day}/${month}/${year}`;
}

// Generate reference number
function generateReferenceNumber(prefix = 'REF') {
    const timestamp = Date.now().toString(36).toUpperCase();
    const random = Math.random().toString(36).substring(2, 6).toUpperCase();
    return `${prefix}-${timestamp}-${random}`;
}

// Navigate back to portal
function goBack() {
    window.location.href = '../index.html';
}

// Print result
function printResult() {
    window.print();
}
