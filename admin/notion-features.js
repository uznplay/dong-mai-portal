// ==========================================
// GLOBAL BUTTON SETTINGS (Persisted)
// ==========================================
let buttonSettings = {
    background: '#ce7a58',  // SOLID COLOR - not gradient
    textColor: '#ffffff',
    fontSize: '14px',
    padding: '10px 24px',
    borderRadius: '8px'
};

// Load saved settings - but ensure it's always solid color
if (localStorage.getItem('buttonSettings')) {
    try {
        const saved = JSON.parse(localStorage.getItem('buttonSettings'));
        // Override any gradient with solid color
        buttonSettings = { ...buttonSettings, ...saved, background: '#ce7a58' };
    } catch (e) {}
}

function saveButtonSettings() {
    localStorage.setItem('buttonSettings', JSON.stringify(buttonSettings));
}

// ==========================================
// GLOBAL BUTTON FUNCTIONS
// ==========================================

// Edit button - shows editor panel
window.editButton = function(buttonId) {
    const btn = document.getElementById(buttonId);
    if (!btn) return;
    showButtonEditor(btn);
};

// Edit Link URL only
window.editButtonLink = function(buttonId) {
    const btn = document.getElementById(buttonId);
    if (!btn) return;
    const currentUrl = btn.dataset.url || '';
    const newUrl = prompt('Sửa đường dẫn URL:', currentUrl);
    if (newUrl && newUrl.trim() !== '' && newUrl !== currentUrl) {
        btn.dataset.url = newUrl;
        showToast('Đã cập nhật liên kết');
    }
    hideButtonToolbar();
};

// Change background color
window.changeButtonColor = function(buttonId, color) {
    const btn = document.getElementById(buttonId);
    if (!btn) return;
    btn.style.background = color;
    btn.dataset.background = color;
    buttonSettings.background = color;
    saveButtonSettings();
    showToast('Đã đổi màu nền');
};

// Change text color
window.changeButtonTextColor = function(buttonId, color) {
    const btn = document.getElementById(buttonId);
    if (!btn) return;
    btn.style.color = color;
    btn.dataset.textColor = color;
    buttonSettings.textColor = color;
    saveButtonSettings();
    showToast('Đã đổi màu chữ');
};

// Change border radius
window.changeButtonRadius = function(buttonId, radius) {
    const btn = document.getElementById(buttonId);
    if (!btn) return;
    btn.style.borderRadius = radius;
    btn.dataset.borderRadius = radius;
    buttonSettings.borderRadius = radius;
    saveButtonSettings();
    showToast('Đã đổi độ bo tròn');
};

// Change button size
window.changeButtonSize = function(buttonId, size) {
    const btn = document.getElementById(buttonId);
    if (!btn) return;
    const sizes = {
        small: { padding: '6px 16px', fontSize: '12px' },
        medium: { padding: '10px 24px', fontSize: '14px' },
        large: { padding: '14px 32px', fontSize: '16px' }
    };
    if (sizes[size]) {
        btn.style.padding = sizes[size].padding;
        btn.style.fontSize = sizes[size].fontSize;
        btn.dataset.size = size;
        buttonSettings.padding = sizes[size].padding;
        buttonSettings.fontSize = sizes[size].fontSize;
        saveButtonSettings();
    }
    showToast('Đã đổi kích cỡ');
};

// Delete button
window.deleteButton = function(buttonId) {
    const btn = document.getElementById(buttonId);
    if (!btn) return;
    const text = btn.textContent;
    const textNode = document.createTextNode(text);
    btn.parentNode.replaceChild(textNode, btn);
    const selection = window.getSelection();
    const range = document.createRange();
    range.setStart(textNode, text.length);
    range.collapse(true);
    selection.removeAllRanges();
    selection.addRange(range);
    showToast('Đã xóa nút');
    hideButtonToolbar();
};

// Delete code format
window.deleteCode = function(codeId) {
    const codeEl = document.getElementById(codeId);
    if (!codeEl) return;
    const text = codeEl.textContent;
    const textNode = document.createTextNode(text);
    codeEl.parentNode.replaceChild(textNode, codeEl);
    const selection = window.getSelection();
    const range = document.createRange();
    range.setStart(textNode, text.length);
    range.collapse(true);
    selection.removeAllRanges();
    selection.addRange(range);
    showToast('Đã xóa định dạng code');
};

// ==========================================
// GLOBAL VARIABLES
// ==========================================
let selectedBlockId = null;
let textToolbar = null;
let blockActionsMenu = null;
let buttonToolbarEl = null;
let buttonEditorEl = null;
let currentBlockForSelector = null;

// ==========================================
// EXPOSE GLOBALS IMMEDIATELY
// ==========================================
window.showBlockMenuFor = showBlockMenuFor;
window.showBlockActions = showBlockActions;
window.removeBlock = removeBlock;
window.moveBlock = moveBlockById;
window.addBlock = addBlock;
window.formatText = formatText;
window.setBlockType = setBlockType;
window.setColor = setColor;
window.toggleDropdown = toggleDropdown;
window.updateSlug = updateSlug;
window.toggleSettings = toggleSettings;
window.insertOrEditLink = insertOrEditLink;
window.showButtonToolbar = showButtonToolbar;
window.hideButtonToolbar = hideButtonToolbar;
window.showButtonColors = showButtonColors;
window.showButtonTextColors = showButtonTextColors;
window.duplicateBlock = duplicateBlock;
window.editButton = editButton;
window.deleteButton = deleteButton;
window.changeButtonColor = changeButtonColor;
window.changeButtonTextColor = changeButtonTextColor;
window.changeButtonRadius = changeButtonRadius;
window.changeButtonSize = changeButtonSize;

// ==========================================
// DOMContentLoaded
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        initEditorFeatures();
        const editor = document.getElementById('notionEditor');
        if (editor && editor.children.length === 0) {
            addBlock('paragraph', true);
        }
    }, 50);
});

