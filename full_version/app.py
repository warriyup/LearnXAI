from flask import Blueprint, render_template, request, jsonify
from db import (
    get_all_chats,
    get_chat,
    new_chat,
    add_message,
    rename_chat,
    delete_chat
)
import requests
import os

bp = Blueprint("full", __name__, url_prefix="/full")


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/list_chats")
def list_chats_api():
    return jsonify(get_all_chats())


@bp.route("/new_chat", methods=["POST"])
def new_chat_api():
    chat_id = new_chat()
    return jsonify({"chat_id": chat_id})


@bp.route("/get_chat/<chat_id>")
def get_chat_api(chat_id):
    chat = get_chat(chat_id)
    return jsonify(chat)


@bp.route("/rename_chat/<chat_id>", methods=["POST"])
def rename_chat_api(chat_id):
    title = request.json.get("title", "")
    rename_chat(chat_id, title)
    return jsonify({"status": "ok"})


@bp.route("/delete_chat/<chat_id>", methods=["POST"])
def delete_chat_api(chat_id):
    delete_chat(chat_id)
    return jsonify({"status": "ok"})


@bp.route("/chat/<chat_id>", methods=["POST"])
def chat_api(chat_id):
    text = request.json.get("message", "")

    add_message(chat_id, "user", text)

    key = os.getenv("OPENROUTER_KEY")

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": text}],
        "max_tokens": 300
    }

    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        )

        data = r.json()
        reply = data["choices"][0]["message"]["content"]

    except Exception as e:
        reply = "Ошибка соединения с ИИ."

    add_message(chat_id, "assistant", reply)

    return jsonify({"reply": reply})
