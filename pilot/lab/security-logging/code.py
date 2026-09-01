"""Журналирование входа в админку учебной витрины.

Фрагмент учебного приложения, сведённый к одному вопросу: что попадает
в запись журнала. Журнал держится в памяти; dump_log() отдаёт ровно то,
что увидит тот, кто получил доступ к файлу журнала.

Лаборатория гайдбука. Всё исполняется локально, сети не требует и
никуда не обращается. Применимо только к этой лабе.

Задача: починить журналирование так, чтобы hack.py перестал
срабатывать, а tests.py продолжил проходить.
"""

import hashlib
import time

_USERS = {"anna": "qwerty2026", "boris": "Tg7#kLp2!wQa"}
_SESSIONS: dict[str, str] = {}
_LOG: list[str] = []


def _log(record: str) -> None:
    _LOG.append(record)


def login(user: str, password: str):
    """Вход; возвращает токен сессии или None при отказе."""
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    ok = _USERS.get(user) == password
    # УЯЗВИМО — демонстрация, не для продакшена
    _log(f"{stamp} event=login user={user} "
         f"result={'ok' if ok else 'fail'} password={password}")
    if not ok:
        return None
    token = hashlib.sha256(f"{user}:{time.time()}".encode()).hexdigest()[:16]
    _SESSIONS[token] = user
    # УЯЗВИМО — демонстрация, не для продакшена
    _log(f"{stamp} event=session user={user} result=ok token={token}")
    return token


def read_report(token: str):
    """Отчёт для владельца токена; чужому или пустому токену — None."""
    user = _SESSIONS.get(token)
    if user is None:
        return None
    return f"отчёт для {user}: продажи за неделю"


def dump_log() -> list[str]:
    """Содержимое журнала — то же, что уйдёт с ним при утечке."""
    return list(_LOG)


def reset() -> None:
    """Очистить журнал и сессии. Нужно тестам и повторным запускам."""
    _LOG.clear()
    _SESSIONS.clear()