function initEditorFeatures() {
    initKeyboardShortcuts();
    initTextToolbar();
    initInlineElementHandlers();

    const editor = document.getElementById('notionEditor');
    if (editor) {
        editor.addEventListener('input', autoSaveDraft);
        // Save when clicking outside (blur) - ensures link/content is saved before leaving
        editor.addEventListener('blur', autoSaveDraft);
    }
    const title = document.getElementById('postTitle');
    if (title) {
        title.addEventListener('input', () => {
            updateSlug();
            autoSaveDraft();
        });
        // Save when clicking outside (blur)
        title.addEventListener('blur', autoSaveDraft);
    }

    // Add blur handlers to all form fields to save when clicking outside
    const formFields = ['postSummary', 'postCategory', 'postTags', 'thumbnailUrlInput'];
    formFields.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('blur', autoSaveDraft);
            // Also trigger on change for select elements
            el.addEventListener('change', autoSaveDraft);
        }
    });

    // Add blur handler for thumbnail file input
    const thumbnailInput = document.getElementById('thumbnailInput');
    if (thumbnailInput) {
        thumbnailInput.addEventListener('change', autoSaveDraft);
    }

    document.addEventListener('click', (e) => {
        if (blockActionsMenu && blockActionsMenu.classList.contains('active') && !e.target.closest('#blockActionsMenu')) {
            hideBlockActionsMenu();
        }

        const slashMenu = document.getElementById('slashMenu');
        const isClickingToolbar = e.target.closest('#textToolbar') || e.target.closest('.toolbar-btn');
        const isClickingDropdown = e.target.closest('.toolbar-dropdown-menu');
        const isClickingBlockMenu = e.target.closest('.block-add-btn');
        const isClickingSlashMenu = e.target.closest('#slashMenu');
        const isClickingSettings = e.target.closest('#toggleSettingsBtn');
        const isClickingButtonEditor = e.target.closest('#buttonEditor');

        if (slashMenu && !slashMenu.classList.contains('hidden') &&
            !isClickingSlashMenu && !isClickingToolbar && !isClickingDropdown &&
            !isClickingBlockMenu && !isClickingSettings && !isClickingButtonEditor) {
            slashMenu.classList.add('hidden');
            slashMenu.classList.remove('block');
        }

        if (!isClickingToolbar && !isClickingDropdown) {
            document.querySelectorAll('.toolbar-dropdown-menu').forEach(el => {
                el.classList.remove('active');
            });
        }

        if (buttonToolbarEl && !buttonToolbarEl.contains(e.target) && !e.target.classList.contains('inline-button')) {
            hideButtonToolbar();
        }

        if (buttonEditorEl && !buttonEditorEl.contains(e.target) && !e.target.classList.contains('inline-button')) {
            hideButtonEditor();
        }
    });
}

// ==========================================
// INLINE ELEMENT HANDLERS (Button & Code) - V3
// ==========================================
// INLINE ELEMENT HANDLERS (Button & Code) - V4 FINAL
// ==========================================
function initInlineElementHandlers() {
    const editor = document.getElementById('notionEditor');
    if (!editor) return;

    // Click on inline element = FOCUS
    editor.addEventListener('mousedown', function(e) {
        if (e.target.classList.contains('inline-button')) {
            e.preventDefault();
            e.target.focus();
            e.target.classList.add('editing');
        }
        if (e.target.classList.contains('inline-code')) {
            e.preventDefault();
            e.target.focus();
            e.target.classList.add('editing');
        }
    });

    // Double click = show toolbar
    editor.addEventListener('dblclick', function(e) {
        if (e.target.classList.contains('inline-button')) {
            e.stopPropagation();
            showButtonEditor(e.target);
        }
        if (e.target.classList.contains('inline-code')) {
            e.stopPropagation();
            showCodeToolbar(e.target);
        }
    });

    // Mouse DOWN outside = Exit element
    document.addEventListener('mousedown', function(e) {
        const editor = document.getElementById('notionEditor');
        const clickedInline = e.target.closest('.inline-button') || e.target.closest('.inline-code');
        const clickedToolbar = e.target.closest('.button-editor') || e.target.closest('#codeToolbar');

        if (!clickedInline && !clickedToolbar) {
            // User clicked outside - exit any editing element
            exitAllInlineElements();
        }
    });

    // Keyboard handling
    editor.addEventListener('keydown', function(e) {
        const activeEl = document.activeElement;

        if (activeEl.classList.contains('inline-button') || activeEl.classList.contains('inline-code')) {
            const selection = window.getSelection();
            if (!selection || selection.rangeCount === 0) return;

            const range = selection.getRangeAt(0);
            const textLength = activeEl.textContent.length;
            const atStart = range.startOffset === 0;
            const atEnd = range.endOffset === textLength;

            // ESCAPE = Exit
            if (e.key === 'Escape') {
                e.preventDefault();
                exitInlineElement(activeEl);
                return;
            }

            // SHIFT + ENTER = Exit inline element immediately
            if (e.key === 'Enter' && e.shiftKey) {
                e.preventDefault();
                e.stopPropagation(); // Prevent bubbling to main keyboard handler
                exitInlineElement(activeEl);
                return;
            }

            // Arrow keys at edge = Exit (without Shift)
            if ((e.key === 'ArrowLeft' && atStart) ||
                (e.key === 'ArrowRight' && atEnd) ||
                (e.key === 'ArrowUp' && atStart) ||
                (e.key === 'ArrowDown' && atEnd)) {

                if (!e.shiftKey) {
                    e.preventDefault();
                    e.stopPropagation(); // Prevent bubbling
                    exitInlineElement(activeEl);
                    return;
                }
            }

            // Backspace at start OR Delete at end = Remove element
            if ((e.key === 'Backspace' && atStart) ||
                (e.key === 'Delete' && atEnd)) {
                e.preventDefault();
                e.stopPropagation(); // Prevent bubbling
                removeInlineElement(activeEl);
                return;
            }

            // ESCAPE = Exit
            if (e.key === 'Escape') {
                e.preventDefault();
                e.stopPropagation(); // Prevent bubbling
                exitInlineElement(activeEl);
                return;
            }
        }
    });
}

function exitAllInlineElements() {
    const editor = document.getElementById('notionEditor');
    if (!editor) return;

    editor.querySelectorAll('.inline-button.editing, .inline-code.editing').forEach(el => {
        exitInlineElement(el);
    });
}

function exitInlineElement(el) {
    el.classList.remove('editing');

    const selection = window.getSelection();
    if (!selection) return;

    // Create a range that starts AFTER the element
    const range = document.createRange();
    range.setStartAfter(el);
    range.collapse(true);

    selection.removeAllRanges();
    selection.addRange(range);

    // Focus back on editor to ensure we're "out"
    const editor = document.getElementById('notionEditor');
    if (editor) {
        editor.focus();
    }
}

