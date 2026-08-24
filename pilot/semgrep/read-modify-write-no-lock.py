"""Тест-кейсы правила read-modify-write-no-lock.

Разметка: строка ruleid над ожидаемой находкой, строка ok над чистым местом.
"""

import sqlite3

conn = sqlite3.connect(":memory:")


def withdraw(amount):
    """Остаток прочитан, новый посчитан в приложении, записан присвоением."""
    balance = conn.execute("SELECT balance FROM acct WHERE id=1").fetchone()[0]
    if balance < amount:
        return "недостаточно средств"
    # ruleid: read-modify-write-no-lock
    conn.execute("UPDATE acct SET balance=? WHERE id=1", (balance - amount,))
    return "выдано"


def bump_counter():
    """Тот же порядок на счётчике: чтение, инкремент в Python, запись."""
    value = conn.execute("SELECT hits FROM page WHERE id=1").fetchone()[0]
    # ruleid: read-modify-write-no-lock
    conn.execute("UPDATE page SET hits=? WHERE id=1", (value + 1,))


def withdraw_atomic(amount):
    """Условие и новое значение — внутри одного UPDATE."""
    cursor = conn.execute(
        "UPDATE acct SET balance=balance-? WHERE id=1 AND balance>=?",
        (amount, amount))
    # ok: read-modify-write-no-lock
    return "выдано" if cursor.rowcount == 1 else "недостаточно средств"


def withdraw_locked(amount):
    """Строка взята под запись до чтения."""
    conn.execute("BEGIN IMMEDIATE")
    balance = conn.execute("SELECT balance FROM acct WHERE id=1").fetchone()[0]
    if balance >= amount:
        # ok: read-modify-write-no-lock
        conn.execute("UPDATE acct SET balance=? WHERE id=1",
                     (balance - amount,))
    conn.execute("COMMIT")


def rename_account(new_name):
    """Запись без предшествующего чтения гонкой этого вида не является."""
    # ok: read-modify-write-no-lock
    conn.execute("UPDATE acct SET name=? WHERE id=1", (new_name,))
