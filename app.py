from flask import Flask, request, redirect, render_template, jsonify
import os, uuid, requests
from db import init_db, get_all_chats, new_chat, get_chat, add_message, rename_chat, delete_chat
from full_version.app import blueprint as full_bp
from light_version.app import blueprint as lite_bp

# =========================
# ИНИЦИАЛИЗАЦИЯ
# =========================
init_db()
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY")

# Модели
MODEL_FREE = "google/gemini-2.0-flash-lite-preview"
MODEL_VIP = "google/gemini-2.0-flash-preview"

# Токены
TOKENS_FREE = 200
TOKENS_VIP = 800

MAX_INPUT_CHARS = 3500   # меньше → дешевле

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


# =========================
#   ЧАТ
# =========================
@app.route("/chat/<chat_id>", methods=["POST"])
def chat_route(chat_id):

    user_message = request.json.get("message", "").strip()
    vip = request.json.get("vip", False)

    if not user_message:
        return jsonify({"reply": "Ошибка: пустое сообщение."})

    if len(user_message) > MAX_INPUT_CHARS:
        user_message = user_message[:MAX_INPUT_CHARS]

    add_message(chat_id, "user", user_message)

    raw = get_chat(chat_id)
    history = raw["messages"][-4:] if raw else []  # <= 4 последних сообщений

    # system prompt дешевый и короткий
    system_prompt = {
        "role": "system",
        "content":
            "Ты — дружелюбный школьный помощник. "
            "Отвечай коротко: 5–6 предложений максимум. "
            "Без сложных терминов, без философии."
    }

    messages = [system_prompt] + history

    payload = {
        "model": MODEL_VIP if vip else MODEL_FREE,
        "messages": messages,
        "max_tokens": TOKENS_VIP if vip else TOKENS_FREE,
        "temperature": 0.5
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }

    try:
        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=20
        )
        j = res.json()
        reply = j.get("choices", [{}])[0].get("message", {}).get("content", "Ошибка ИИ.")
    except:
        reply = "Ошибка: нет ответа от модели."

    add_message(chat_id, "assistant", reply)

    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run()