function removeInlineElement(el) {
    const parent = el.parentNode;
    const text = el.textContent;

    // Create text node with content
    const textNode = document.createTextNode(text);
    parent.insertBefore(textNode, el);
    parent.removeChild(el);

    // Move cursor to text
    const selection = window.getSelection();
    const range = document.createRange();
    range.setStart(textNode, text.length);
    range.collapse(true);
    selection.removeAllRanges();
    selection.addRange(range);

    showToast('Đã xóa');
}

function showButtonToolbar(event, buttonId) {
    event.stopPropagation();

    if (!buttonToolbarEl) {
        buttonToolbarEl = document.createElement('div');
        buttonToolbarEl.id = 'buttonToolbar';
        buttonToolbarEl.className = 'button-toolbar';
        document.body.appendChild(buttonToolbarEl);
    }

    const rect = event.target.getBoundingClientRect();
    buttonToolbarEl.style.left = rect.left + 'px';
    buttonToolbarEl.style.top = (rect.top - 50) + 'px';

    buttonToolbarEl.innerHTML = `
        <button class="btn-toolbar-btn" onclick="editButton('${buttonId}')" title="Chỉnh sửa">✏️ Sửa</button>
        <button class="btn-toolbar-btn" onclick="deleteButton('${buttonId}')" title="Xóa nút" style="color: red;">🗑️ Xóa</button>
    `;

    buttonToolbarEl.classList.add('active');
}

function hideButtonToolbar() {
    if (buttonToolbarEl) buttonToolbarEl.classList.remove('active');
}

function showButtonEditor(btn) {
    // Ensure button has an ID
    if (!btn.id) {
        btn.id = 'btn-' + Date.now() + Math.floor(Math.random() * 1000);
        console.log('Generated new btn.id:', btn.id);
    }

    hideButtonEditor();

    buttonEditorEl = document.createElement('div');
    buttonEditorEl.id = 'buttonEditor';
    buttonEditorEl.className = 'button-editor';

    const rect = btn.getBoundingClientRect();
    buttonEditorEl.style.left = rect.left + 'px';
    buttonEditorEl.style.top = (rect.top + rect.height + 10) + 'px';

    const currentBg = btn.style.background || buttonSettings.background;
    const currentTextColor = btn.style.color || buttonSettings.textColor;
    const currentRadius = btn.style.borderRadius || buttonSettings.borderRadius;
    const currentSize = btn.dataset.size || 'medium';

    buttonEditorEl.innerHTML = `
        <div class="editor-section">
            <label>📝 Nội dung:</label>
            <input type="text" id="btnTextInput" value="${btn.textContent}" placeholder="Nhập text" oninput="updateButtonText('${btn.id}', this.value)">
        </div>
        <div class="editor-section">
            <label>🔗 Link:</label>
            <input type="text" id="btnUrlInput" value="${btn.dataset.url || 'https://'}" placeholder="Nhập URL" oninput="updateButtonFromEditor('${btn.id}')">
        </div>
        <div class="editor-section">
            <label>🎨 Màu chữ:</label>
            <button class="color-btn" onclick="showButtonTextColors('${btn.id}')" style="background: ${currentTextColor}; width: 36px; height: 36px; border-radius: 50%; border: 2px solid #ddd;"></button>
        </div>
        <div class="editor-section">
            <label>⬜ Màu nền:</label>
            <button class="color-btn" onclick="showButtonColors('${btn.id}')" style="background: ${currentBg}; width: 36px; height: 36px; border-radius: 6px; border: 2px solid #ddd;"></button>
        </div>
        <div class="editor-section">
            <label>📐 Bo tròn:</label>
            <select id="btnRadiusSelect" onchange="changeButtonRadius('${btn.id}', this.value);">
                <option value="0px" ${currentRadius === '0px' ? 'selected' : ''}>Vuông (0px)</option>
                <option value="4px" ${currentRadius === '4px' ? 'selected' : ''}>Nhọn (4px)</option>
                <option value="8px" ${currentRadius === '8px' ? 'selected' : ''}>Tròn vừa (8px)</option>
                <option value="16px" ${currentRadius === '16px' ? 'selected' : ''}>Tròn (16px)</option>
                <option value="50px" ${currentRadius === '50px' ? 'selected' : ''}>Tròn đều (50px)</option>
            </select>
        </div>
        <div class="editor-section">
            <label>📏 Kích cỡ:</label>
            <select id="btnSizeSelect" onchange="changeButtonSize('${btn.id}', this.value);">
                <option value="small" ${currentSize === 'small' ? 'selected' : ''}>Nhỏ (12px)</option>
                <option value="medium" ${currentSize === 'medium' ? 'selected' : ''}>Vừa (14px)</option>
                <option value="large" ${currentSize === 'large' ? 'selected' : ''}>Lớn (16px)</option>
            </select>
        </div>
        <div class="editor-section">
            <button class="save-btn" onclick="saveButtonAndClose('${btn.id}')">💾 Lưu & Đóng</button>
        </div>
        <div class="editor-section">
            <button class="delete-btn" onclick="deleteButton('${btn.id}')">🗑️ Xóa nút</button>
        </div>
    `;

    document.body.appendChild(buttonEditorEl);

    setTimeout(() => {
        const urlInput = document.getElementById('btnUrlInput');
        if (urlInput) {
            urlInput.focus();
            urlInput.select();
        }
    }, 100);
}

function updateButtonFromEditor(buttonId) {
    const btn = document.getElementById(buttonId);
    if (!btn) return;
    const urlInput = document.getElementById('btnUrlInput');
    if (urlInput && urlInput.value.trim() !== '' && urlInput.value !== 'https://') {
        btn.dataset.url = urlInput.value;
    }
}

function updateButtonText(buttonId, newText) {
    const btn = document.getElementById(buttonId);
    if (!btn) return;
    btn.textContent = newText;
}

function hideButtonEditor() {
    if (buttonEditorEl) {
        buttonEditorEl.remove();
        buttonEditorEl = null;
    }
}

