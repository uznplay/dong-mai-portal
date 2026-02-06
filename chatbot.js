function toggleChat() {
    const drawer = document.getElementById('chat-drawer');
    const iconClose = document.getElementById('chat-icon-close');
    const chatHint = document.getElementById('chat-hint');

    if (drawer.classList.contains('hidden')) {
        // OPEN CHAT
        drawer.classList.remove('hidden');
        iconClose.classList.remove('hidden');
        iconClose.classList.remove('opacity-0');

        // Hide hint when chat is open
        if (chatHint) chatHint.style.display = 'none';

        // Auto focus input
        setTimeout(() => document.getElementById('chat-input')?.focus(), 100);
    } else {
        // CLOSE CHAT
        drawer.classList.add('hidden');
        iconClose.classList.add('hidden');
        iconClose.classList.add('opacity-0');
    }
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const sendBtn = document.querySelector('button[onclick="sendMessage()"]');
    const message = input.value.trim();

    if (!message || input.disabled) return;

    // Set waiting state
    const setBusy = (isBusy) => {
        const resetBtn = document.getElementById('chat-reset');
        input.disabled = isBusy;
        if (sendBtn) sendBtn.disabled = isBusy;
        if (resetBtn) resetBtn.disabled = isBusy;

        if (isBusy) {
            localStorage.setItem('chat_is_waiting', Date.now());
        } else {
            localStorage.removeItem('chat_is_waiting');
        }
    };

    setBusy(true);

    const chatMessages = document.getElementById('chat-messages');

    // Add user message
    const userDiv = document.createElement('div');
    userDiv.className = 'bg-gray-200 p-3 rounded-2xl rounded-tr-none text-sm text-gray-800 max-w-[85%] self-end ml-auto';
    userDiv.textContent = message;
    chatMessages.appendChild(userDiv);

    input.value = '';
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Add loading message
    const botDiv = document.createElement('div');
    botDiv.className = 'bg-red-50 p-3 rounded-2xl rounded-tl-none text-sm text-gray-800 max-w-[85%] self-start whitespace-pre-wrap leading-relaxed';
    botDiv.innerHTML = '<span class="animate-pulse">Đang tra cứu thông tin...</span>';
    chatMessages.appendChild(botDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Retrieve or Generate Session ID - PERSISTENT
    let sessionId = localStorage.getItem('chatSessionId');
    if (!sessionId) {
        sessionId = Math.random().toString(36).substring(2) + Date.now().toString(36);
        localStorage.setItem('chatSessionId', sessionId);
    }

    // Retrieve previous context
    const lastContext = localStorage.getItem('chat_last_context') || "";

    // Parse Markdown-like formatting (Robust Placeholder Strategy)
    function formatMessage(text) {
        // 1. Escape HTML
        let html = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        // 2. Extract Markdown Links [Title](URL) and hide them -> SAFE_LINK_0
        const links = [];
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, title, url) => {
            const placeholder = `__SAFE_LINK_${links.length}__`;
            links.push({ placeholder, title, url });
            return placeholder;
        });

        // 3. Auto-link remaining bare URLs (only those NOT inside markdown links)
        html = html.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" class="text-blue-600 underline break-all hover:text-blue-800">$1</a>');

        // 4. Restore Markdown Links as proper HTML
        links.forEach(link => {
            const anchor = `<a href="${link.url}" target="_blank" class="text-blue-600 underline break-all hover:text-blue-800">${link.title}</a>`;
            html = html.replace(link.placeholder, anchor);
        });

        // 5. Format Bold: **text** -> <b>$1</b>
        html = html.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');

        // 6. Lists: - item -> • item
        html = html.replace(/^\s*-\s/gm, '• ');

        return html;
    }

    // --- SECURITY UTILS ---
    const SECRET_KEY = "DM_Portal_2026_Secure";

    function obfuscate(text) {
        const xor = text.split('').map(c => String.fromCharCode(c.charCodeAt(0) ^ 5)).join('');
        return btoa(unescape(encodeURIComponent(xor)));
    }

    async function generateSignature(payload, ts) {
        const msgUint8 = new TextEncoder().encode(ts + payload + SECRET_KEY);
        const hashBuffer = await crypto.subtle.digest('SHA-256', msgUint8);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }

    try {
        const timestamp = Math.floor(Date.now() / 1000).toString();
        const obfuscatedPayload = obfuscate(message);
        const obfuscatedContext = lastContext ? obfuscate(lastContext) : "";
        const obfuscatedSession = obfuscate(sessionId);

        // Compute signature on the main payload + timestamp
        const signature = await generateSignature(obfuscatedPayload, timestamp);

        const response = await fetch('/api/chatbot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                p: obfuscatedPayload,    // message
                t: timestamp,            // timestamp
                s: signature,            // signature
                sid: obfuscatedSession,  // session_id
                c: obfuscatedContext     // context
            })
        });

        if (response.status === 429) {
            const errorData = await response.json();
            botDiv.innerHTML = `<span class="text-red-500">${errorData.answer}</span>`;
            setBusy(false);
            return;
        }

        const data = await response.json();

        // Update bot message with Formatting
        botDiv.innerHTML = formatMessage(data.answer);
        botDiv.classList.add('break-words');

        // Store context for next time if it was returned
        if (data.context) {
            localStorage.setItem('chat_last_context', data.context);
        }

        // Add sources if any
        if (data.sources && data.sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'text-[10px] text-gray-400 mt-2 italic';
            sourcesDiv.innerHTML = 'Nguồn tham khảo: ' + data.sources.map(s => `<a href="${s}" target="_blank" class="underline hover:text-red-primary mb-1 block">${s}</a>`).join('');
            botDiv.appendChild(sourcesDiv);
        }

    } catch (error) {
        botDiv.textContent = 'Hiện tại hệ thống AI đang quá tải và không phản hồi kịp (Timeout). Vui lòng thử lại sau ít phút.';
        console.error('Chat error:', error);
    } finally {
        setBusy(false);
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function resetChat() {
    localStorage.removeItem('chatSessionId');
    localStorage.removeItem('chat_last_context');
    localStorage.removeItem('chat_is_waiting');
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = `
        <div class="bg-red-50 p-3 rounded-2xl rounded-tl-none text-sm text-gray-800 max-w-[85%] self-start">
          Xin chào! Tôi có thể giúp gì cho bạn về các thủ tục hành chính tại phường Đông Mai?
        </div>`;
    // Generate new session ID immediately
    const sessionId = Math.random().toString(36).substring(2) + Date.now().toString(36);
    localStorage.setItem('chatSessionId', sessionId);
}

// Handle Enter key
document.getElementById('chat-input')?.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
// Initialize
document.addEventListener('DOMContentLoaded', function () {
    // Check if we were waiting for a response before reload
    const lastWaiting = localStorage.getItem('chat_is_waiting');
    if (lastWaiting) {
        const diff = Date.now() - parseInt(lastWaiting);
        if (diff < 60000) { // If less than 60s, keep disabled
            const input = document.getElementById('chat-input');
            const sendBtn = document.querySelector('button[onclick="sendMessage()"]');
            const resetBtn = document.getElementById('chat-reset');

            if (input) input.disabled = true;
            if (sendBtn) sendBtn.disabled = true;
            if (resetBtn) resetBtn.disabled = true;

            // Show a waiting message
            const chatMessages = document.getElementById('chat-messages');
            const botDiv = document.createElement('div');
            botDiv.className = 'bg-red-50 p-3 rounded-2xl rounded-tl-none text-sm text-gray-800 max-w-[85%] self-start italic';
            botDiv.textContent = 'Hệ thống đang xử lý câu hỏi trước đó của bạn... (Nếu quá lâu, hãy F5 lại sau 1 phút)';
            chatMessages.appendChild(botDiv);

            // Clear after remaining time
            setTimeout(() => {
                if (input) input.disabled = false;
                if (sendBtn) sendBtn.disabled = false;
                if (resetBtn) resetBtn.disabled = false;
                localStorage.removeItem('chat_is_waiting');
            }, 60000 - diff);
        } else {
            localStorage.removeItem('chat_is_waiting');
        }
    }

    // Reuse or create Session ID
    let sessionId = localStorage.getItem('chatSessionId');
    if (!sessionId) {
        sessionId = Math.random().toString(36).substring(2) + Date.now().toString(36);
        localStorage.setItem('chatSessionId', sessionId);
    }
    console.log("Chat Session ID:", sessionId);

    // Auto-focus input
    document.getElementById('chat-input')?.focus();
});