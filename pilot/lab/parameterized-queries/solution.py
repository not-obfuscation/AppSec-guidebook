"""Образцовое решение лабы parameterized-queries.

Список id переменной длины передаётся связанными параметрами: под каждый
элемент — свой заполнитель `?`, значения едут отдельным аргументом. Текст
запроса не собирается из данных. Остальное — как в code.py.

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


def by_category(category):
    cur = _conn().cursor()
    cur.execute(
        "SELECT id, name, price FROM products "
        "WHERE category = ? AND released = 1",
        (category,))
    return cur.fetchall()


def by_ids(ids):
    """Карточки выбранных товаров: заполнитель на каждый элемент списка."""
    cur = _conn().cursor()
    if not ids:
        return []
    placeholders = ",".join("?" for _ in ids)              # (1)
    query = (
        "SELECT id, name, price FROM products "
        "WHERE released = 1 AND id IN (" + placeholders + ")"
    )
    cur.execute(query, tuple(ids))                         # (2)
    return cur.fetchall()


def reset():
    global _DB
    _DB = sqlite3.connect(":memory:")
    cur = _DB.cursor()
    cur.execute("CREATE TABLE products "
                "(id INTEGER, category TEXT, name TEXT, "
                "price INTEGER, released INTEGER)")
    cur.executemany(
        "INSERT INTO products VALUES (?, ?, ?, ?, ?)",
        [(1, "Gifts", "Открытка", 200, 1),
         (2, "Gifts", "Букет", 1500, 1),
         (3, "Gifts", "Подарок к запуску", 9900, 0),
         (4, "Tech", "Наушники", 4500, 1),
         (5, "Tech", "Секретный прототип", 120000, 0)])
    _DB.commit()