// Save button changes and close editor
async function saveButtonAndClose(buttonId) {
    hideButtonEditor();

    // Debug log button
    const btn = document.getElementById(buttonId);
    console.log('Button ID:', buttonId);
    console.log('Button found:', !!btn);
    console.log('Button data-url BEFORE:', btn ? btn.dataset.url : 'N/A');

    // Force update blocks to capture button changes
    updateBlocks();
    console.log('Blocks count:', blocks.length);
    console.log('First block content:', blocks[0] ? blocks[0].content : 'N/A');

    // Get current post data and update only content
    if (currentPostId) {
        try {
            const { error } = await supabase
                .from('featured_news')
                .update({ content: blocks })
                .eq('id', currentPostId);

            if (error) throw error;

            console.log('Saved successfully!');

            // Show success
            const saveStatus = document.getElementById('saveStatus');
            if (saveStatus) {
                saveStatus.textContent = 'Đã lưu liên kết!';
                saveStatus.classList.add('text-green-600');
                setTimeout(() => {
                    saveStatus.textContent = 'Đã lưu';
                    saveStatus.classList.remove('text-green-600');
                }, 2000);
            }
        } catch (err) {
            console.error('Error saving button:', err);
            alert('Lỗi lưu: ' + err.message);
        }
    } else {
        console.log('No currentPostId - cannot save');
        alert('Vui lưu tiêu đề trước khi lưu liên kết!');
    }
}

function showButtonColors(buttonId) {
    const btn = document.getElementById(buttonId);
    if (!btn) return;

    const colorMenu = document.createElement('div');
    colorMenu.className = 'color-picker-menu';
    colorMenu.innerHTML = `
        <div class="color-grid">
            <div class="color-option solid" style="background: #ce7a58" onclick="changeButtonColor('${buttonId}', '#ce7a58'); this.parentElement.parentElement.remove()">Mặc định</div>
            <div class="color-option solid" style="background: #dc2626" onclick="changeButtonColor('${buttonId}', '#dc2626'); this.parentElement.parentElement.remove()">Đỏ</div>
            <div class="color-option solid" style="background: #16a34a" onclick="changeButtonColor('${buttonId}', '#16a34a'); this.parentElement.parentElement.remove()">Xanh lá</div>
            <div class="color-option solid" style="background: #2563eb" onclick="changeButtonColor('${buttonId}', '#2563eb'); this.parentElement.parentElement.remove()">Xanh dương</div>
            <div class="color-option solid" style="background: #7c3aed" onclick="changeButtonColor('${buttonId}', '#7c3aed'); this.parentElement.parentElement.remove()">Tím</div>
            <div class="color-option solid" style="background: #ea580c" onclick="changeButtonColor('${buttonId}', '#ea580c'); this.parentElement.parentElement.remove()">Cam</div>
            <div class="color-option solid" style="background: #0891b2" onclick="changeButtonColor('${buttonId}', '#0891b2'); this.parentElement.parentElement.remove()">Xanh biển</div>
            <div class="color-option solid" style="background: #1a1a2e" onclick="changeButtonColor('${buttonId}', '#1a1a2e'); this.parentElement.parentElement.remove()">Đen</div>
            <div class="color-option solid" style="background: #ffffff; border: 1px solid #ddd" onclick="changeButtonColor('${buttonId}', '#ffffff'); this.parentElement.parentElement.remove()">Trắng</div>
        </div>
        <input type="color" id="customColorInput" onchange="changeButtonColor('${buttonId}', this.value); this.parentElement.remove()" title="Chọn màu tùy chỉnh">
    `;

    const editorRect = document.getElementById('buttonEditor')?.getBoundingClientRect();
    if (editorRect) {
        colorMenu.style.position = 'fixed';
        colorMenu.style.left = editorRect.left + 'px';
        colorMenu.style.top = (editorRect.top - 120) + 'px';
        colorMenu.style.zIndex = '10002';
        document.body.appendChild(colorMenu);
    }
}

function showButtonTextColors(buttonId) {
    const btn = document.getElementById(buttonId);
    if (!btn) return;

    const colorMenu = document.createElement('div');
    colorMenu.className = 'color-picker-menu';
    colorMenu.innerHTML = `
        <div class="color-grid">
            <div class="color-option solid" style="background: #ffffff; border: 1px solid #ddd" onclick="changeButtonTextColor('${buttonId}', '#ffffff'); this.parentElement.parentElement.remove()">Trắng</div>
            <div class="color-option solid" style="background: #1a1a2e" onclick="changeButtonTextColor('${buttonId}', '#1a1a2e'); this.parentElement.parentElement.remove()">Đen</div>
            <div class="color-option solid" style="background: #dc2626" onclick="changeButtonTextColor('${buttonId}', '#dc2626'); this.parentElement.parentElement.remove()">Đỏ</div>
            <div class="color-option solid" style="background: #16a34a" onclick="changeButtonTextColor('${buttonId}', '#16a34a'); this.parentElement.parentElement.remove()">Xanh lá</div>
            <div class="color-option solid" style="background: #2563eb" onclick="changeButtonTextColor('${buttonId}', '#2563eb'); this.parentElement.parentElement.remove()">Xanh dương</div>
            <div class="color-option solid" style="background: #7c3aed" onclick="changeButtonTextColor('${buttonId}', '#7c3aed'); this.parentElement.parentElement.remove()">Tím</div>
            <div class="color-option solid" style="background: #ea580c" onclick="changeButtonTextColor('${buttonId}', '#ea580c'); this.parentElement.parentElement.remove()">Cam</div>
        </div>
    `;

    const editorRect = document.getElementById('buttonEditor')?.getBoundingClientRect();
    if (editorRect) {
        colorMenu.style.position = 'fixed';
        colorMenu.style.left = editorRect.left + 'px';
        colorMenu.style.top = (editorRect.top - 100) + 'px';
        colorMenu.style.zIndex = '10002';
        document.body.appendChild(colorMenu);
    }
}

