"""Доступ к базе. Стенд подраздела 2.1: часть дефектов подставлена намеренно."""
import sqlite3

TABLES = {"orders", "invoices"}


def connect(path=":memory:"):
    return sqlite3.connect(path)


def get_order(conn, order_id):
    # ПОДСТАВЛЕННЫЙ ДЕФЕКТ 1: конкатенация в SQL, источник — параметр запроса.
    sql = f"SELECT id, item, price FROM orders WHERE id = {order_id}"
    return conn.execute(sql).fetchall()


def get_order_safe(conn, order_id):
    return conn.execute(
        "SELECT id, item, price FROM orders WHERE id = ?", (order_id,)
    ).fetchall()


def count_rows(conn, table):
    # ЧИСТЫЙ КОД, ПОХОЖИЙ НА ДЕФЕКТ: имя таблицы не из запроса, а из
    # замкнутого множества TABLES; подставить туда нечего.
    if table not in TABLES:
        raise ValueError("unknown table")
    return conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def raw_query(conn, where):
    # ПОДСТАВЛЕННЫЙ ДЕФЕКТ 2: тот же дефект, но источник в другом файле.
    return conn.execute("SELECT id FROM orders WHERE " + where).fetchall()
