"""Сравнение товаров: выборка нескольких товаров по списку идентификаторов.

Функция витрины «сравнить выбранное»: приходит список id из корзины, надо
вернуть их карточки. Значение одной категории подставляется правильно —
связанным параметром. А список id собран в запрос склейкой, потому что
«параметром список переменной длины не передать». Это и есть дефект темы:
границу применимости параметра приняли за повод вернуться к склейке.

База — SQLite в памяти, сети не требуется, HTTP не поднимается.

Лаборатория гайдбука. Всё исполняется локально и применимо только к
этой лабе.

Задача: передать список id связанными параметрами, не собирая его в
текст запроса склейкой.
"""

import sqlite3

_DB = None


def _conn():
    global _DB
    if _DB is None:
        reset()
    return _DB


def by_category(category):
    """Товары категории. Значение подставлено правильно — параметром."""
    cur = _conn().cursor()
    cur.execute(
        "SELECT id, name, price FROM products "
        "WHERE category = ? AND released = 1",
        (category,))
    return cur.fetchall()


# УЯЗВИМО — демонстрация, не для продакшена.
def by_ids(ids):
    """Карточки выбранных товаров по списку id.

    id приходят строками из запроса и склеиваются в список IN. Любая
    строка в списке становится частью команды.
    """
    cur = _conn().cursor()
    in_list = ",".join(ids)                                # (1)
    query = (
        "SELECT id, name, price FROM products "
        "WHERE released = 1 AND id IN (" + in_list + ")"   # (2)
    )
    cur.execute(query)
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