function showCodeToolbar(codeEl) {
    // Remove any existing toolbar
    const existingToolbar = document.getElementById('codeToolbar');
    if (existingToolbar) existingToolbar.remove();

    const codeToolbar = document.createElement('div');
    codeToolbar.id = 'codeToolbar';
    codeToolbar.className = 'code-toolbar';

    const rect = codeEl.getBoundingClientRect();
    codeToolbar.style.left = rect.left + 'px';
    codeToolbar.style.top = (rect.top + rect.height + 10) + 'px';

    const codeId = codeEl.id;

    codeToolbar.innerHTML = `
        <button class="code-toolbar-btn" id="btnDeleteCode" data-code-id="${codeId}">🗑️ Xóa code</button>
    `;

    document.body.appendChild(codeToolbar);

    // Add click handler separately to avoid issues with onclick string
    document.getElementById('btnDeleteCode').addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const id = this.dataset.codeId;
        const el = document.getElementById(id);
        if (el) {
            const text = el.textContent;
            const textNode = document.createTextNode(text);
            el.parentNode.replaceChild(textNode, el);

            const selection = window.getSelection();
            const range = document.createRange();
            range.setStart(textNode, text.length);
            range.collapse(true);
            selection.removeAllRanges();
            selection.addRange(range);

            showToast('Đã xóa code format');
        }
        codeToolbar.remove();
    });

    // Auto hide after 3 seconds
    setTimeout(() => {
        if (codeToolbar.parentNode) {
            codeToolbar.remove();
        }
    }, 3000);
}

// ==========================================
// 2. BLOCK MANAGEMENT
// ==========================================
function addBlock(type, focus = false, index = -1, initialHTML = '') {
    const editor = document.getElementById('notionEditor');
    const id = 'block-' + Date.now() + Math.floor(Math.random() * 1000);

    const block = document.createElement('div');
    block.className = 'notion-block';
    block.id = id;
    block.dataset.type = type;

    let content = '';
    const placeholderMap = {
        'paragraph': "Nhập nội dung...",
        'h1': "Tiêu đề 1...",
        'h2': "Tiêu đề 2...",
        'h3': "Tiêu đề 3...",
        'ul': "Danh sách...",
        'ol': "Danh sách...",
        'blockquote': "Trích dẫn...",
        'callout': "Thông báo...",
        'code': "Code here...",
        'divider': ""
    };

    switch (type) {
        case 'h1': case 'h2': case 'h3':
            content = `<${type} class="notion-block-content" contenteditable="true" data-type="${type}" data-placeholder="${placeholderMap[type]}">${initialHTML}</${type}>`;
            break;
        case 'ul': case 'ol':
            const listTag = type === 'ul' ? 'ul' : 'ol';
            content = `<${listTag} class="notion-block-content pl-6" contenteditable="true" data-type="${type}" data-placeholder="${placeholderMap[type]}"><li>${initialHTML || ''}</li></${listTag}>`;
            break;
        case 'blockquote':
            content = `<blockquote class="notion-block-content" contenteditable="true" data-type="${type}" data-placeholder="${placeholderMap[type]}">${initialHTML}</blockquote>`;
            break;
        case 'callout':
            content = `<div class="notion-block-content callout" contenteditable="true" data-type="${type}" data-placeholder="${placeholderMap[type]}"><span class="text-2xl mr-2" contenteditable="false">💡</span><span contenteditable="true" class="flex-1">${initialHTML}</span></div>`;
            break;
        case 'code':
            content = `<pre class="notion-block-content" contenteditable="true" data-type="${type}" data-placeholder="${placeholderMap[type]}">${initialHTML}</pre>`;
            break;
        case 'divider':
            content = `<hr class="notion-block-content" data-type="${type}">`;
            break;
        case 'image':
            const src = (initialHTML && (initialHTML.startsWith('http') || initialHTML.startsWith('data:'))) ? initialHTML : '';
            content = `<div class="image-block-wrapper"><img src="${src}" alt="Image" class="image-block-preview" id="img-${id}"><div class="image-block-remove" onclick="removeBlock('${id}')"><i data-lucide="x" class="w-4 h-4"></i></div></div>`;
            break;
        default:
            // Use div instead of p to avoid browser HTML parsing issues with nested elements
            content = `<div class="notion-block-content" contenteditable="true" data-type="paragraph" data-placeholder="${placeholderMap['paragraph']}">${initialHTML}</div>`;
    }

    block.innerHTML = `
        <div class="block-controls" contenteditable="false">
            <div class="block-add-btn" onclick="showBlockMenuFor('${id}')" title="Thêm block">
                <i data-lucide="plus" class="w-3.5 h-3.5"></i>
            </div>
            <div class="block-actions-btn" onclick="showBlockActions(event, '${id}')" title="Tùy chọn">
                <i data-lucide="more-horizontal" class="w-3.5 h-3.5"></i>
            </div>
        </div>
        ${content}
    `;

    if (index >= 0) {
        if (index < editor.children.length) editor.insertBefore(block, editor.children[index]);
        else editor.appendChild(block);
    } else {
        editor.appendChild(block);
    }

    hideBlockSelector();

    if (window.lucide) lucide.createIcons();

    if (focus) {
        const contentEl = block.querySelector('.notion-block-content');
        if (contentEl) {
            setTimeout(() => contentEl.focus(), 0);
        }
    }
}

function removeBlock(blockId) {
    const block = document.getElementById(blockId);
    if (!block) return;
    const editor = document.getElementById('notionEditor');
    if (editor.children.length <= 1) {
        block.querySelector('.notion-block-content').innerHTML = '';
        return;
    }
    block.remove();
}

function moveBlockById(blockId, direction) {
    const block = document.getElementById(blockId);
    if (!block) return;
    const editor = document.getElementById('notionEditor');
    const blocks = Array.from(editor.children);
    const index = blocks.indexOf(block);
    const newIndex = index + direction;
    if (newIndex >= 0 && newIndex < blocks.length) {
        const target = blocks[newIndex];
        direction === -1 ? target.before(block) : target.after(block);
    }
}

