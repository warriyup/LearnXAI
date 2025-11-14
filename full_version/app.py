from flask import Blueprint, request, jsonify, render_template
import os
import uuid
import requests
from db import init_db, list_chats, create_chat, get_chat, add_message, rename_chat, delete_chat

init_db()

blueprint = Blueprint(
    "full",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/full/static"
)

# ------------------------------
# Настройки ИИ
# ------------------------------
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY")

MAIN_MODEL = "google/gemini-2.0-flash-lite-preview"
FALLBACK_MODEL = "deepseek/deepseek-chat"
MAX_TOKENS = 300
MAX_HISTORY = 8
TEMPERATURE = 0.55


# ------------------------------
# Отправка запроса в OpenRouter
# ------------------------------
def ask_openrouter(messages, model=MAIN_MODEL):

    if not OPENROUTER_KEY:
        return "Ошибка: ключ OpenRouter не найден."

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE
    }

    # ---------- Основная модель ----------
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        if r.ok:
            j = r.json()
            return j["choices"][0]["message"]["content"]
        else:
            raise Exception("Main model failed")
    except:
        # ---------- Fallback модель ----------
        try:
            payload["model"] = FALLBACK_MODEL
            r = requests.post(url, json=payload, headers=headers, timeout=30)
            if r.ok:
                j = r.json()
                return j["choices"][0]["message"]["content"]
            else:
                return "Ошибка: ИИ временно недоступен."
        except:
            return "Ошибка: не удалось подключиться к ИИ."


# ------------------------------
# Роуты
# ------------------------------
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


# ------------------------------
# Основной чат-эндпоинт
# ------------------------------
@blueprint.route("/chat/<chat_id>", methods=["POST"])
def chat_api(chat_id):

    data = request.get_json() or {}
    text = data.get("message", "").strip()

    if not text:
        return jsonify({"reply": "Ошибка: пустое сообщение."})

    # добавляем сообщение пользователя
    add_message(chat_id, "user", text)

    # загружаем историю
    chat = get_chat(chat_id)
    history = chat.get("messages", [])[-MAX_HISTORY:]

    # формируем нормальные messages
    messages = [
        {
            "role": "system",
            "content": (
                "Ты — умный и дружелюбный ИИ-помощник для школьников. "
                "Отвечай коротко, ясно, помогай решать задачи по школе. "
                "Не используй ненормативную лексику. "
                "Объясняй простыми словами."
            )
        }
    ]

    for m in history:
        messages.append({"role": m["role"], "content": m["content"]})

    messages.append({"role": "user", "content": text})

    # обращаемся к ИИ
    reply = ask_openrouter(messages)

    # сохраняем ответ
    add_message(chat_id, "assistant", reply)

    return jsonify({"reply": reply})
