"""Витрина каталога: поиск товаров по категории и вход в кабинет.

Фрагмент интернет-магазина, сведённый к одному вопросу: как строится
текст запроса SQL. База — SQLite в памяти, сети не требуется, HTTP не
поднимается. Оба запроса собираются склейкой строк, и это и есть
дефект темы.

Лаборатория гайдбука. Всё исполняется локально и применимо только к
этой лабе.

Задача: перевести запросы на параметры так, чтобы hack.py перестал
срабатывать, а tests.py продолжил проходить.
"""

import sqlite3

_DB = None


def _conn():
    """Соединение с базой в памяти. Живёт до reset()."""
    global _DB
    if _DB is None:
        reset()
    return _DB


# УЯЗВИМО — демонстрация, не для продакшена.
def search_products(category):
    """Список выпущенных товаров категории.

    Возвращает список пар (название, цена).
    """
    cur = _conn().cursor()
    query = (
        "SELECT name, price FROM products "
        "WHERE category = '" + category + "' AND released = 1"
    )
    cur.execute(query)
    return cur.fetchall()


# УЯЗВИМО — демонстрация, не для продакшена.
def login(username, password):
    """Вход по имени и паролю. Возвращает роль или None."""
    cur = _conn().cursor()
    query = (
        "SELECT username, role FROM users "
        "WHERE username = '" + username + "' "
        "AND password = '" + password + "'"
    )
    cur.execute(query)
    row = cur.fetchone()
    return None if row is None else {"username": row[0], "role": row[1]}


def reset():
    """Пересоздать базу в исходном виде."""
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
