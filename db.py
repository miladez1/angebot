# db.py

import sqlite3
import datetime

def init_db():
    conn = sqlite3.connect("tattoo_bot.db")
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS reserve_times (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        time TEXT,
        status TEXT,
        user_id INTEGER,
        lock_until DATETIME,
        receipt_file_id TEXT,
        checked_by_admin INTEGER DEFAULT 0
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS texts (
        key TEXT PRIMARY KEY,
        value TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS ai_setting (
        key TEXT PRIMARY KEY,
        value TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS broadcast (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        date DATETIME
    )""")
    conn.commit()
    conn.close()

def get_setting(key, default=None):
    conn = sqlite3.connect("tattoo_bot.db")
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = sqlite3.connect("tattoo_bot.db")
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()

def add_admin(user_id):
    conn = sqlite3.connect("tattoo_bot.db")
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_admins():
    conn = sqlite3.connect("tattoo_bot.db")
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM admins")
    admins = [row[0] for row in cur.fetchall()]
    conn.close()
    return admins

def add_reserve_date_time(date, time):
    conn = sqlite3.connect("tattoo_bot.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO reserve_times (date, time, status) VALUES (?, ?, 'free')", (date, time))
    conn.commit()
    conn.close()

def get_free_times(date):
    conn = sqlite3.connect("tattoo_bot.db")
    cur = conn.cursor()
    cur.execute(
        "SELECT time FROM reserve_times WHERE date=? AND status='free' AND (lock_until IS NULL OR lock_until<CURRENT_TIMESTAMP)",
        (date,))
    times = [row[0] for row in cur.fetchall()]
    conn.close()
    return times

def lock_reserve_time(date, time, user_id):
    until = (datetime.datetime.now() + datetime.timedelta(minutes=30)).isoformat()
    conn = sqlite3.connect("tattoo_bot.db")
    cur = conn.cursor()
    cur.execute(
        "UPDATE reserve_times SET status='locked', user_id=?, lock_until=? WHERE date=? AND time=?",
        (user_id, until, date, time))
    conn.commit()
    conn.close()

def unlock_reserve_time(date, time):
    conn = sqlite3.connect("tattoo_bot.db")
    cur = conn.cursor()
    cur.execute(
        "UPDATE reserve_times SET status='free', user_id=NULL, lock_until=NULL WHERE date=? AND time=?",
        (date, time))
    conn.commit()
    conn.close()

def confirm_reserve(date, time, user_id, receipt_file_id):
    conn = sqlite3.connect("tattoo_bot.db")
    cur = conn.cursor()
    cur.execute(
        "UPDATE reserve_times SET status='reserved', receipt_file_id=?, user_id=?, checked_by_admin=1 WHERE date=? AND time=?",
        (receipt_file_id, user_id, date, time))
    conn.commit()
    conn.close()

def reject_reserve(date, time):
    unlock_reserve_time(date, time)

def get_locked_reserves():
    conn = sqlite3.connect("tattoo_bot.db")
    cur = conn.cursor()
    cur.execute(
        "SELECT id, date, time, user_id, lock_until, receipt_file_id FROM reserve_times WHERE status='locked' AND lock_until>CURRENT_TIMESTAMP"
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def get_user_reserves(user_id):
    conn = sqlite3.connect("tattoo_bot.db")
    cur = conn.cursor()
    cur.execute(
        "SELECT date, time, status FROM reserve_times WHERE user_id=? ORDER BY date, time", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_all_dates():
    conn = sqlite3.connect("tattoo_bot.db")
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT date FROM reserve_times ORDER BY date")
    dates = [row[0] for row in cur.fetchall()]
    conn.close()
    return dates

def set_text(key, value):
    conn = sqlite3.connect("tattoo_bot.db")
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO texts (key, value) VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()

def get_text(key, default):
    conn = sqlite3.connect("tattoo_bot.db")
    cur = conn.cursor()
    cur.execute("SELECT value FROM texts WHERE key=?", (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else default

def set_ai_setting(key, value):
    conn = sqlite3.connect("tattoo_bot.db")
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO ai_setting (key,value) VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()

def get_ai_setting(key, default=None):
    conn = sqlite3.connect("tattoo_bot.db")
    cur = conn.cursor()
    cur.execute("SELECT value FROM ai_setting WHERE key=?", (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else default