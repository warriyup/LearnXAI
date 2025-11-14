// === LearnX Full Version Client Script ===

// DOM references
const chatBox = document.getElementById("chat-box");
const msgInput = document.getElementById("msg");
const sendBtn = document.getElementById("send-btn");
const chatListRoot = document.getElementById("chat-list");
const newChatBtn = document.getElementById("new-chat-btn");
const searchInput = document.getElementById("search");
const chatTitleEl = document.getElementById("chat-title");
const versionBtn = document.getElementById("version-btn");
const getVipBtn = document.getElementById("vip-btn");

let currentChat = null;
let pendingRequestId = 0;
let contextMenu = null;

// ============== UTILS ==============
function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function mdToHtml(t) {
  if (!t) return "";
  let s = escapeHtml(t);
  s = s.replace(/\*\*(.*?)\*\*/g, "<b>$1</b>");
  s = s.replace(/\*(.*?)\*/g, "<i>$1</i>");
  s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
  s = s.replace(/\r\n|\r/g, "\n");
  s = s.replace(/\n{2,}/g, "</p><p>");
  s = s.replace(/\n/g, "<br>");
  return `<p>${s}</p>`;
}

// ============== CHAT UI ==============
function clearChatUI() {
  chatBox.innerHTML = "";
}

function addMessageToUI(text, sender) {
  const row = document.createElement("div");
  row.className = "msg-row " + (sender === "user" ? "user" : "bot");

  const bubble = document.createElement("div");
  bubble.className = "msg " + (sender === "user" ? "msg-user" : "msg-bot");
  bubble.innerHTML = mdToHtml(text);

  row.appendChild(bubble);
  chatBox.appendChild(row);

  chatBox.scrollTop = chatBox.scrollHeight;
}

function showThinking() {
  const id = "thinking-indicator";
  if (document.getElementById(id)) return;

  const row = document.createElement("div");
  row.className = "msg-row bot";
  row.id = id;

  const bubble = document.createElement("div");
  bubble.className = "msg msg-bot";
  bubble.innerHTML = "<p>LearnX AI думает…</p>";

  row.appendChild(bubble);
  chatBox.appendChild(row);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function removeThinking() {
  const t = document.getElementById("thinking-indicator");
  if (t) t.remove();
}

// ============== CHAT LIST ==============
async function loadChats() {
  try {
    const res = await fetch("/full/list_chats");
    const data = await res.json();
    renderChatList(data);
  } catch (e) {
    chatListRoot.innerHTML =
      `<div style="color:var(--muted);padding:8px">Не удалось загрузить чаты</div>`;
  }
}

function renderChatList(data) {
  chatListRoot.innerHTML = "";

  Object.keys(data).forEach(id => {
    const info = data[id];
    const item = document.createElement("div");
    item.className = "chat-item";
    item.dataset.chatId = id;

    item.innerHTML = `
      <span class="chat-title">${escapeHtml(info.title || "Новый чат")}</span>
      <span class="dots">⋯</span>
    `;

    // Open chat by clicking item
    item.addEventListener("click", () => openChat(id));

    // Dots menu
    const dots = item.querySelector(".dots");
    dots.addEventListener("click", (ev) => {
      ev.stopPropagation();
      ev.preventDefault();
      showContextMenu(ev, id);
    });

    chatListRoot.appendChild(item);
  });
}

// ============== CHAT ACTIONS ==============
async function newChat() {
  try {
    const res = await fetch("/full/new_chat", { method: "POST" });
    const j = await res.json();
    currentChat = j.chat_id;

    clearChatUI();
    addMessageToUI("Новый чат создан.", "bot");

    await loadChats();
    openChat(currentChat);
  } catch (e) {
    alert("Не удалось создать чат");
  }
}

async function openChat(id) {
  currentChat = id;
  clearChatUI();
  setChatTitle("LearnX AI");

  try {
    const res = await fetch(`/full/get_chat/${encodeURIComponent(id)}`);
    const d = await res.json();

    setChatTitle(`LearnX AI — ${d.title || "Новый чат"}`);

    (d.messages || []).forEach(m => {
      addMessageToUI(m.content, m.role === "user" ? "user" : "bot");
    });

  } catch (e) {
    addMessageToUI("Не удалось загрузить чат.", "bot");
  }
}

function setChatTitle(text) {
  chatTitleEl.textContent = text;
}

async function sendMessage() {
  const text = msgInput.value.trim();
  if (!text) return;
  if (!currentChat) return alert("Сначала создайте чат.");

  addMessageToUI(text, "user");
  msgInput.value = "";
  msgInput.focus();

  showThinking();
  const reqId = ++pendingRequestId;

  try {
    const res = await fetch(`/full/chat/${encodeURIComponent(currentChat)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });

    const d = await res.json();

    if (reqId !== pendingRequestId) {
      removeThinking();
      return;
    }

    removeThinking();
    addMessageToUI(d.reply || "Ошибка AI", "bot");
    loadChats();

  } catch (e) {
    removeThinking();
    addMessageToUI("Ошибка соединения с ИИ.", "bot");
  }
}

// ============== CONTEXT MENU (rename/delete) ==============
function showContextMenu(ev, chatId) {
  if (contextMenu) contextMenu.remove();

  const menu = document.createElement("div");
  menu.className = "context-menu";
  menu.innerHTML = `
    <button data-act="rename">Переименовать</button>
    <button data-act="delete" class="danger">Удалить</button>
  `;

  document.getElementById("context-root").appendChild(menu);

  menu.style.left = ev.pageX + "px";
  menu.style.top = ev.pageY + "px";

  contextMenu = menu;

  menu.addEventListener("click", async (e) => {
    const act = e.target.dataset.act;
    if (!act) return;

    if (act === "rename") {
      const title = prompt("Новое название:");
      if (!title) return;
      await fetch(`/full/rename_chat/${chatId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title })
      });
      loadChats();
      if (currentChat === chatId) setChatTitle(`LearnX AI — ${title}`);
    }

    if (act === "delete") {
      if (!confirm("Удалить чат?")) return;
      await fetch(`/full/delete_chat/${chatId}`, { method: "POST" });
      if (currentChat === chatId) {
        clearChatUI();
        setChatTitle("LearnX AI");
        currentChat = null;
      }
      loadChats();
    }

    menu.remove();
    contextMenu = null;
  });

  requestAnimationFrame(() => {
    window.addEventListener("click", dismissContextMenu, { once: true });
  });
}

