"""SQLite storage: analyses, trusted contacts, scam-number reports, simulator scores."""
import sqlite3
import time
from contextlib import closing

import config


def _run(sql, args=(), fetch=False):
    with closing(sqlite3.connect(config.DB_PATH)) as c:
        c.row_factory = sqlite3.Row
        cur = c.execute(sql, args)
        rows = cur.fetchall() if fetch else None
        c.commit()
        return rows


def init():
    with closing(sqlite3.connect(config.DB_PATH)) as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS analyses(
                id INTEGER PRIMARY KEY, chat_id INTEGER, ts REAL,
                score INTEGER, level TEXT, tactics TEXT, transcript TEXT);
            CREATE TABLE IF NOT EXISTS contacts(
                owner_id INTEGER, contact_id INTEGER, UNIQUE(owner_id, contact_id));
            CREATE TABLE IF NOT EXISTS invite_codes(code TEXT PRIMARY KEY, owner_id INTEGER);
            CREATE TABLE IF NOT EXISTS reports(
                number TEXT PRIMARY KEY, count INTEGER, last_ts REAL);
            CREATE TABLE IF NOT EXISTS sim_scores(
                id INTEGER PRIMARY KEY, chat_id INTEGER, ts REAL,
                scenario TEXT, outcome TEXT, score INTEGER);
            """
        )
        c.commit()


def save_analysis(chat_id, score, level, tactics, transcript=""):
    _run("INSERT INTO analyses(chat_id, ts, score, level, tactics, transcript) VALUES(?,?,?,?,?,?)",
         (chat_id, time.time(), score, level, tactics, transcript))


def add_invite(code, owner_id):
    _run("INSERT OR REPLACE INTO invite_codes(code, owner_id) VALUES(?,?)", (code, owner_id))


def redeem_invite(code, contact_id):
    rows = _run("SELECT owner_id FROM invite_codes WHERE code=?", (code,), fetch=True)
    if not rows:
        return None
    owner = rows[0]["owner_id"]
    _run("INSERT OR IGNORE INTO contacts(owner_id, contact_id) VALUES(?,?)", (owner, contact_id))
    return owner


def contacts_of(owner_id):
    rows = _run("SELECT contact_id FROM contacts WHERE owner_id=?", (owner_id,), fetch=True)
    return [r["contact_id"] for r in rows]


def report_number(number):
    _run("INSERT INTO reports(number, count, last_ts) VALUES(?,1,?) "
         "ON CONFLICT(number) DO UPDATE SET count=count+1, last_ts=excluded.last_ts",
         (number, time.time()))
    return number_reports(number)


def number_reports(number):
    rows = _run("SELECT count FROM reports WHERE number=?", (number,), fetch=True)
    return rows[0]["count"] if rows else 0


def save_sim(chat_id, scenario, outcome, score):
    _run("INSERT INTO sim_scores(chat_id, ts, scenario, outcome, score) VALUES(?,?,?,?,?)",
         (chat_id, time.time(), scenario, outcome, score))