// ==========================================
// 3. KEYBOARD SHORTCUTS
// ==========================================
function initKeyboardShortcuts() {
    const editor = document.getElementById('notionEditor');

    editor.addEventListener('keydown', (e) => {
        const activeBlock = document.activeElement.closest('.notion-block');
        if (!activeBlock) return;

        const index = Array.from(editor.children).indexOf(activeBlock);

        // ENTER = Line break within current block
        if (e.key === 'Enter' && !e.shiftKey) {
            if (document.getElementById('blockTypeSelector').classList.contains('active')) return;
            e.preventDefault();
            document.execCommand('insertLineBreak', false, null);
            return;
        }

        // SHIFT + ENTER = Create new block
        if (e.key === 'Enter' && e.shiftKey) {
            e.preventDefault();
            const currentType = activeBlock.dataset.type;
            if (currentType === 'ul' || currentType === 'ol') {
                addBlock(currentType, true, index + 1);
            } else {
                addBlock('paragraph', true, index + 1);
            }
            return;
        }

        // SHIFT + ENTER = Create new block
        if (e.key === 'Enter' && e.shiftKey) {
            e.preventDefault();
            const currentType = activeBlock.dataset.type;
            if (currentType === 'ul' || currentType === 'ol') {
                addBlock(currentType, true, index + 1);
            } else {
                addBlock('paragraph', true, index + 1);
            }
            return;
        }

        if (e.key === '/' && document.activeElement.textContent === '') {
            showBlockSelector(activeBlock);
        }

        if (e.key === 'Backspace' && document.activeElement.textContent === '') {
            if (editor.children.length > 1) {
                e.preventDefault();
                removeBlock(activeBlock.id);
                const prev = editor.children[Math.max(0, index - 1)];
                if (prev) prev.querySelector('.notion-block-content')?.focus();
            }
        }
    });
}

// ==========================================
// 4. FLOATING TOOLBAR
// ==========================================
function initTextToolbar() {
    textToolbar = document.getElementById('textToolbar');
    document.addEventListener('selectionchange', updateToolbarPosition);

    if (textToolbar) {
        textToolbar.addEventListener('mousedown', (e) => {
            e.preventDefault();
        });
    }
}

function updateToolbarPosition() {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
        if (textToolbar) textToolbar.classList.remove('active');
        document.querySelectorAll('.toolbar-dropdown-menu').forEach(el => el.classList.add('hidden'));
        return;
    }

    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    const editor = document.getElementById('notionEditor');
    const titleEl = document.getElementById('postTitle');

    if (!editor || (!editor.contains(selection.anchorNode) && (!titleEl || !titleEl.contains(selection.anchorNode)))) {
        if (textToolbar) textToolbar.classList.remove('active');
        return;
    }

    if (textToolbar) {
        textToolbar.style.left = (rect.left + rect.width / 2 - textToolbar.offsetWidth / 2) + 'px';
        textToolbar.style.top = (rect.top - textToolbar.offsetHeight - 10) + 'px';
        textToolbar.classList.add('active');
    }
}

// ==========================================
// 5. FORMAT TEXT
// ==========================================
function formatText(command, value = null) {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) return;

    // CODE FORMAT - Make editable nested block
    if (command === 'code') {
        const selectedText = selection.toString();
        if (!selectedText) {
            showToast('Vui lòng bôi đen văn bản!');
            return;
        }

        // Check if already in code
        if (selection.rangeCount > 0) {
            const range = selection.getRangeAt(0);
            const container = range.startContainer.nodeType === 3 ? range.startContainer.parentNode : range.startContainer;
            const codeSpan = container.closest('.inline-code');

            if (codeSpan) {
                const textNode = document.createTextNode(codeSpan.textContent);
                codeSpan.parentNode.replaceChild(textNode, codeSpan);
                const newRange = document.createRange();
                newRange.setStart(textNode, textNode.textContent.length);
                newRange.collapse(true);
                selection.removeAllRanges();
                selection.addRange(newRange);
                showToast('Đã tắt định dạng code');
                return;
            }
        }

        // Create editable code block
        const codeId = 'code-' + Date.now();
        const codeHTML = `<span id="${codeId}" class="inline-code" contenteditable="true" style="background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-family: monospace; color: #dc2626;" title="Click để edit, Shift+Enter hoặc mũi tên để thoát">${selectedText}</span>`;

        document.execCommand('insertHTML', false, codeHTML);

        setTimeout(() => {
            const codeEl = document.getElementById(codeId);
            if (codeEl) {
                codeEl.focus();
                const range = document.createRange();
                range.selectNodeContents(codeEl);
                range.collapse(false);
                selection.removeAllRanges();
                selection.addRange(range);
            }
        }, 10);

        showToast('Đã thêm code block');
        return;
    }

    // BUTTON LINK
    if (command === 'buttonLink') {
        if (selection.isCollapsed || !selection.toString()) {
            showToast('Vui lòng bôi đen văn bản!');
            return;
        }

        const url = prompt('Nhập URL:', 'https://');
        if (!url || url.trim() === '' || url === 'https://') return;

        const btnText = selection.toString();
        const btnId = 'btn-' + Date.now();

        const btnHTML = `<span id="${btnId}" class="inline-button" contenteditable="true" data-url="${url}" data-background="${buttonSettings.background}" data-text-color="${buttonSettings.textColor}" data-padding="${buttonSettings.padding}" data-font-size="${buttonSettings.fontSize}" data-border-radius="${buttonSettings.borderRadius}" style="display: inline-block; background: ${buttonSettings.background}; color: ${buttonSettings.textColor}; padding: ${buttonSettings.padding}; border-radius: ${buttonSettings.borderRadius}; font-size: ${buttonSettings.fontSize}; font-weight: 600;" title="Click để edit, Shift+Enter hoặc mũi tên để thoát">${btnText}</span>`;

        document.execCommand('insertHTML', false, btnHTML);

        setTimeout(() => {
            const btnEl = document.getElementById(btnId);
            if (btnEl) {
                btnEl.focus();
                const range = document.createRange();
                range.selectNodeContents(btnEl);
                range.collapse(false);
                selection.removeAllRanges();
                selection.addRange(range);
            }
        }, 10);

        showToast('Đã thêm nút');
        return;
    }

    // LINK
    if (command === 'createLink') {
        const url = prompt('Nhập đường dẫn URL:', 'https://');
        if (url) document.execCommand(command, false, url);
    } else {
        document.execCommand(command, false, value);
    }

    const newSelection = window.getSelection();
    if (newSelection && newSelection.rangeCount > 0) {
        newSelection.getRangeAt(0).startContainer.parentNode?.focus();
    }
}

function insertOrEditLink() {
    formatText('createLink');
}

// ==========================================
// 6. SETTINGS & DROPDOWNS
// ==========================================
function toggleSettings() {
    const modal = document.getElementById('settingsModal');
    const panel = document.getElementById('settingsPanel');
    if (!modal || !panel) return;

    const isActive = modal.classList.contains('active');

    if (isActive) {
        modal.classList.remove('active');
        setTimeout(() => { modal.style.display = 'none'; }, 300);
    } else {
        modal.style.display = 'flex';
        void modal.offsetWidth;
        modal.classList.add('active');
        if (window.lucide) lucide.createIcons();
    }
}

