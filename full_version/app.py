from flask import Blueprint, request, jsonify
import uuid
import os
from openai import OpenAI

from db import (
    init_db,
    get_all_chats,
    new_chat,
    get_chat,
    add_message,
    rename_chat,
    delete_chat
)

# Инициализация базы
init_db()

full_bp = Blueprint("full", __name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@full_bp.route("/list_chats")
def list_chats():
    return jsonify(get_all_chats())


@full_bp.route("/new_chat", methods=["POST"])
def create_chat():
    chat_id = str(uuid.uuid4())
    new_chat(chat_id)
    return jsonify({"chat_id": chat_id})


@full_bp.route("/get_chat/<chat_id>")
def get_chat_route(chat_id):
    return jsonify(get_chat(chat_id))


@full_bp.route("/chat/<chat_id>", methods=["POST"])
def ask_ai(chat_id):
    data = request.get_json()
    message = data.get("message")

    if not message:
        return jsonify({"error": "empty message"}), 400

    # Сохранить сообщение пользователя
    add_message(chat_id, "user", message)

    # Вызов ИИ
    reply = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Ты — мощная и дружелюбная AI Model LearnX."},
            {"role": "user", "content": message}
        ]
    ).choices[0].message.content

    # Сохранить ответ
    add_message(chat_id, "assistant", reply)

    return jsonify({"reply": reply})


@full_bp.route("/rename_chat/<chat_id>", methods=["POST"])
def rename_chat_route(chat_id):
    title = request.json.get("title")
    rename_chat(chat_id, title)
    return jsonify({"status": "ok"})


@full_bp.route("/delete_chat/<chat_id>", methods=["POST"])
def delete_chat_route(chat_id):
    delete_chat(chat_id)
    return jsonify({"status": "ok"})
