from flask import Blueprint, request, jsonify, render_template
import os
import uuid
import requests
from db import init_db, list_chats, create_chat, get_chat, add_message, rename_chat, delete_chat

init_db()

blueprint = Blueprint("full", __name__, template_folder="templates", static_folder="static", static_url_path="/full/static")

OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY") or os.environ.get("OPENAI_API_KEY")
# модель можно переопределить через переменную окружения MODEL
DEFAULT_MODEL = os.environ.get("MODEL", "qwen2.5-7b-instruct")

def ask_openrouter(messages, model=DEFAULT_MODEL, max_tokens=300, temperature=0.7):
    if not OPENROUTER_KEY:
        return "Ошибка: ключ API для OpenRouter не настроен."

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        if not resp.ok:
            # возвращаем текст ошибки от OpenRouter (поможет дебагу)
            try:
                return f"Ошибка от OpenRouter: {resp.status_code} {resp.text}"
            except Exception:
                return f"Ошибка от OpenRouter: {resp.status_code}"
        j = resp.json()
        choices = j.get("choices")
        if isinstance(choices, list) and choices:
            msg = choices[0].get("message") or {}
            content = msg.get("content")
            if isinstance(content, str):
                return content
        return "Ошибка: некорректный ответ от OpenRouter."
    except requests.exceptions.RequestException:
        return "Ошибка соединения с ИИ."

@blueprint.route("/")
def index():
    return render_template("index.html")

@blueprint.route("/list_chats")
def list_chats_api():
    return jsonify(list_chats())

@blueprint.route("/new_chat", methods=["POST"])
def new_chat_api():
    chat_id = str(uuid.uuid4())
    create_chat(chat_id)
    return jsonify({"chat_id": chat_id})

@blueprint.route("/get_chat/<chat_id>")
def get_chat_api(chat_id):
    return jsonify(get_chat(chat_id) or {})

@blueprint.route("/rename_chat/<chat_id>", methods=["POST"])
def rename_chat_api(chat_id):
    title = request.json.get("title", "")
    rename_chat(chat_id, title)
    return jsonify({"status": "ok"})

@blueprint.route("/delete_chat/<chat_id>", methods=["POST"])
def delete_chat_api(chat_id):
    delete_chat(chat_id)
    return jsonify({"status": "ok"})

@blueprint.route("/chat/<chat_id>", methods=["POST"])
def chat_api(chat_id):
    data = request.get_json() or {}
    text = data.get("message", "")
    if not text:
        return jsonify({"reply": "Ошибка: пустое сообщение."})
    add_message(chat_id, "user", text)
    history = get_chat(chat_id).get("messages", [])[-10:]
    messages = []
    for m in history:
        role = m.get("role", "user")
        content = m.get("content", "")
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": text})
    reply = ask_openrouter(messages, model="qwen/qwen2.5-7b-instruct:free", max_tokens=250, temperature=0.7)
    add_message(chat_id, "assistant", reply)
    return jsonify({"reply": reply})
