from flask import Flask, request, redirect, render_template, jsonify
import os, uuid, requests
from db import init_db, get_all_chats, new_chat, get_chat, add_message, rename_chat, delete_chat
from full_version.app import blueprint as full_bp
from light_version.app import blueprint as lite_bp

init_db()
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY")

# -------------------------------
# Настройки ИИ
# -------------------------------
MAIN_MODEL = "google/gemini-2.0-flash-lite-preview"
FALLBACK_MODEL = "deepseek/deepseek-chat"
MAX_INPUT_CHARS = 5000
MAX_TOKENS = 1500

app = Flask(__name__)
app.register_blueprint(full_bp, url_prefix="/full")
app.register_blueprint(lite_bp, url_prefix="/lite")


@app.route("/")
def root():
    mode = request.cookies.get("mode", "auto")
    if mode == "lite":
        return redirect("/lite/")
    ua = request.headers.get("User-Agent", "")
    if "mobile" in ua.lower():
        return redirect("/lite/")
    return redirect("/full/")


@app.route("/settings")
def settings():
    return render_template("settings.html")


@app.route("/new_chat", methods=["POST"])
def new_chat_route():
    chat_id = str(uuid.uuid4())
    new_chat(chat_id)
    return jsonify({"chat_id": chat_id})


@app.route("/list_chats")
def list_all_chats():
    return jsonify(get_all_chats())


@app.route("/get_chat/<chat_id>")
def get_chat_by_id(chat_id):
    chat = get_chat(chat_id)
    return jsonify(chat or {})


@app.route("/rename_chat/<chat_id>", methods=["POST"])
def rename_chat_api(chat_id):
    new_title = request.json.get("title", "")
    rename_chat(chat_id, new_title)
    return jsonify({"status": "ok"})


@app.route("/delete_chat/<chat_id>", methods=["POST"])
def delete_chat_api(chat_id):
    delete_chat(chat_id)
    return jsonify({"status": "ok"})


# -------------------------------
#  Основной чат-эндпоинт
# -------------------------------
@app.route("/chat/<chat_id>", methods=["POST"])
def chat_route(chat_id):

    user_message = request.json.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "Ошибка: пустое сообщение."})

    # Ограничение длины входа
    if len(user_message) > MAX_INPUT_CHARS:
        user_message = user_message[:MAX_INPUT_CHARS]

    # Записываем сообщение пользователя
    add_message(chat_id, "user", user_message)

    # Забираем историю (не слишком длинную)
    raw_chat = get_chat(chat_id)
    history = raw_chat["messages"][-4:] if raw_chat else []

    # Префикс для "обучения" стиля ИИ
    system_prompt = {
        "role": "system",
        "content": (
            "Ты — ИИ-помощник для школьников. "
            "Отвечай коротко и понятно, "
            "объясняй понятно и не используй матерные слова. "
            "Не уходи в философию. Помогай решать учебные задачи."
        )
    }

    full_messages = [system_prompt] + history

    payload = {
        "model": MAIN_MODEL,
        "messages": full_messages,
        "max_tokens": MAX_TOKENS,
        "temperature": 0.5
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }

    reply = "Ошибка соединения с ИИ."

    # -------------------------------------
    # 1. Пробуем основную модель
    # -------------------------------------
    try:
        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )
        if res.ok:
            j = res.json()
            reply = j.get("choices", [{}])[0].get("message", {}).get("content", reply)
        else:
            raise Exception("Main model error")
    except:
        # -------------------------------------
        # 2. Fallback модель
        # -------------------------------------
        try:
            payload["model"] = FALLBACK_MODEL
            res = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=30
            )
            if res.ok:
                j = res.json()
                reply = j.get("choices", [{}])[0].get("message", {}).get("content", reply)
            else:
                reply = "Ошибка: ИИ сейчас недоступен."
        except:
            reply = "Ошибка: не удаётся получить ответ от ИИ."

    # Записываем ответ ассистента
    add_message(chat_id, "assistant", reply)

    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run()
