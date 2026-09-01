"""Образцовое решение лабы: то же журналирование без секретов и подделок.

Разбор — в теме `security-logging`, блок «Как чинится». Здесь только код.
"""

import hashlib
import time

_USERS = {"anna": "qwerty2026", "boris": "Tg7#kLp2!wQa"}
_SESSIONS: dict[str, str] = {}
_LOG: list[str] = []


def _log(record: str) -> None:
    _LOG.append(record)


def _clean(text: str) -> str:
    """Убрать из данных символы, разбивающие запись журнала."""
    return text.replace("\r", "_").replace("\n", "_")


def _fingerprint(token: str) -> str:
    """Отпечаток токена: по нему находят запись, открыть ею нельзя."""
    return hashlib.sha256(token.encode()).hexdigest()[:8]


def login(user: str, password: str):
    """Вход; возвращает токен сессии или None при отказе."""
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    ok = _USERS.get(user) == password
    _log(f"{stamp} event=login user={_clean(user)} "
         f"result={'ok' if ok else 'fail'} password=***")
    if not ok:
        return None
    token = hashlib.sha256(f"{user}:{time.time()}".encode()).hexdigest()[:16]
    _SESSIONS[token] = user
    _log(f"{stamp} event=session user={_clean(user)} result=ok "
         f"token_fp={_fingerprint(token)}")
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
    """Очистить журнал и сессии."""
    _LOG.clear()
    _SESSIONS.clear()
