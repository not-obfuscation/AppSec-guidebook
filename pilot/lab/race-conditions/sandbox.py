"""Стенд лабы: база во временном каталоге, счёт и одноразовый промокод.

Сети нет, ничего вне временного каталога не создаётся.
"""

import atexit
import os
import shutil
import sqlite3
import tempfile

START_BALANCE = 100
PROMO_CODE = "SALE"

_dir = tempfile.mkdtemp(prefix="lab-race-")
atexit.register(shutil.rmtree, _dir, ignore_errors=True)
DB = os.path.join(_dir, "wallet.db")


def connect(timeout=5):
    conn = sqlite3.connect(DB, isolation_level=None, timeout=timeout)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def reset(unique_redeem=False):
    """Свежая база перед каждым опытом."""
    conn = connect()
    conn.executescript("""
        DROP TABLE IF EXISTS acct;
        DROP TABLE IF EXISTS promo;
        DROP TABLE IF EXISTS redeem;
        CREATE TABLE acct(id INTEGER PRIMARY KEY, balance INTEGER);
        CREATE TABLE promo(code TEXT PRIMARY KEY, used INTEGER);
    """)
    if unique_redeem:
        conn.execute("CREATE TABLE redeem(code TEXT, user TEXT,"
                     " UNIQUE(code, user))")
    else:
        conn.execute("CREATE TABLE redeem(code TEXT, user TEXT)")
    conn.execute("INSERT INTO acct VALUES (1, ?)", (START_BALANCE,))
    conn.execute("INSERT INTO promo VALUES (?, 0)", (PROMO_CODE,))
    conn.close()


def balance():
    conn = connect()
    value = conn.execute("SELECT balance FROM acct WHERE id=1").fetchone()[0]
    conn.close()
    return value


def redemptions():
    conn = connect()
    value = conn.execute("SELECT count(*) FROM redeem").fetchone()[0]
    conn.close()
    return value
