"""Уязвимое приложение: три решения при отказе зависимости, все три — пропуск.

Пока служба прав и хранилище счётчиков живы, приложение ведёт себя правильно.
Разница видна только на пути ошибки, а он тестами не покрыт.
"""

import sandbox


def authorize(policy, user, action):
    """Ответ обработчика на запрос действия: '200 <action>', '403' или '503'."""
    try:
        answer = policy.check(user, action)
    except Exception:
        # Отказ службы прав неотличим от разрешения: решение принято здесь.
        return "200 " + action
    if answer.get("allow", True):
        # Ответа «решение не принято» у разбора нет: умолчание разрешает.
        return "200 " + action
    return "403"


def login_attempt(store, login, password):
    """Возвращает True, если попытку входа пустили дальше проверки пароля."""
    try:
        used = store.incr("login:" + login)
    except Exception:
        # Счётчик недоступен — ограничитель частоты перестаёт существовать.
        return True
    return used <= sandbox.RATE_LIMIT
