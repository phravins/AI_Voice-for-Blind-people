from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from config import MONGO_URI, MONGO_DB_NAME
import os

_client = MongoClient(MONGO_URI)

def _db():
    return _client[MONGO_DB_NAME]

def _oid(val):
    try:
        return ObjectId(val)
    except Exception:
        return None

def init_db():
    db = _db()
    db.projects.create_index("name")
    db.pdfs.create_index("project_id")
    db.chats.create_index("project_id")
    db.messages.create_index("chat_id")

def list_projects():
    db = _db()
    docs = db.projects.find({}, projection={"name": 1}).sort("_id", -1)
    return [{"id": str(d["_id"]), "name": d.get("name", "")} for d in docs]

def create_project(name):
    db = _db()
    db.projects.insert_one({"name": name, "created_at": datetime.utcnow()})

def get_project(pid):
    db = _db()
    oid = _oid(pid)
    if not oid:
        return None
    d = db.projects.find_one({"_id": oid}, projection={"name": 1})
    if not d:
        return None
    return {"id": str(d["_id"]), "name": d.get("name", "")}

def ensure_default_project():
    db = _db()
    d = db.projects.find_one({"name": "Default"})
    if not d:
        res = db.projects.insert_one({"name": "Default", "created_at": datetime.utcnow()})
        return str(res.inserted_id)
    return str(d["_id"])

def list_project_pdfs(project_id):
    db = _db()
    docs = db.pdfs.find({"project_id": str(project_id)}, projection={"filename": 1}).sort("_id", -1)
    return [{"id": str(d["_id"]), "filename": d.get("filename", "")} for d in docs]

def add_pdf(project_id, filename, path):
    db = _db()
    db.pdfs.insert_one({
        "project_id": str(project_id),
        "filename": filename,
        "path": path,
        "uploaded_at": datetime.utcnow()
    })

def get_pdf(pdf_id):
    db = _db()
    oid = _oid(pdf_id)
    if not oid:
        return None
    d = db.pdfs.find_one({"_id": oid})
    if not d:
        return None
    return {"id": str(d["_id"]), "project_id": d.get("project_id"), "filename": d.get("filename"), "path": d.get("path")}

def delete_pdf(pdf_id):
    db = _db()
    pdf = get_pdf(pdf_id)
    if not pdf:
        return False
    if pdf.get("path") and os.path.exists(pdf["path"]):
        try:
            os.remove(pdf["path"])
        except Exception:
            pass
    db.pdfs.delete_one({"_id": ObjectId(pdf_id)})
    return True

def create_chat(project_id, title):
    db = _db()
    res = db.chats.insert_one({
        "project_id": str(project_id),
        "title": title,
        "created_at": datetime.utcnow()
    })
    return str(res.inserted_id)

def list_chats(project_id):
    db = _db()
    docs = db.chats.find({"project_id": str(project_id)}, projection={"title": 1}).sort("_id", -1)
    return [{"id": str(d["_id"]), "title": d.get("title", "")} for d in docs]

def add_message(chat_id, role, text, audio=None):
    db = _db()
    db.messages.insert_one({
        "chat_id": str(chat_id),
        "role": role,
        "text": text,
        "audio": audio,
        "created_at": datetime.utcnow()
    })

def list_messages(chat_id):
    db = _db()
    docs = db.messages.find({"chat_id": str(chat_id)}, projection={"role": 1, "text": 1, "audio": 1}).sort("_id", 1)
    return [{"role": d.get("role", ""), "text": d.get("text", ""), "audio": d.get("audio")} for d in docs]
