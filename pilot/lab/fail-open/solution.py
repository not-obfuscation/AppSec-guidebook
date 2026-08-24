"""Образец починки: у проверки три исхода, и каждый обработан своей веткой.

Отказ зависимости больше не путается ни с разрешением, ни с запретом:
приложение отвечает 503 и записывает событие. Ограничитель частоты переходит
на локальный счётчик того же лимита, а не исчезает.
"""

import sandbox

AUDIT = []          # события безопасности: срабатывание запасного пути
_LOCAL = {}         # счётчик попыток на время отказа хранилища


def authorize(policy, user, action):
    """Ответ обработчика на запрос действия: '200 <action>', '403' или '503'."""
    try:
        answer = policy.check(user, action)
    except sandbox.PolicyUnavailable as exc:
        AUDIT.append(f"policy unavailable: {exc}")
        return "503"
    if "allow" not in answer:
        AUDIT.append(f"policy returned no decision: {answer}")
        return "503"
    return "200 " + action if answer["allow"] else "403"


def login_attempt(store, login, password):
    """Возвращает True, если попытку входа пустили дальше проверки пароля."""
    key = "login:" + login
    try:
        used = store.incr(key)
    except sandbox.StoreUnavailable as exc:
        AUDIT.append(f"counter store unavailable: {exc}")
        _LOCAL[key] = _LOCAL.get(key, 0) + 1
        used = _LOCAL[key]
    return used <= sandbox.RATE_LIMIT
