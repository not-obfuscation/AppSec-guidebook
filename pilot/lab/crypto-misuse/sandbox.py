"""Стенд лабы: ключ приложения и разбор состояния сессии.

Сети нет, файлов вне временного каталога не создаётся: всё живёт в памяти.
"""

APP_KEY = bytes(range(16))            # ключ приложения, атакующему неизвестен
BLOCK = 16


def make_state(user: str, role: str, credit: int) -> str:
    """Состояние сессии до шифрования: три поля через точку с запятой."""
    return f"user={user};role={role};credit={credit}"


def parse_state(text: str) -> dict:
    out = {}
    for part in text.split(";"):
        if "=" in part:
            key, value = part.split("=", 1)
            out[key] = value
    return out