function setBlockType(type) {
    const selection = window.getSelection();
    if (!selection.rangeCount) return;
    const node = selection.anchorNode;
    const block = (node.nodeType === 3 ? node.parentNode : node).closest('.notion-block');
    if (!block) return;

    const id = block.id;
    const index = Array.from(block.parentNode.children).indexOf(block);

    removeBlock(id);
    addBlock(type, true, index);
}

function toggleDropdown(id) {
    document.querySelectorAll('.toolbar-dropdown-menu').forEach(e => {
        if (e.id !== id) e.classList.remove('active');
    });
    const el = document.getElementById(id);
    if (el) el.classList.toggle('active');
}

function setColor(type, color) {
    if (color === 'custom') {
        const customColor = prompt('Nhập mã màu:', '#000000');
        if (customColor) formatText(type, customColor);
        return;
    }
    formatText(type, color);
    document.querySelectorAll('.toolbar-dropdown-menu').forEach(el => {
        el.classList.remove('active');
        el.classList.add('hidden');
    });
}

// ==========================================
// 7. SLASH MENU
// ==========================================
const SLASH_MENU_ITEMS = [
    {
        title: 'Cơ bản',
        items: [
            { type: 'paragraph', label: 'Văn bản', icon: 'type', desc: 'Viết văn bản.' },
            { type: 'h1', label: 'Tiêu đề 1', icon: 'heading-1', desc: 'Tiêu đề lớn.' },
            { type: 'h2', label: 'Tiêu đề 2', icon: 'heading-2', desc: 'Tiêu đề vừa.' },
            { type: 'h3', label: 'Tiêu đề 3', icon: 'heading-3', desc: 'Tiêu đề nhỏ.' },
            { type: 'ul', label: 'Danh sách', icon: 'list', desc: 'Danh sách.' },
            { type: 'ol', label: 'Danh sách số', icon: 'list-ordered', desc: 'Danh sách số.' },
            { type: 'blockquote', label: 'Trích dẫn', icon: 'quote', desc: 'Trích dẫn.' },
            { type: 'divider', label: 'Phân cách', icon: 'minus', desc: 'Đường kẻ.' },
            { type: 'callout', label: 'Lưu ý', icon: 'info', desc: 'Khung lưu ý.' },
        ]
    },
    {
        title: 'Đa phương tiện',
        items: [
            { type: 'image', label: 'Hình ảnh', icon: 'image', desc: 'Tải ảnh.' },
        ]
    },
    {
        title: 'Nâng cao',
        items: [
            { type: 'code', label: 'Code block', icon: 'code', desc: 'Chèn code.' },
        ]
    }
];

function createSlashMenu() {
    const menu = document.createElement('div');
    menu.id = 'slashMenu';
    menu.className = 'fixed z-50 bg-white shadow-xl rounded-lg border border-gray-200 w-80 max-h-96 overflow-y-auto py-2';
    menu.style.display = 'none';

    SLASH_MENU_ITEMS.forEach(section => {
        const title = document.createElement('div');
        title.className = 'px-3 py-1.5 text-xs font-semibold text-gray-500 uppercase select-none';
        title.textContent = section.title;
        menu.appendChild(title);

        section.items.forEach(item => {
            const el = document.createElement('div');
            el.className = 'flex items-center gap-3 px-3 py-2 mx-1 hover:bg-gray-100 rounded cursor-pointer';
            el.innerHTML = `
                <div class="w-10 h-10 flex items-center justify-center bg-white border border-gray-200 rounded">
                    <i data-lucide="${item.icon}" class="w-5 h-5"></i>
                </div>
                <div>
                    <div class="text-sm font-medium">${item.label}</div>
                    <div class="text-xs text-gray-400">${item.desc}</div>
                </div>
            `;
            el.onclick = (e) => {
                e.stopPropagation();
                applyBlockType(item.type);
                hideSlashMenu();
            };
            menu.appendChild(el);
        });
    });

    document.body.appendChild(menu);
    return menu;
}

function showBlockSelector(block) {
    let menu = document.getElementById('slashMenu');
    if (!menu) {
        menu = createSlashMenu();
        if (window.lucide) lucide.createIcons();
    }

    const rect = block.getBoundingClientRect();
    const menuHeight = 350;
    const top = (rect.bottom + menuHeight > window.innerHeight) ? (rect.top - menuHeight) : (rect.bottom + 5);

    menu.style.top = top + 'px';
    menu.style.left = rect.left + 'px';
    menu.classList.remove('hidden');
    menu.classList.add('block');
    currentBlockForSelector = block;
}

function hideSlashMenu() {
    const menu = document.getElementById('slashMenu');
    if (menu) {
        menu.classList.add('hidden');
        menu.classList.remove('block');
    }
    currentBlockForSelector = null;
}

function hideBlockSelector() {
    hideSlashMenu();
}

function showBlockMenuFor(blockId) {
    const block = document.getElementById(blockId);
    if (block) showBlockSelector(block);
}

function applyBlockType(type) {
    if (!currentBlockForSelector) return;
    const block = currentBlockForSelector;
    const editor = document.getElementById('notionEditor');
    const index = Array.from(editor.children).indexOf(block);

    removeBlock(block.id);
    addBlock(type, true, index);

    if (type === 'image') {
        setTimeout(() => {
            const uploadInput = document.getElementById('imageUpload');
            if (uploadInput) uploadInput.click();
        }, 100);
    }
}

