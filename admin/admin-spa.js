/**
 * Admin Portal SPA Logic
 * Handles Routing, Tab Switching, and Data Loading
 */

// ==========================================
// 1. CONFIGURATION & STATE
// ==========================================
let currentTab = 'dashboard';
const TABS = ['dashboard', 'news', 'guides', 'users', 'settings'];

document.addEventListener('DOMContentLoaded', async () => {
    // Wait for Supabase config to be ready (from config.js)
    if (window.supabaseReady) {
        await window.supabaseReady;
    }
    initSPA();
});

function initSPA() {
    checkAuth();
    setupNavigation();
    loadTab(currentTab);
    updateUserInfo();
}

function checkAuth() {
    const sessionStr = localStorage.getItem('supabaseSession');
    if (!sessionStr) {
        window.location.href = '/admin/login.html';
        return;
    }

    try {
        const session = JSON.parse(sessionStr);
        // Safety check if expires_at exists
        if (session.expires_at) {
            const expiresAt = session.expires_at * 1000;
            if (new Date().getTime() > expiresAt) {
                localStorage.removeItem('adminUser');
                localStorage.removeItem('supabaseSession');
                window.location.href = '/admin/login.html';
                return;
            }
        }
    } catch (e) {
        // Corrupt session data
        localStorage.removeItem('adminUser');
        localStorage.removeItem('supabaseSession');
        window.location.href = '/admin/login.html';
    }
}

function updateUserInfo() {
    const userStr = localStorage.getItem('adminUser');
    if (userStr) {
        const user = JSON.parse(userStr);
        document.getElementById('currentAdminName').textContent = user.full_name || user.username || 'Admin';
        document.getElementById('currentAdminRole').textContent = user.role || 'Admin';
    }
}

function logout() {
    if (confirm('Bạn có chắc chắn muốn đăng xuất?')) {
        localStorage.removeItem('adminUser');
        localStorage.removeItem('supabaseSession');
        window.location.href = '/admin/login.html';
    }
}

// ==========================================
// 2. NAVIGATION LOGIC
// ==========================================
function setupNavigation() {
    document.querySelectorAll('.sidebar-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const tab = link.getAttribute('data-tab');
            if (tab) switchTab(tab);
        });
    });
}

function switchTab(tabId) {
    if (!TABS.includes(tabId)) return;

    // Update Sidebar Active State
    document.querySelectorAll('.sidebar-link').forEach(el => {
        if (el.getAttribute('data-tab') === tabId) {
            el.classList.add('active', 'bg-red-600', 'text-white');
            el.classList.remove('text-gray-700', 'hover:bg-red-50');
        } else {
            el.classList.remove('active', 'bg-red-600', 'text-white');
            el.classList.add('text-gray-700', 'hover:bg-red-50');
        }
    });

    // Hide all views
    document.querySelectorAll('.admin-view').forEach(view => {
        view.classList.add('hidden');
    });

    // Show selected view
    const targetView = document.getElementById(`view-${tabId}`);
    if (targetView) {
        targetView.classList.remove('hidden');
        loadTabData(tabId);
    }

    currentTab = tabId;
}

function loadTab(tabId) {
    switchTab(tabId);
}

// ==========================================
// 3. DATA LOADING (Placeholder for merged logic)
// ==========================================

// Helper function to open news editor (within SPA if possible)
function openNewsEditor(postId = null) {
    const url = postId ? `/admin/admin-news-edit.html?id=${postId}` : `/admin/admin-news-edit.html?action=new`;
    window.location.href = url; // Navigate directly (same tab)
}

function loadTabData(tabId) {
    console.log(`Loading data for ${tabId}...`);
    switch (tabId) {
        case 'dashboard':
            loadDashboardStats();
            break;
        case 'news':
            loadNewsList();
            break;
        case 'guides':
            loadGuidesList();
            break;
        case 'users':
            loadUsersList();
            break;
    }
}

// --- Dashboard Logic ---
async function loadDashboardStats() {
    try {
        // Load all news
        const { data: allNews, error } = await supabase
            .from('featured_news')
            .select('*')
            .order('created_at', { ascending: false });

        if (error) throw error;

        // Calculate stats
        const published = allNews.filter(n => n.status === 'published');

        // Update DOM
        document.getElementById('totalPosts').textContent = allNews.length;
        document.getElementById('publishedPosts').textContent = published.length;

        // Load recent posts (top 5)
        renderRecentPosts(allNews.slice(0, 5));
    } catch (e) {
        console.error('Error loading dashboard:', e);
    }
}

