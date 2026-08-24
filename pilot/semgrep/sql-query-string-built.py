"""Тест-кейсы правила sql-query-string-built.

Маркер стоит строкой выше ожидаемой находки: `ruleid:` — правило
обязано сработать, `ok:` — обязано промолчать. Сверка:

    .venv-tools/bin/python pilot/semgrep/check.py sql-query
"""


class _Cur:
    def execute(self, *a):
        return a

    def executemany(self, *a):
        return a


cur = _Cur()


# --- ловит -----------------------------------------------------------

def search_concat(category):
    query = "SELECT name FROM products WHERE category = '" + category + "'"
    # ruleid: sql-query-string-built
    cur.execute(query)


def search_fstring(category):
    # ruleid: sql-query-string-built
    cur.execute(f"SELECT name FROM products WHERE category = '{category}'")


def search_percent(category):
    query = "SELECT name FROM products WHERE category = '%s'" % category
    # ruleid: sql-query-string-built
    cur.execute(query)


def search_format(category):
    # ruleid: sql-query-string-built
    cur.execute("SELECT name FROM products WHERE category = '{}'".format(category))


def bulk_concat(rows, suffix):
    query = "INSERT INTO products VALUES (?, ?)" + suffix
    # ruleid: sql-query-string-built
    cur.executemany(query, rows)


# --- молчит ----------------------------------------------------------

def search_param(category):
    # Текст запроса постоянный, данные — связанным параметром.
    # ok: sql-query-string-built
    cur.execute("SELECT name FROM products WHERE category = ?", (category,))


def search_adjacent(category):
    # Склейка соседних строковых литералов, данных в тексте нет.
    # ok: sql-query-string-built
    cur.execute(
        "SELECT name FROM products "
        "WHERE category = ? AND released = 1",
        (category,))


def bulk_param(rows):
    # Постоянный текст, значения — списком кортежей.
    # ok: sql-query-string-built
    cur.executemany("INSERT INTO products VALUES (?, ?)", rows)
