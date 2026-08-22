"""Учётные записи сервиса заявок на доступ: регистрация и вход.

Фрагмент внутреннего сервиса, сведённый к одному вопросу: в каком виде
лежит пароль. Хранилище держится в памяти; export_dump() отдаёт ровно
то, что увидит атакующий, получивший резервную копию базы.

Лаборатория гайдбука. Всё исполняется локально, сети не требует и
никуда не обращается. Применимо только к этой лабе.

Задача: починить хранение так, чтобы hack.py перестал срабатывать,
а tests.py продолжил проходить.
"""

import hashlib

_STORE: dict[str, str] = {}


def register(login: str, password: str) -> None:
    """Завести учётную запись."""
    # УЯЗВИМО — демонстрация, не для продакшена
    _STORE[login] = hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify(login: str, password: str) -> bool:
    """Проверить пару логин-пароль."""
    stored = _STORE.get(login)
    if stored is None:
        return False
    # УЯЗВИМО — демонстрация, не для продакшена
    candidate = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return candidate == stored


def load_legacy(login: str, sha256_hex: str) -> None:
    """Внести запись из старой базы: голый SHA-256 без соли.

    Так выглядят учётные записи, заведённые предыдущей версией
    сервиса. Они уже есть в проде, и трогать их нечем: исходных
    паролей ни у кого нет.
    """
    _STORE[login] = sha256_hex


def export_dump() -> list[tuple[str, str]]:
    """Содержимое таблицы — то же, что уйдёт с резервной копией."""
    return sorted(_STORE.items())


def reset() -> None:
    """Очистить хранилище. Нужно тестам и повторным запускам."""
    _STORE.clear()
