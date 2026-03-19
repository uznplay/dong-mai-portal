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

    // Set waiting state (with storage error handling)
    const setBusy = (isBusy) => {
        const resetBtn = document.getElementById('chat-reset');
        input.disabled = isBusy;
        if (sendBtn) sendBtn.disabled = isBusy;
        if (resetBtn) resetBtn.disabled = isBusy;

        try {
            if (isBusy) {
                localStorage.setItem('chat_is_waiting', Date.now());
            } else {
                localStorage.removeItem('chat_is_waiting');
            }
        } catch (e) {
            // Storage blocked - continue without storing state
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

    const isCryptoAvailable = typeof crypto !== 'undefined' && typeof crypto.subtle !== 'undefined';

    // Correct SHA-256 implementation for fallback
    async function sha256(message) {
        if (isCryptoAvailable) {
            try {
                const msgUint8 = new TextEncoder().encode(message);
                const hashBuffer = await crypto.subtle.digest('SHA-256', msgUint8);
                return Array.from(new Uint8Array(hashBuffer)).map(b => b.toString(16).padStart(2, '0')).join('');
            } catch (e) {}
        }

        const utf8 = new TextEncoder().encode(message);
        const len = utf8.length;
        const nBlocks = ((len + 8) >> 6) + 1;
        const words = new Uint32Array(nBlocks * 16);
        for (let i = 0; i < len; i++) words[i >> 2] |= utf8[i] << (24 - (i % 4) * 8);
        words[len >> 2] |= 0x80 << (24 - (len % 4) * 8);
        words[nBlocks * 16 - 1] = len * 8;

        const h = new Uint32Array([0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]);
        const k = new Uint32Array([
            0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
            0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
            0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
            0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
            0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
            0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
            0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
            0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
        ]);
        const rot = (n, s) => (n >>> s) | (n << (32 - s));
        const w = new Uint32Array(64);

        for (let i = 0; i < nBlocks; i++) {
            for (let j = 0; j < 16; j++) w[j] = words[i * 16 + j];
            for (let j = 16; j < 64; j++) {
                const s0 = rot(w[j - 15], 7) ^ rot(w[j - 15], 18) ^ (w[j - 15] >>> 3);
                const s1 = rot(w[j - 2], 17) ^ rot(w[j - 2], 19) ^ (w[j - 2] >>> 10);
                w[j] = (w[j - 16] + s0 + w[j - 7] + s1) | 0;
            }
            let [a, b, c, d, e, f, g, h8] = [h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7]];
            for (let j = 0; j < 64; j++) {
                const t1 = (h8 + (rot(e, 6) ^ rot(e, 11) ^ rot(e, 25)) + ((e & f) ^ (~e & g)) + k[j] + w[j]) | 0;
                const t2 = ((rot(a, 2) ^ rot(a, 13) ^ rot(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) | 0;
                [a, b, c, d, e, f, g, h8] = [(t1 + t2) | 0, a, b, c, (d + t1) | 0, e, f, g];
            }
            h[0] = (h[0] + a)|0; h[1] = (h[1] + b)|0; h[2] = (h[2] + c)|0; h[3] = (h[3] + d)|0;
            h[4] = (h[4] + e)|0; h[5] = (h[5] + f)|0; h[6] = (h[6] + g)|0; h[7] = (h[7] + h8)|0;
        }
        return Array.from(h).map(v => (v >>> 0).toString(16).padStart(8, '0')).join('');
    }



    function obfuscate(text) {
        const xor = text.split('').map(c => String.fromCharCode(c.charCodeAt(0) ^ 5)).join('');
        return btoa(unescape(encodeURIComponent(xor)));
    }

    async function generateSignature(payload, ts) {
        // Use SHA-256 for signature (works with or without crypto.subtle)
        return await sha256(ts + payload + SECRET_KEY);
    }

    try {
        // Check if localStorage is available
        let sessionId;
        try {
            sessionId = localStorage.getItem('chatSessionId');
            if (!sessionId) {
                sessionId = Math.random().toString(36).substring(2) + Date.now().toString(36);
                localStorage.setItem('chatSessionId', sessionId);
            }
        } catch (storageError) {
            // Fallback: generate random session ID per message
            sessionId = Math.random().toString(36).substring(2) + Date.now().toString(36);
        }

        // Retrieve previous context (with error handling)
        let lastContext = "";
        try {
            lastContext = localStorage.getItem('chat_last_context') || "";
        } catch (e) {
            // Storage blocked, use empty context
        }

        // Prepare payload and signature
        const timestamp = Math.floor(Date.now() / 1000).toString();
        const obfuscatedPayload = obfuscate(message);
        const obfuscatedContext = lastContext ? obfuscate(lastContext) : "";
        const obfuscatedSession = obfuscate(sessionId);
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

        if (!response.ok) {
            // Handle error responses (403, 500, etc.)
            let errorMessage = 'Lỗi hệ thống, vui lòng thử lại sau.';
            try {
                const errorData = await response.json();
                errorMessage = errorData.answer || errorData.error || errorMessage;
            } catch (e) {
                // Response is not JSON, use status text
                if (response.status === 403) {
                    errorMessage = 'Từ chối truy cập. Vui lòng thử F5 trang hoặc đợi một chút rồi thử lại.';
                } else if (response.status === 500) {
                    errorMessage = 'Lỗi server. Vui lòng thử lại sau.';
                }
            }
            botDiv.innerHTML = `<span class="text-red-500">${errorMessage}</span>`;
            setBusy(false);
            return;
        }

        const data = await response.json();

        // Update bot message with Formatting
        botDiv.innerHTML = formatMessage(data.answer);
        botDiv.classList.add('break-words');

        // Store context for next time if it was returned
        if (data.context) {
            try {
                localStorage.setItem('chat_last_context', data.context);
            } catch (e) {
                // Storage blocked - ignore
            }
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
    try {
        localStorage.removeItem('chatSessionId');
        localStorage.removeItem('chat_last_context');
        localStorage.removeItem('chat_is_waiting');
    } catch (e) {
        // Storage blocked - ignore
    }
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = `
        <div class="bg-red-50 p-3 rounded-2xl rounded-tl-none text-sm text-gray-800 max-w-[85%] self-start">
          Xin chào! Tôi có thể giúp gì cho bạn về các thủ tục hành chính tại phường Đông Mai?
        </div>`;
    // Generate new session ID immediately
    const sessionId = Math.random().toString(36).substring(2) + Date.now().toString(36);
    try {
        localStorage.setItem('chatSessionId', sessionId);
    } catch (e) {
        // Storage blocked - ignore
    }
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
    let lastWaiting = null;
    try {
        lastWaiting = localStorage.getItem('chat_is_waiting');
    } catch (e) {
        // Storage blocked
    }

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
                try {
                    localStorage.removeItem('chat_is_waiting');
                } catch (e) {}
            }, 60000 - diff);
        } else {
            try {
                localStorage.removeItem('chat_is_waiting');
            } catch (e) {}
        }
    }

    // Reuse or create Session ID
    let sessionId = null;
    try {
        sessionId = localStorage.getItem('chatSessionId');
        if (!sessionId) {
            sessionId = Math.random().toString(36).substring(2) + Date.now().toString(36);
            localStorage.setItem('chatSessionId', sessionId);
        }
    } catch (e) {
        sessionId = Math.random().toString(36).substring(2) + Date.now().toString(36);
    }
    console.log("Chat Session ID:", sessionId);

    // Auto-focus input
    document.getElementById('chat-input')?.focus();
});
