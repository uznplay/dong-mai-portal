/**
 * Admin Layout Manager
 * Centralizes Sidebar and Common Logic
 */

const ADMIN_NAV_ITEMS = [
    { id: 'dashboard', label: 'Dashboard', icon: 'layout-dashboard', href: 'admin-dashboard.html' },
    { id: 'news', label: 'Tin nổi bật', icon: 'newspaper', href: 'admin-news.html' },
    { id: 'users', label: 'Quản lý Admin', icon: 'users', href: 'admin-users.html' },
    { id: 'media', label: 'Thư viện Media', icon: 'image', href: 'admin-media.html' },
    { id: 'settings', label: 'Cài đặt', icon: 'settings', href: 'admin-settings.html' },
    { id: 'logs', label: 'Nhật ký hoạt động', icon: 'activity', href: 'admin-logs.html' }
];

function renderSidebar(activePageId) {
    const userStr = localStorage.getItem('adminUser');
    const user = userStr ? JSON.parse(userStr) : { name: 'Admin', role: 'admin' };

    const navHTML = ADMIN_NAV_ITEMS.map(item => {
        const activeClass = item.id === activePageId ? 'active bg-red-600 text-white' : 'text-gray-700 hover:bg-red-50';
        // Note: The original 'active' class used background-color: #D32F2F; color: white; via CSS. 
        // We can use Tailwind classes directly or keep the 'active' class if CSS is loaded.
        // Let's rely on the CSS 'sidebar-link' class and 'active' class from styles.css/inline styles if present, 
        // OR fully switch to Tailwind.
        // Given existing styles, 'sidebar-link' and 'active' are used.
        const isActive = item.id === activePageId;
        return `
            <a href="${item.href}" 
               class="sidebar-link ${isActive ? 'active' : ''} flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-colors ${!isActive ? 'text-gray-700' : ''}">
                <i data-lucide="${item.icon}" class="w-5 h-5"></i>
                ${item.label}
            </a>
        `;
    }).join('');

    return `
        <aside class="w-64 bg-white shadow-xl z-30 flex flex-col h-full">
            <!-- Logo -->
            <div class="p-6 border-b">
                <div class="flex items-center gap-3">
                    <img src="../logo.png" alt="Logo" class="w-10 h-10 object-contain">
                    <div>
                        <h1 class="font-bold text-gray-900">Admin Portal</h1>
                        <p class="text-xs text-gray-500">Phường Đông Mai</p>
                    </div>
                </div>
            </div>

            <!-- Navigation -->
            <nav class="flex-1 p-4 space-y-1 overflow-y-auto">
                ${navHTML}
            </nav>

            <!-- User Menu -->
            <div class="p-4 border-t">
                <div class="flex items-center gap-3 mb-4">
                    <div class="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                        <i data-lucide="user" class="w-5 h-5 text-red-600"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <p class="font-medium text-gray-900 truncate" title="${user.full_name || user.username || 'Admin'}">
                            ${user.full_name || user.username || 'Admin'}
                        </p>
                        <p class="text-xs text-gray-500 capitalize">${user.role || 'Admin'}</p>
                    </div>
                </div>
                <button onclick="logout()" class="w-full flex items-center justify-center gap-2 px-4 py-2 border border-gray-200 rounded-xl text-gray-600 hover:bg-gray-50 transition-colors">
                    <i data-lucide="log-out" class="w-4 h-4"></i>
                    Đăng xuất
                </button>
            </div>
        </aside>
    `;
}

function logout() {
    if (confirm('Bạn có chắc chắn muốn đăng xuất?')) {
        localStorage.removeItem('adminUser');
        localStorage.removeItem('supabaseSession');
        window.location.href = '/admin/login.html';
    }
}

// Global initialization function
window.initAdminLayout = function (activePageId) {
    const sidebarContainer = document.getElementById('sidebar-container');
    if (sidebarContainer) {
        sidebarContainer.innerHTML = renderSidebar(activePageId);
        if (window.lucide) lucide.createIcons();
    }

    // Auth Check (Simple)
    // Auth Check with Expiry
    const sessionStr = localStorage.getItem('supabaseSession');
    if (!sessionStr && !window.location.href.includes('login.html')) {
        window.location.href = '/admin/login.html';
        return;
    }

    if (sessionStr) {
        try {
            const session = JSON.parse(sessionStr);
            const expiresAt = session.expires_at * 1000; // Supabase uses seconds
            const now = new Date().getTime();

            if (now > expiresAt) {
                console.log('Session expired, logging out...');
                localStorage.removeItem('adminUser');
                localStorage.removeItem('supabaseSession');
                window.location.href = '/admin/login.html';
            }
        } catch (e) {
            console.error('Session parse error:', e);
            window.location.href = '/admin/login.html';
        }
    }
};
