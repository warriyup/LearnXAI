import sqlite3
from datetime import datetime

DB_PATH = "database.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS chats (id TEXT PRIMARY KEY, title TEXT, created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id TEXT, role TEXT, content TEXT, time TEXT)")
    conn.commit()

def list_chats():
    cur = get_conn().cursor()
    rows = cur.execute("SELECT id,title,created_at FROM chats ORDER BY created_at DESC").fetchall()
    return {r["id"]: {"title": r["title"], "created_at": r["created_at"]} for r in rows}

def create_chat(chat_id):
    cur = get_conn().cursor()
    cur.execute("INSERT INTO chats (id,title,created_at) VALUES (?,?,?)", (chat_id,"Новый чат",datetime.utcnow().isoformat()))
    cur.connection.commit()

def get_chat(chat_id):
    conn = get_conn(); cur = conn.cursor()
    chat = cur.execute("SELECT * FROM chats WHERE id=?", (chat_id,)).fetchone()
    if not chat: return {"title":"Новый чат","messages":[]}
    msgs = cur.execute("SELECT role,content,time FROM messages WHERE chat_id=? ORDER BY id", (chat_id,)).fetchall()
    return {"title": chat["title"], "messages": [dict(m) for m in msgs]}

def add_message(chat_id, role, content):
    cur = get_conn().cursor()
    cur.execute("INSERT INTO messages (chat_id,role,content,time) VALUES (?,?,?,?)", (chat_id,role,content,datetime.utcnow().isoformat()))
    cur.connection.commit()

def rename_chat(chat_id, title):
    cur = get_conn().cursor()
    cur.execute("UPDATE chats SET title=? WHERE id=?", (title,chat_id))
    cur.connection.commit()

def delete_chat(chat_id):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
    cur.execute("DELETE FROM chats WHERE id=?", (chat_id,))
    conn.commit()
