const chatBox = document.getElementById("chat-box");
const msgInput = document.getElementById("msg");
const sendBtn = document.getElementById("send-btn");
const chatListRoot = document.getElementById("chat-list");

let currentChat = null;

// Markdown-like formatting
function md(t) {
    return t
        .replace(/\*\*(.*?)\*\*/g, "<b>$1</b>")
        .replace(/\*(.*?)\*/g, "<i>$1</i>")
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        .replace(/\n{2,}/g, "</p><p>")
        .replace(/\n/g, "<br>");
}

function clearChatUI() {
    chatBox.innerHTML = "";
}

function addMsg(text, sender) {
    const div = document.createElement("div");
    div.className = sender === "user" ? "msg-user" : "msg-bot";
    div.innerHTML = `<p>${md(text)}</p>`;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function addThinking() {
    const div = document.createElement("div");
    div.className = "msg-bot";
    div.id = "thinking";
    div.innerHTML = "<p>LearnX AI думает…</p>";
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function removeThinking() {
    const el = document.getElementById("thinking");
    if (el) el.remove();
}

async function loadChats() {
    try {
        const res = await fetch("/list_chats");
        const data = await res.json();
        chatListRoot.innerHTML = "";

        for (const id of Object.keys(data)) {
            const item = document.createElement("div");
            item.className = "chat-item";
            item.innerHTML = `
                <span class="chat-title">${data[id].title}</span>
                <span class="dots">⋯</span>
            `;

            item.onclick = () => openChat(id);
            item.querySelector(".dots").onclick = (ev) => {
                ev.stopPropagation();
                showMenu(ev, id);
            };

            chatListRoot.appendChild(item);
        }
    } catch (e) {
        console.error(e);
    }
}

async function newChat() {
    const res = await fetch("/new_chat", { method: "POST" });
    const data = await res.json();
    currentChat = data.chat_id;

    clearChatUI();
    addMsg("Новый чат создан!", "bot");

    await loadChats();
    openChat(currentChat);
}

async function openChat(id) {
    currentChat = id;
    clearChatUI();

    const res = await fetch(`/get_chat/${id}`);
    const data = await res.json();

    for (const msg of data.messages) {
        addMsg(msg.content, msg.role === "user" ? "user" : "bot");
    }
}

async function sendMessage() {
    const text = msgInput.value.trim();
    if (!text || !currentChat) return;

    addMsg(text, "user");
    msgInput.value = "";
    addThinking();

    try {
        const res = await fetch(`/chat/${currentChat}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        });

        const data = await res.json();
        removeThinking();
        addMsg(data.reply, "bot");
        await loadChats();

    } catch (e) {
        removeThinking();
        addMsg("Ошибка соединения с ИИ.", "bot");
    }
}

// ===== CONTEXT MENU =====

let menu = null;

function showMenu(ev, id) {
    if (menu) menu.remove();

    menu = document.createElement("div");
    menu.className = "context-menu";
    menu.innerHTML = `
        <button data-act="rename">Переименовать</button>
        <button data-act="delete" class="danger">Удалить</button>
    `;

    document.body.appendChild(menu);
    menu.style.left = ev.pageX + "px";
    menu.style.top = ev.pageY + "px";
    menu.style.display = "block";

    menu.onclick = e => {
        if (e.target.dataset.act === "rename") renameChat(id);
        if (e.target.dataset.act === "delete") deleteChat(id);
        menu.remove();
        menu = null;
    };

    window.addEventListener("click", () => {
        if (menu) menu.remove();
        menu = null;
    }, { once: true });
}

async function renameChat(id) {
    const t = prompt("Новое название:");
    if (!t) return;

    await fetch(`/rename_chat/${id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: t })
    });

    loadChats();
}

async function deleteChat(id) {
    if (!confirm("Удалить чат?")) return;

    await fetch(`/delete_chat/${id}`, { method: "POST" });

    if (currentChat === id) {
        clearChatUI();
        currentChat = null;
    }

    loadChats();
}

// ===== EVENTS =====

msgInput.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

sendBtn.onclick = sendMessage;

loadChats();
