"""Стенд лабы: служба прав, хранилище счётчиков и набор запросов.

Сети нет, файлов не создаётся: всё живёт в памяти. Обе зависимости умеют
три состояния — жива, мертва и «отвечает, но не решением».
"""


class PolicyUnavailable(Exception):
    """Служба прав недоступна: соединение отвергнуто или таймаут."""


class StoreUnavailable(Exception):
    """Хранилище счётчиков недоступно."""


PRIVILEGED = {"delete_user", "export_all", "grant_admin", "refund"}
RATE_LIMIT = 5


class PolicyService:
    """Служба прав. Решение принимает она, приложение только спрашивает."""

    def __init__(self):
        self.state = "up"          # up | down | degraded
        self.calls = 0

    def check(self, user: dict, action: str) -> dict:
        self.calls += 1
        if self.state == "down":
            raise PolicyUnavailable("connection refused")
        if self.state == "degraded":
            # Служба жива, но решения не приняла: поля allow в ответе нет.
            return {"error": "policy engine warm-up", "retry_after": 5}
        allowed = user["role"] == "admin" or action not in PRIVILEGED
        return {"allow": allowed}


class CounterStore:
    """Хранилище счётчиков попыток входа, общее на все процессы."""

    def __init__(self):
        self.state = "up"
        self.counters = {}

    def incr(self, key: str) -> int:
        if self.state == "down":
            raise StoreUnavailable("connection refused")
        self.counters[key] = self.counters.get(key, 0) + 1
        return self.counters[key]


def new_world():
    return PolicyService(), CounterStore()
