"""SQLite persistence for quests, task completion, photos and journal entries."""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(os.getenv("GRASSQUEST_DB_PATH", "data/grassquest.db"))


def connect(path: Path | str | None = None) -> sqlite3.Connection:
    target = Path(path) if path else DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(target)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db


def init_db(path: Path | str | None = None) -> None:
    with connect(path) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS quests(
          id INTEGER PRIMARY KEY, title TEXT NOT NULL, season TEXT NOT NULL, place TEXT NOT NULL,
          group_name TEXT NOT NULL, minutes INTEGER NOT NULL, difficulty TEXT NOT NULL,
          tasks_json TEXT NOT NULL, completed_json TEXT NOT NULL DEFAULT '[]',
          status TEXT NOT NULL DEFAULT 'Planned', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS journals(
          id INTEGER PRIMARY KEY, quest_id INTEGER NOT NULL REFERENCES quests(id) ON DELETE CASCADE,
          body TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', photos_json TEXT NOT NULL DEFAULT '[]',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)


def save_quest(quest: dict[str, Any], path: Path | str | None = None) -> int:
    init_db(path)
    with connect(path) as db:
        cur = db.execute("INSERT INTO quests(title,season,place,group_name,minutes,difficulty,tasks_json) VALUES(?,?,?,?,?,?,?)",
                         (quest["title"], quest["season"], quest["place"], quest["group"], quest["minutes"], quest["difficulty"], json.dumps(quest["tasks"])))
        return int(cur.lastrowid)


def list_quests(path: Path | str | None = None) -> list[dict[str, Any]]:
    init_db(path)
    with connect(path) as db:
        return [dict(row) for row in db.execute("SELECT * FROM quests ORDER BY created_at DESC,id DESC")]


def get_quest(quest_id: int, path: Path | str | None = None) -> dict[str, Any] | None:
    with connect(path) as db:
        row = db.execute("SELECT * FROM quests WHERE id=?", (quest_id,)).fetchone()
        return dict(row) if row else None


def update_completed(quest_id: int, completed: list[int], path: Path | str | None = None) -> None:
    with connect(path) as db:
        db.execute("UPDATE quests SET completed_json=? WHERE id=?", (json.dumps(sorted(set(completed))), quest_id))


def mark_done(quest_id: int, path: Path | str | None = None) -> None:
    with connect(path) as db:
        db.execute("UPDATE quests SET status='Done' WHERE id=?", (quest_id,))


def delete_quest(quest_id: int, path: Path | str | None = None) -> None:
    with connect(path) as db:
        db.execute("DELETE FROM quests WHERE id=?", (quest_id,))


def save_journal(quest_id: int, body: str, note: str = "", photos: list[dict[str, Any]] | None = None, path: Path | str | None = None) -> int:
    with connect(path) as db:
        cur = db.execute("INSERT INTO journals(quest_id,body,note,photos_json) VALUES(?,?,?,?)", (quest_id, body, note, json.dumps(photos or [])))
        return int(cur.lastrowid)


def list_journals(path: Path | str | None = None) -> list[dict[str, Any]]:
    init_db(path)
    with connect(path) as db:
        return [dict(row) for row in db.execute("SELECT j.*,q.title AS quest_title FROM journals j JOIN quests q ON q.id=j.quest_id ORDER BY j.created_at DESC,j.id DESC")]


def update_journal(journal_id: int, body: str, path: Path | str | None = None) -> None:
    with connect(path) as db:
        db.execute("UPDATE journals SET body=? WHERE id=?", (body, journal_id))


def clear_all(path: Path | str | None = None) -> None:
    with connect(path) as db:
        db.execute("DELETE FROM journals")
        db.execute("DELETE FROM quests")
