"""Образцовое решение лабы sqli-basics: запросы на параметрах.

Текст запроса — постоянная строка, данные приходят отдельно связанными
параметрами. База различает код и данные независимо от того, что
прислали. Остальное — как в code.py.

Лаборатория гайдбука. Всё исполняется локально и применимо только к
этой лабе.
"""

import sqlite3

_DB = None


def _conn():
    global _DB
    if _DB is None:
        reset()
    return _DB


def search_products(category):
    """Список выпущенных товаров категории."""
    cur = _conn().cursor()
    cur.execute(
        "SELECT name, price FROM products "
        "WHERE category = ? AND released = 1",
        (category,))
    return cur.fetchall()


def login(username, password):
    """Вход по имени и паролю. Возвращает роль или None."""
    cur = _conn().cursor()
    cur.execute(
        "SELECT username, role FROM users "
        "WHERE username = ? AND password = ?",
        (username, password))
    row = cur.fetchone()
    return None if row is None else {"username": row[0], "role": row[1]}


def reset():
    global _DB
    _DB = sqlite3.connect(":memory:")
    cur = _DB.cursor()
    cur.execute("CREATE TABLE products "
                "(id INTEGER, category TEXT, name TEXT, "
                "price INTEGER, released INTEGER)")
    cur.execute("CREATE TABLE users "
                "(username TEXT, password TEXT, role TEXT)")
    cur.executemany(
        "INSERT INTO products VALUES (?, ?, ?, ?, ?)",
        [(1, "Gifts", "Открытка", 200, 1),
         (2, "Gifts", "Букет", 1500, 1),
         (3, "Gifts", "Подарок к запуску", 9900, 0),
         (4, "Tech", "Наушники", 4500, 1)])
    cur.executemany(
        "INSERT INTO users VALUES (?, ?, ?)",
        [("wiener", "peter", "user"),
         ("administrator", "s3cr3t-9f2a", "admin")])
    _DB.commit()
