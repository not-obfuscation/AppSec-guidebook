"""УЯЗВИМЫЙ образец: кошелёк и промокод с проверкой отдельно от записи.

Оба обработчика читают состояние, решают и записывают решение тремя разными
запросами. Между чтением и записью лежит окно, в котором состояние успевает
измениться.

Демонстрация для лабы, не для продакшена.
"""

import sqlite3

import sandbox

SCHEMA_UNIQUE_REDEEM = False


def withdraw(amount):
    """Снятие со счёта: проверка остатка и списание — два запроса."""
    conn = sandbox.connect()
    try:
        balance = conn.execute(
            "SELECT balance FROM acct WHERE id=1").fetchone()[0]
        if balance < amount:
            return "недостаточно средств"
        conn.execute("UPDATE acct SET balance=? WHERE id=1",
                     (balance - amount,))
        return "выдано"
    except sqlite3.OperationalError:
        return "база занята"
    finally:
        conn.close()


def redeem(code, user):
    """Одноразовый промокод: проверка, начисление, отметка — три запроса."""
    conn = sandbox.connect()
    try:
        row = conn.execute("SELECT used FROM promo WHERE code=?",
                           (code,)).fetchone()
        if row is None:
            return "код не найден"
        if row[0]:
            return "код уже использован"
        conn.execute("INSERT INTO redeem VALUES (?,?)", (code, user))
        conn.execute("UPDATE promo SET used=1 WHERE code=?", (code,))
        return "скидка начислена"
    except sqlite3.OperationalError:
        return "база занята"
    finally:
        conn.close()