// ==========================================
// 8. ALIGNMENT
// ==========================================
function setAlignment(align, targetBlock = null) {
    const selection = window.getSelection();

    // If there's a text selection, apply inline alignment to just the selection
    if (selection.rangeCount > 0 && !selection.isCollapsed) {
        const range = selection.getRangeAt(0);
        const selectedText = range.toString().trim();

        // Only apply inline alignment if there's actual selected text
        if (selectedText.length > 0) {
            console.log('Applying inline alignment to selected text:', align);

            // Create a div with inline alignment (not span, to avoid p>div issues)
            const div = document.createElement('div');
            div.style.textAlign = align;
            div.style.display = 'inline-block';
            div.style.width = '100%';
            div.className = 'inline-alignment';
            div.contentEditable = 'true';

            // Extract and wrap the selected content
            try {
                const extractedContent = range.extractContents();
                div.appendChild(extractedContent);
                range.insertNode(div);

                // Clear selection and place cursor after the div
                selection.removeAllRanges();
                const newRange = document.createRange();
                newRange.setStartAfter(div);
                newRange.collapse(true);
                selection.addRange(newRange);

                console.log('Inline alignment applied successfully');
                return;
            } catch (e) {
                console.error('Error applying inline alignment:', e);
            }
        }
    }

    // If no selection or inline failed, apply to entire block (original behavior)
    let block = targetBlock;

    if (!block && selection.rangeCount > 0) {
        const node = selection.anchorNode;
        block = (node.nodeType === 3 ? node.parentNode : node).closest('.notion-block');
    }
    if (!block) return;

    const imgWrapper = block.querySelector('.image-block-wrapper');
    if (imgWrapper) {
        imgWrapper.classList.remove('text-left', 'text-center', 'text-right');
        imgWrapper.classList.add(`text-${align}`);
        return;
    }

    const content = block.querySelector('.notion-block-content');
    if (content) {
        // Check if content already has inline alignment elements
        const existingInlineAlign = content.querySelector('.inline-alignment');
        if (existingInlineAlign) {
            // Update existing inline alignment instead of applying block-level
            console.log('Updating existing inline alignment to:', align);
            existingInlineAlign.style.textAlign = align;
            // Update the style attribute to ensure it's preserved
            existingInlineAlign.setAttribute('style', `text-align: ${align}; display: inline-block; width: 100%;`);
            return;
        }

        // No inline alignment, apply to entire block
        content.classList.remove('text-left', 'text-center', 'text-right');
        content.classList.add(`text-${align}`);
        content.style.textAlign = align;
    }
}
window.setAlignment = setAlignment;

// ==========================================
// 9. BLOCK ACTIONS
// ==========================================
function showBlockActions(event, blockId) {
    event.stopPropagation();

    if (!blockActionsMenu) {
        blockActionsMenu = document.createElement('div');
        blockActionsMenu.id = 'blockActionsMenu';
        blockActionsMenu.className = 'block-menu';
        document.body.appendChild(blockActionsMenu);
    }

    const rect = event.target.getBoundingClientRect();
    blockActionsMenu.style.left = rect.left + 'px';
    blockActionsMenu.style.top = (rect.bottom + 5) + 'px';

    blockActionsMenu.innerHTML = `
        <div class="block-menu-item" onclick="duplicateBlock('${blockId}')">
            <i data-lucide="copy" class="w-4 h-4"></i> <span>Nhân bản</span>
        </div>
        <div class="block-menu-item" onclick="removeBlock('${blockId}')">
            <i data-lucide="trash-2" class="w-4 h-4 text-red-500"></i> <span class="text-red-500">Xóa</span>
        </div>
    `;

    blockActionsMenu.classList.add('active');
    if (window.lucide) lucide.createIcons();
}

function hideBlockActionsMenu() {
    if (blockActionsMenu) blockActionsMenu.classList.remove('active');
}

function duplicateBlock(blockId) {
    const block = document.getElementById(blockId);
    if (block) {
        const clone = block.cloneNode(true);
        clone.id = 'block-' + Date.now();
        clone.querySelector('.block-add-btn').onclick = () => showBlockMenuFor(clone.id);
        clone.querySelector('.block-actions-btn').onclick = (e) => showBlockActions(e, clone.id);
        block.after(clone);
    }
    hideBlockActionsMenu();
}

// ==========================================
// 10. TITLE & SLUG
// ==========================================
function updateSlug() {
    const titleEl = document.getElementById('postTitle');
    const slugEl = document.getElementById('slug');
    if (!titleEl || !slugEl) return;

    const title = titleEl.tagName === 'INPUT' ? titleEl.value : titleEl.innerText;
    const slug = title.toLowerCase()
        .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
        .replace(/[đĐ]/g, 'd')
        .replace(/[^a-z0-9\s-]/g, '')
        .replace(/\s+/g, '-')
        .replace(/^-+|-+$/g, '');

    slugEl.value = slug;
}

// ==========================================
// 12. AUTO SAVE
// ==========================================
let autoSaveTimer = null;
function autoSaveDraft() {
    clearTimeout(autoSaveTimer);
    autoSaveTimer = setTimeout(() => {
        const titleEl = document.getElementById('postTitle');
        const editor = document.getElementById('notionEditor');
        if (!titleEl || !editor) return;

        const title = titleEl.tagName === 'INPUT' ? titleEl.value : titleEl.innerText;
        const content = editor.innerHTML;

        const params = new URLSearchParams(window.location.search);
        const id = params.get('id') || 'new';
        localStorage.setItem('draft_post_' + id, JSON.stringify({
            title,
            content,
            lastSaved: Date.now()
        }));

        const saveStatus = document.getElementById('saveStatus');
        if (saveStatus) {
            saveStatus.textContent = 'Đã lưu nháp ' + new Date().toLocaleTimeString();
            saveStatus.classList.add('text-green-600');
            setTimeout(() => saveStatus.classList.remove('text-green-600'), 1000);
        }
    }, 1000);
}
window.autoSaveDraft = autoSaveDraft;

// ==========================================
// 12b. SAVE ON PAGE CLOSE (beforeunload)
// ==========================================
window.addEventListener('beforeunload', function(e) {
    // Force save draft before page closes
    const titleEl = document.getElementById('postTitle');
    const editor = document.getElementById('notionEditor');
    if (titleEl && editor) {
        const title = titleEl.tagName === 'INPUT' ? titleEl.value : titleEl.innerText;
        const content = editor.innerHTML;

        const params = new URLSearchParams(window.location.search);
        const id = params.get('id') || 'new';
        localStorage.setItem('draft_post_' + id, JSON.stringify({
            title,
            content,
            lastSaved: Date.now()
        }));
    }
});

// ==========================================
// 13. LINK HOVER TOOLTIP
// ==========================================
document.addEventListener('mouseover', function(e) {
    if (e.target.tagName === 'A') {
        e.target.title = e.target.href || '';
    }
});