function dismissContextMenu() {
  if (contextMenu) contextMenu.remove();
  contextMenu = null;
}

// ============== TOP RIGHT MENU ==============
function createTopMenu() {
  const popup = document.createElement("div");
  popup.className = "menu-popup";
  popup.id = "menu-popup";

  popup.innerHTML = `
    <button id="theme-toggle">Переключить тему</button>
    <button id="about-btn">О приложении</button>
  `;

  document.body.appendChild(popup);

  document.getElementById("theme-toggle").addEventListener("click", () => {
    document.body.classList.toggle("theme-light");
    popup.remove();
  });

  document.getElementById("about-btn").addEventListener("click", () => {
    alert("LearnX — MVP. Версия v1.0");
    popup.remove();
  });

  requestAnimationFrame(() => {
    window.addEventListener("click", () => popup.remove(), { once: true });
  });
}

// ============== INIT ==============
async function init() {
  newChatBtn.addEventListener("click", newChat);
  sendBtn.addEventListener("click", sendMessage);

  msgInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  searchInput.addEventListener("input", () => {
    const q = searchInput.value.toLowerCase();
    Array.from(chatListRoot.children).forEach(node => {
      const t = node.querySelector(".chat-title").textContent.toLowerCase();
      node.style.display = t.includes(q) ? "" : "none";
    });
  });

  if (versionBtn) versionBtn.addEventListener("click", () => alert("Скоро!"));
  if (getVipBtn) getVipBtn.addEventListener("click", () => alert("VIP скоро!"));

  const menuBtn = document.getElementById("menu-btn");
  if (menuBtn) {
    menuBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const exists = document.getElementById("menu-popup");
      if (exists) return exists.remove();
      createTopMenu();
    });
  }

  await loadChats();
}

init();