function renderRecentPosts(posts) {
    const container = document.getElementById('recentPosts');
    if (!container) return;

    if (!posts || posts.length === 0) {
        container.innerHTML = `
            <div class="p-6 text-center text-gray-500">
                <i data-lucide="file-text" class="w-12 h-12 mx-auto mb-2 opacity-50"></i>
                <p>Chưa có bài viết nào</p>
                <button onclick="openNewsEditor()" 
                    class="mt-2 text-red-600 hover:text-red-700">
                    Viết bài viết đầu tiên
                </button>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
        return;
    }

    container.innerHTML = posts.map(post => `
        <div class="p-4 hover:bg-gray-50 transition-colors cursor-pointer" 
            onclick="openNewsEditor(${post.id})")>
            <div class="flex gap-4">
                ${post.thumbnail_url ? `
                    <img src="${post.thumbnail_url}" alt="${post.title}" 
                        class="w-16 h-16 rounded-xl object-cover flex-shrink-0">
                ` : `
                    <div class="w-16 h-16 rounded-xl bg-gray-100 flex items-center justify-center flex-shrink-0">
                        <i data-lucide="image" class="w-6 h-6 text-gray-400"></i>
                    </div>
                `}
                <div class="flex-1 min-w-0">
                    <h4 class="font-medium text-gray-900 truncate">${post.title}</h4>
                    <p class="text-sm text-gray-500 mt-1">${new Date(post.created_at).toLocaleDateString('vi-VN')}</p>
                </div>
                <div class="flex items-center gap-2">
                    <span class="px-2 py-1 ${post.status === 'published' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'} text-xs rounded-full">
                        ${post.status === 'published' ? 'Đã đăng' : 'Bản nháp'}
                    </span>
                    ${post.is_pinned ? '<span class="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full">Ghim</span>' : ''}
                </div>
            </div>
        </div>
    `).join('');

    if (window.lucide) lucide.createIcons();
}


// --- Users Logic ---
async function loadUsersList() {
    const listContainer = document.getElementById('usersList');
    if (!listContainer) return;

    listContainer.innerHTML = '<tr><td colspan="4" class="text-center py-4">Đang tải...</td></tr>';

    // Add Table Header if missing (since we only have tbody in HTML)
    // Actually, HTML structure for users view is missing table wrapper. 
    // Let's inject a simple table if the container is just the div.
    // Wait, let's fix the HTML structure in index.html first? 
    // No, I'll just clear the container and append a table structure if I can.
    // But wait, the HTML I wrote has `<div class="bg-white..."><p>...</p><tbody id="usersList"></tbody></div>`. 
    // This is invalid HTML (tbody/tr inside div). I need to fix the HTML structure for Users first.
    // However, assuming I fix HTML, here is the JS:

    try {
        const { data: users, error } = await supabase
            .from('admin_users')
            .select('*')
            .order('created_at', { ascending: false });

        if (error) throw error;

        // Note: I need to output TRs here.
        listContainer.innerHTML = users.map(user => `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4">
                    <div class="font-medium text-gray-900">${user.full_name || user.username}</div>
                    <div class="text-sm text-gray-500">${user.email}</div>
                </td>
                 <td class="px-6 py-4 capitalize">${user.role}</td>
                 <td class="px-6 py-4">
                    <span class="px-2 py-1 rounded-full text-xs font-medium ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                        ${user.is_active ? 'Hoạt động' : 'Đã khóa'}
                    </span>
                 </td>
                 <td class="px-6 py-4 text-sm text-gray-500">
                    ${new Date(user.created_at).toLocaleDateString('vi-VN')}
                 </td>
            </tr>
        `).join('');
    } catch (e) {
        listContainer.innerHTML = `<tr><td colspan="4" class="text-center text-red-500 py-4">Lỗi: ${e.message}</td></tr>`;
    }
}
async function loadNewsList() {
    const listContainer = document.getElementById('newsList');
    if (!listContainer) return;

    listContainer.innerHTML = '<tr><td colspan="5" class="text-center py-4">Đang tải...</td></tr>';

    try {
        // Exclude guides: neither has tag "hướng dẫn" nor category "Hướng dẫn"
        const { data: posts, error } = await supabase
            .from('featured_news')
            .select('*')
            .not('tags', 'cs', '{"hướng dẫn"}')
            .neq('category', 'huong-dan')
            .order('created_at', { ascending: false });

        if (error) throw error;

        if (!posts || posts.length === 0) {
            listContainer.innerHTML = '<tr><td colspan="5" class="text-center py-4">Chưa có bài viết nào.</td></tr>';
            return;
        }

        listContainer.innerHTML = posts.map(post => `
            <tr class="hover:bg-gray-50 transition-colors">
                <td class="px-6 py-4">
                    <div class="flex items-center gap-3">
                        <img src="${post.thumbnail_url || '../logo.png'}" class="w-10 h-10 rounded-lg object-cover bg-gray-100">
                        <div class="font-medium text-gray-900 line-clamp-1">${post.title}</div>
                    </div>
                </td>
                <td class="px-6 py-4 text-gray-500">${post.category || 'Tin tức'}</td>
                <td class="px-6 py-4">
                     <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${post.status === 'published' ? 'bg-green-100 text-green-800' :
                post.status === 'draft' ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'
            }">
                        ${post.status === 'published' ? 'Đã đăng' : 'Bản nháp'}
                    </span>
                </td>
                <td class="px-6 py-4 text-gray-500 text-sm">
                    ${new Date(post.created_at).toLocaleDateString('vi-VN')}
                </td>
                <td class="px-6 py-4">
                    <div class="flex items-center gap-2">
                        <button onclick="clonePost('${post.id}')"
                            class="p-2 text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
                            title="Nhân bản">
                            <i data-lucide="copy" class="w-4 h-4"></i>
                        </button>
                        <a href="/admin/admin-news-edit.html?id=${post.id}" target="_blank"
                            class="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                            <i data-lucide="edit-2" class="w-4 h-4"></i>
                        </a>
                        <button onclick="deletePost('${post.id}')"
                            class="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                            <i data-lucide="trash-2" class="w-4 h-4"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');

        if (window.lucide) lucide.createIcons();

    } catch (err) {
        console.error('Load news error:', err);
        listContainer.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-red-500">Lỗi tải dữ liệu: ${err.message}</td></tr>`;
    }
}

