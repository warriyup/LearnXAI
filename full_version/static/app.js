// full version client script - replace entire file
const chatBox = document.getElementById("chat-box");
const msgInput = document.getElementById("msg");
const sendBtn = document.getElementById("send-btn");
const chatListRoot = document.getElementById("chat-list");
const newChatBtn = document.getElementById("new-chat-btn");
const searchInput = document.getElementById("search");
const chatTitleEl = document.getElementById("chat-title");
const dailyCounter = document.getElementById("daily-counter");
const versionBtn = document.getElementById("version-btn");
const themeToggle = document.getElementById("theme-toggle");
const getVipBtn = document.getElementById("get-vip-btn");

let currentChat = null;
let pendingRequestId = 0;
let contextMenu = null;

function escapeHtml(s){ return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;"); }

function mdToHtml(t){
  if(!t) return "";
  let s = escapeHtml(t);
  s = s.replace(/\*\*(.*?)\*\*/g,"<b>$1</b>");
  s = s.replace(/\*(.*?)\*/g,"<i>$1</i>");
  s = s.replace(/`([^`]+)`/g,"<code>$1</code>");
  s = s.replace(/\r\n|\r/g,"\n");
  s = s.replace(/\n{2,}/g,"</p><p>");
  s = s.replace(/\n/g,"<br>");
  return `<p>${s}</p>`;
}

function clearChatUI(){ chatBox.innerHTML = ""; }

function addMessageToUI(text, sender){
  const row = document.createElement("div");
  row.className = "msg-row " + (sender === "user" ? "user":"bot");
  const bubble = document.createElement("div");
  bubble.className = "msg " + (sender === "user" ? "msg-user" : "msg-bot");
  bubble.innerHTML = mdToHtml(text);
  row.appendChild(bubble);
  chatBox.appendChild(row);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function showThinking(){
  const id = "thinking-indicator";
  if(document.getElementById(id)) return;
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

function removeThinking(){
  const t = document.getElementById("thinking-indicator");
  if(t) t.remove();
}

async function loadChats(){
  try{
    const res = await fetch("/full/list_chats");
    if(!res.ok) throw new Error("failed");
    const data = await res.json();
    renderChatList(data);
  }catch(e){
    chatListRoot.innerHTML = `<div style="color:var(--muted);padding:8px">Не удалось загрузить чаты</div>`;
  }
}

function renderChatList(data){
  chatListRoot.innerHTML = "";
  const keys = Object.keys(data);
  keys.forEach(id=>{
    const info = data[id] || {};
    const item = document.createElement("div");
    item.className = "chat-item";
    item.dataset.chatId = id;
    item.innerHTML = `<span class="chat-title">${escapeHtml(info.title||"Новый чат")}</span><span class="dots">⋯</span>`;
    item.onclick = ()=>openChat(id);
    const dots = item.querySelector(".dots");
    dots.addEventListener("click", (ev)=>{ ev.stopPropagation(); showContextMenu(ev, id); });
    chatListRoot.appendChild(item);
  });
}

async function newChat(){
  try{
    const res = await fetch("/full/new_chat", { method:"POST" });
    if(!res.ok) throw new Error("failed");
    const j = await res.json();
    currentChat = j.chat_id;
    clearChatUI();
    addMessageToUI("Новый чат создан.","bot");
    await loadChats();
    openChat(currentChat);
  }catch(e){
    alert("Не удалось создать чат");
  }
}

async function openChat(id){
  currentChat = id;
  clearChatUI();
  setChatTitle("LearnX AI");
  try{
    const res = await fetch(`/full/get_chat/${encodeURIComponent(id)}`);
    if(!res.ok) throw new Error("failed");
    const d = await res.json();
    const chatName = d.title || "Новый чат";
    setChatTitle(`LearnX AI — ${chatName}`);
    (d.messages||[]).forEach(m=>{
      addMessageToUI(m.content, m.role === "user" ? "user":"bot");
    });
  }catch(e){
    addMessageToUI("Не удалось загрузить этот чат.","bot");
  }
}

function setChatTitle(text){
  chatTitleEl.textContent = text;
}

async function sendMessage(){
  const text = msgInput.value.trim();
  if(!text) return;
  if(!currentChat){ alert("Сначала создайте чат."); return; }
  addMessageToUI(text, "user");
  msgInput.value = "";
  msgInput.focus();
  showThinking();
  const thisReq = ++pendingRequestId;
  try{
    const res = await fetch(`/full/chat/${encodeURIComponent(currentChat)}`, {
      method:"POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ message: text })
    });
    if(!res.ok) throw new Error("failed");
    const d = await res.json();
    if(thisReq !== pendingRequestId){
      removeThinking();
      return;
    }
    removeThinking();
    const reply = (d && typeof d.reply === "string") ? d.reply : "Не удалось получить ответ от AI.";
    addMessageToUI(reply, "bot");
    await loadChats();
  }catch(e){
    removeThinking();
    addMessageToUI("Ошибка соединения с ИИ.", "bot");
  }
}

function showContextMenu(ev, chatId){
  if(contextMenu) contextMenu.remove();
  const menu = document.createElement("div");
  menu.className = "context-menu";
  menu.innerHTML = `<button data-act="rename">Переименовать</button><button data-act="delete" class="danger">Удалить</button>`;
  document.getElementById("context-root").appendChild(menu);
  menu.style.left = Math.min(window.innerWidth - 220, ev.pageX) + "px";
  menu.style.top = Math.min(window.innerHeight - 140, ev.pageY) + "px";
  contextMenu = menu;
  menu.addEventListener("click", async (e)=>{
    const act = e.target.dataset.act;
    if(!act) return;
    if(act === "rename"){
      const title = prompt("Новое название чата:");
      if(!title) { menu.remove(); contextMenu = null; return; }
      await fetch(`/full/rename_chat/${chatId}`, { method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({ title }) });
      await loadChats();
      if(currentChat === chatId) setChatTitle(`LearnX AI — ${title}`);
    } else if(act === "delete"){
      if(!confirm("Удалить чат?")) { menu.remove(); contextMenu = null; return; }
      await fetch(`/full/delete_chat/${chatId}`, { method:"POST" });
      if(currentChat === chatId){ clearChatUI(); currentChat = null; setChatTitle("LearnX AI"); }
      await loadChats();
    }
    menu.remove();
    contextMenu = null;
  });
  setTimeout(()=>{ window.addEventListener("click", dismissContextMenu, { once:true }) }, 10);
}

function dismissContextMenu(){ if(contextMenu) contextMenu.remove(); contextMenu = null; }

function toggleTheme(){
  const body = document.body;
  if(body.classList.contains("theme-dark")){
    body.classList.remove("theme-dark");
    body.classList.add("theme-light");
  } else {
    body.classList.remove("theme-light");
    body.classList.add("theme-dark");
  }
}

async function init(){
  newChatBtn.addEventListener("click", newChat);
  sendBtn.addEventListener("click", sendMessage);
  if(getVipBtn) getVipBtn.addEventListener("click", ()=>alert("Get VIP — пока без реализации"));
  if(versionBtn) versionBtn.addEventListener("click", ()=>alert("Версия ИИ — переключение (пока заглушка)"));
  if(themeToggle) themeToggle.addEventListener("click", toggleTheme);

  msgInput.addEventListener("keydown", (e)=>{ if(e.key === "Enter" && !e.shiftKey){ e.preventDefault(); sendMessage(); }});
  searchInput.addEventListener("input", ()=>{ const q = searchInput.value.toLowerCase().trim(); Array.from(chatListRoot.children).forEach(node=>{ const t = node.querySelector(".chat-title").textContent.toLowerCase(); node.style.display = t.includes(q) ? "" : "none"; })});

  await loadChats();
  const urlParams = new URLSearchParams(window.location.search);
  const initial = urlParams.get("chat");
  if(initial) setTimeout(()=>openChat(initial), 250);
  updateDailyCounter(0);
}

function updateDailyCounter(n){ dailyCounter.textContent = `You have ${n} messages today`; const bot = document.getElementById("daily-counter-bottom"); if(bot) bot.textContent = `You have ${n} messages today`; }

init();

// --- меню / три точки ---
function createMenuPopup(){
  const popup = document.createElement("div");
  popup.className = "menu-popup";
  popup.id = "menu-popup";
  popup.innerHTML = `
    <button id="theme-toggle">Переключить тему</button>
    <button id="about-btn">О приложении</button>
  `;
  document.body.appendChild(popup);

  // handlers
  document.getElementById("theme-toggle").addEventListener("click", ()=>{
    document.documentElement.classList.toggle("light-theme");
    popup.remove();
  });
  document.getElementById("about-btn").addEventListener("click", ()=>{
    alert("LearnX — MVP. Версия: v1.0");
    popup.remove();
  });

  // click outside closes
  setTimeout(()=> { window.addEventListener("click", ()=> popup.remove(), { once:true }); }, 10);
  return popup;
}

document.addEventListener("DOMContentLoaded", ()=>{
  const menuBtn = document.getElementById("menu-btn");
  if(menuBtn){
    menuBtn.addEventListener("click", (e)=>{
      e.stopPropagation();
      // если уже есть — убрать
      const existing = document.getElementById("menu-popup");
      if(existing){ existing.remove(); return; }
      createMenuPopup();
    });
  }
});
