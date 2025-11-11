from flask import Blueprint, request, jsonify
import uuid
import os
from openai import OpenAI

from db import (
    init_db,
    list_chats,
    create_chat,
    get_chat,
    add_message,
    rename_chat,
    delete_chat
)

# инициализация базы
init_db()

full_bp = Blueprint("full", __name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@full_bp.route("/list_chats")
def list_chats_route():
    return jsonify(list_chats())


@full_bp.route("/new_chat", methods=["POST"])
def new_chat_route():
    chat_id = str(uuid.uuid4())
    create_chat(chat_id)
    return jsonify({"chat_id": chat_id})


@full_bp.route("/get_chat/<chat_id>")
def get_chat_route(chat_id):
    return jsonify(get_chat(chat_id))


@full_bp.route("/chat/<chat_id>", methods=["POST"])
def chat_route(chat_id):
    data = request.get_json()
    message = data.get("message")

    if not message:
        return jsonify({"error": "empty message"}), 400

    # сохранить сообщение юзера
    add_message(chat_id, "user", message)

    # запрос к ИИ
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Ты — дружественный помощник LearnX."},
            {"role": "user", "content": message},
        ]
    )

    reply = response.choices[0].message.content

    # сохранить ответ
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
