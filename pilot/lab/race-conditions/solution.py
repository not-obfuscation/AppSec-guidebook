"""Образец починки: решение и запись — одна операция хранилища.

Снятие — условный UPDATE: условие остатка стоит в самом запросе, а решение
принимается по числу затронутых строк. Промокод — уникальный ключ в схеме:
второе начисление отвергает база, а не приложение.
"""

import sqlite3

import sandbox

SCHEMA_UNIQUE_REDEEM = True


def withdraw(amount):
    """Проверка остатка живёт внутри UPDATE, отдельного чтения нет."""
    conn = sandbox.connect()
    try:
        cursor = conn.execute(
            "UPDATE acct SET balance=balance-? WHERE id=1 AND balance>=?",
            (amount, amount))
        return "выдано" if cursor.rowcount == 1 else "недостаточно средств"
    except sqlite3.OperationalError:
        return "база занята"
    finally:
        conn.close()


def redeem(code, user):
    """Отметка ставится первой операцией; повтор отвергает уникальный ключ."""
    conn = sandbox.connect()
    try:
        if conn.execute("SELECT 1 FROM promo WHERE code=?",
                        (code,)).fetchone() is None:
            return "код не найден"
        try:
            conn.execute("INSERT INTO redeem VALUES (?,?)", (code, user))
        except sqlite3.IntegrityError:
            return "код уже использован"
        conn.execute("UPDATE promo SET used=1 WHERE code=?", (code,))
        return "скидка начислена"
    except sqlite3.OperationalError:
        return "база занята"
    finally:
        conn.close()