async function clonePost(id) {
    try {
        // 1. Get the original post
        const { data: original, error: fetchError } = await supabase
            .from('featured_news')
            .select('*')
            .eq('id', id)
            .single();
        
        if (fetchError) throw fetchError;
        if (!original) {
            alert('Không tìm thấy bài viết gốc!');
            return;
        }

        if (!confirm(`Nhân bản bài viết "${original.title}"?\n\nBài viết mới sẽ được tạo dưới dạng "Bản nháp".`)) {
            return;
        }

        // 2. Prepare cloned data
        const cloneData = {
            title: original.title ? `${original.title} (Bản sao)` : 'Bài viết sao chép',
            slug: original.slug ? `${original.slug}-copy-${Date.now()}` : `post-copy-${Date.now()}`,
            summary: original.summary || '',
            content: original.content || null, // JSON array
            content_html: original.content_html || null, // Keep for backward compatibility
            thumbnail_url: original.thumbnail_url || '',
            category: original.category || 'tin-tuc',
            tags: original.tags || [],
            keyword_aliases: original.keyword_aliases || [],
            status: 'draft', // Always save as draft
            is_featured: false, // Reset featured
            is_pinned: false, // Reset pinned
            author_id: original.author_id,
            created_at: new Date().toISOString(),
            published_at: null // Reset publish date
        };

        // 3. Insert as new post
        const { data: newPost, error: insertError } = await supabase
            .from('featured_news')
            .insert(cloneData)
            .select()
            .single();

        if (insertError) throw insertError;

        // 4. Success - reload list
        loadNewsList();
        
        // Show success message
        const notification = document.createElement('div');
        notification.className = 'fixed bottom-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 flex items-center gap-2';
        notification.innerHTML = '<i data-lucide="check-circle" class="w-5 h-5"></i> Đã nhân bản thành công!';
        document.body.appendChild(notification);
        if (window.lucide) lucide.createIcons();
        setTimeout(() => notification.remove(), 3000);

    } catch (err) {
        console.error('Clone post error:', err);
        alert('Lỗi nhân bản: ' + err.message);
    }
}

async function deletePost(id) {
    if (!confirm('Bạn có chắc chắn muốn xóa bài viết này?')) return;
    try {
        const { error } = await supabase.from('featured_news').delete().eq('id', id);
        if (error) throw error;
        loadNewsList(); // Reload
        loadGuidesList(); // Also reload guides if deleted from there
    } catch (e) {
        alert('Lỗi xóa bài: ' + e.message);
    }
}

