// ==========================================
// KEYWORD ALIASES MANAGEMENT
// ==========================================
let currentAliases = [];

function addAlias() {
    const input = document.getElementById('aliasInput');
    const alias = input.value.trim().toLowerCase();

    if (!alias) {
        showToast('Vui lòng nhập từ khóa');
        return;
    }

    if (alias.length > 100) {
        showToast('Từ khóa quá dài (tối đa 100 ký tự)');
        return;
    }

    if (currentAliases.includes(alias)) {
        showToast('Từ khóa đã tồn tại');
        return;
    }

    if (currentAliases.length >= 20) {
        showToast('Đã đạt giới hạn 20 từ khóa');
        return;
    }

    currentAliases.push(alias);
    renderAliases();
    input.value = '';
    input.focus();
}

function removeAlias(alias) {
    currentAliases = currentAliases.filter(a => a !== alias);
    renderAliases();
}

function renderAliases() {
    const container = document.getElementById('aliasesContainer');

    if (!container) return;

    if (currentAliases.length === 0) {
        container.innerHTML = '<p class="text-sm text-gray-400 italic">Chưa có từ khóa liên kết nào</p>';
        return;
    }

    container.innerHTML = currentAliases.map(alias => `
        <span class="inline-flex items-center gap-1 bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
            ${alias}
            <button 
                onclick="removeAlias('${alias.replace(/'/g, "\\'")}')" 
                class="hover:text-blue-600 transition-colors"
                type="button">
                <i data-lucide="x" class="w-3 h-3"></i>
            </button>
        </span>
    `).join('');

    if (window.lucide) lucide.createIcons();
}

// Load aliases when editing existing post
window.addEventListener('DOMContentLoaded', () => {
    renderAliases();
});

// Function to load aliases from post object (called from admin-news-edit.html)
function loadAliasesFromPost(post) {
    if (post && post.keyword_aliases && Array.isArray(post.keyword_aliases)) {
        currentAliases = post.keyword_aliases.filter(a => a && typeof a === 'string');
        renderAliases();
    }
}

// Export for use in editor
window.loadAliasesFromPost = loadAliasesFromPost;
