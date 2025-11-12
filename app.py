from flask import Flask, request, redirect, render_template, jsonify
import os, uuid, requests
from db import init_db, get_all_chats, new_chat, get_chat, add_message, rename_chat, delete_chat
from full_version.app import blueprint as full_bp
from light_version.app import blueprint as lite_bp

init_db()
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY")

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

@app.route("/chat/<chat_id>", methods=["POST"])
def chat_route(chat_id):
    user_message = request.json.get("message", "")
    if not user_message:
        return jsonify({"reply": "Ошибка: пустое сообщение."})
    add_message(chat_id, "user", user_message)
    history = get_chat(chat_id)["messages"][-10:]
    payload = {
        "model": "qwen/qwen2.5-7b-instruct:free",
        "messages": history,
        "max_tokens": 200,
        "temperature": 0.7
    }
    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
    reply = "Ошибка соединения с ИИ."
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers, timeout=30)
        if r.ok:
            j = r.json()
            reply = j.get("choices", [{}])[0].get("message", {}).get("content", reply)
    except:
        reply = "Ошибка соединения с ИИ."
    add_message(chat_id, "assistant", reply)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run()