// --- Guides Logic ---
async function loadGuidesList() {
    const listContainer = document.getElementById('guidesList');
    if (!listContainer) return;

    listContainer.innerHTML = '<tr><td colspan="5" class="text-center py-4">Đang tải...</td></tr>';

    try {
        // Get guides: either has tag "hướng dẫn" OR category "Hướng dẫn"
        const { data: posts, error } = await supabase
            .from('featured_news')
            .select('*')
            .or('tags.cs.{"hướng dẫn"},category.eq.huong-dan')
            .order('created_at', { ascending: false });

        if (error) throw error;

        if (!posts || posts.length === 0) {
            listContainer.innerHTML = '<tr><td colspan="5" class="text-center py-4">Chưa có bài hướng dẫn nào.</td></tr>';
            return;
        }

        listContainer.innerHTML = posts.map(post => `
            <tr class="hover:bg-gray-50 transition-colors">
                <td class="px-6 py-4">
                    <div class="flex items-center gap-3">
                        <img src="${post.thumbnail_url || '../logo.png'}" class="w-10 h-10 rounded-lg object-cover bg-gray-100">
                        <div class="font-medium text-gray-900 line-clamp-1">${post.title}</div>
                    </div>
                </td>
                <td class="px-6 py-4 text-gray-500">${post.category || 'Hướng dẫn'}</td>
                <td class="px-6 py-4">
                     <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${post.status === 'published' ? 'bg-green-100 text-green-800' :
                post.status === 'draft' ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'
            }">
                        ${post.status === 'published' ? 'Đã đăng' : 'Bản nháp'}
                    </span>
                </td>
                <td class="px-6 py-4 text-gray-500 text-sm">
                    ${new Date(post.created_at).toLocaleDateString('vi-VN')}
                </td>
                <td class="px-6 py-4">
                    <div class="flex items-center gap-2">
                        <button onclick="clonePost('${post.id}')"
                            class="p-2 text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
                            title="Nhân bản">
                            <i data-lucide="copy" class="w-4 h-4"></i>
                        </button>
                        <a href="/admin/admin-news-edit.html?id=${post.id}" target="_blank"
                            class="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                            <i data-lucide="edit-2" class="w-4 h-4"></i>
                        </a>
                        <button onclick="deletePost('${post.id}')"
                            class="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                            <i data-lucide="trash-2" class="w-4 h-4"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');

        if (window.lucide) lucide.createIcons();

    } catch (err) {
        console.error('Load guides error:', err);
        listContainer.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-red-500">Lỗi tải dữ liệu: ${err.message}</td></tr>`;
    }
}



// ==========================================
// PASSWORD CHANGE
// ==========================================
async function handleChangePassword(event) {
    event.preventDefault();

    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    // Validation
    if (newPassword !== confirmPassword) {
        showToast('Mật khẩu xác nhận không khớp!', 'error');
        return;
    }

    if (newPassword.length < 6) {
        showToast('Mật khẩu phải ít nhất 6 ký tự!', 'error');
        return;
    }

    if (currentPassword === newPassword) {
        showToast('Mật khẩu mới phải khác mật khẩu hiện tại!', 'error');
        return;
    }

    try {
        // Step 1: Verify current password
        const { data: userData } = await supabase.auth.getUser();
        if (!userData?.user?.email) {
            showToast('Không tìm thấy thông tin người dùng!', 'error');
            return;
        }

        const { error: signInError } = await supabase.auth.signInWithPassword({
            email: userData.user.email,
            password: currentPassword
        });

        if (signInError) {
            showToast('Mật khẩu hiện tại không đúng!', 'error');
            return;
        }

        // Step 2: Update to new password
        const { error } = await supabase.auth.updateUser({
            password: newPassword
        });

        if (error) throw error;

        showToast('Đã đổi mật khẩu thành công!', 'success');
        document.getElementById('passwordForm').reset();
    } catch (err) {
        console.error('Password change error:', err);
        showToast('Lỗi: ' + err.message, 'error');
    }
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 px-6 py-4 rounded-xl shadow-lg z-50 flex items-center gap-3 ${type === 'success' ? 'bg-green-600' : 'bg-red-600'
        } text-white`;

    const icon = type === 'success' ? 'check-circle' : 'alert-circle';
    toast.innerHTML = `
        <i data-lucide="${icon}" class="w-5 h-5"></i>
        <span class="font-medium">${message}</span>
    `;

    document.body.appendChild(toast);
    lucide.createIcons();

    setTimeout(() => {
        toast.style.transition = 'opacity 0.3s';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ==========================================
// CREATE ADMIN MODAL
// ==========================================
function openCreateAdminModal() {
    const modal = document.getElementById('createAdminModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    lucide.createIcons();
}

function closeCreateAdminModal() {
    const modal = document.getElementById('createAdminModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    document.getElementById('createAdminForm').reset();
}

async function handleCreateAdmin(event) {
    event.preventDefault();

    const email = document.getElementById('newAdminEmail').value;
    const password = document.getElementById('newAdminPassword').value;
    const name = document.getElementById('newAdminName').value;

    try {
        const response = await fetch('/api/create-admin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, full_name: name })
        });

        const result = await response.json();

        if (result.error) {
            showToast('❌ ' + result.error, 'error');
            return;
        }

        if (result.success) {
            showToast('✅ Đã tạo admin mới thành công!', 'success');
            closeCreateAdminModal();
            loadUsersList();
        }

    } catch (err) {
        console.error('Create admin error:', err);
        showToast('❌ Lỗi: ' + err.message, 'error');
    }
}
