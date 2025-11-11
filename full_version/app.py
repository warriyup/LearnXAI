from flask import Blueprint, render_template, request, jsonify
from db import get_chats, get_chat, new_chat, add_message, rename_chat, delete_chat
import os

full_bp = Blueprint(
    "full_bp",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/full/static"
)

@full_bp.route("/")
def index():
    return render_template("index.html")

@full_bp.route("/list_chats")
def list_chats():
    return jsonify(get_chats())

@full_bp.route("/new_chat", methods=["POST"])
def new_chat_route():
    return jsonify({"chat_id": new_chat()})

@full_bp.route("/get_chat/<chat_id>")
def get_chat_route(chat_id):
    return jsonify(get_chat(chat_id))

@full_bp.route("/chat/<chat_id>", methods=["POST"])
def chat_route(chat_id):
    msg = request.json.get("message", "")
    reply = add_message(chat_id, msg)
    return jsonify({"reply": reply})

@full_bp.route("/rename_chat/<chat_id>", methods=["POST"])
def rename_chat_route(chat_id):
    title = request.json.get("title", "")
    rename_chat(chat_id, title)
    return jsonify({"ok": True})

@full_bp.route("/delete_chat/<chat_id>", methods=["POST"])
def delete_chat_route(chat_id):
    delete_chat(chat_id)
    return jsonify({"ok": True})
