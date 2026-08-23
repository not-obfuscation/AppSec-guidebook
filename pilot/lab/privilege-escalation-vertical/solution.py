"""Образцовое решение лабы: отказ по умолчанию и один разбор пути.

Отличий от code.py три, и каждое закрывает свой опыт эксплойта.

1. Право объявляется у маршрута (`role=`), а маршрут без объявления
   закрыт: функция, о которой забыли, недоступна никому. Опыт 1.
2. Путь приводится к канону один раз, до маршрутизации и до охраны,
   поэтому разбор у них общий. Опыт 2.
3. Изменяющая функция объявлена наравне с читающей и получает то же
   правило. Опыт 3.
"""

USERS = {
    "anna": {"role": "user"},
    "boris": {"role": "user"},
    "sysadmin": {"role": "admin"},
}

TICKETS = {
    1: {"owner": "anna", "text": "не открывается отчёт"},
    2: {"owner": "boris", "text": "нужен доступ к папке"},
}


class Denied(Exception):
    """Отказ в доступе. Диспетчер превращает его в ответ 403."""


def normalize(path):
    """Канон пути: один разбор на маршрутизацию и на охрану."""
    return "/" + path.strip("/").lower()


class App:
    def __init__(self):
        self.routes = {}
        self.policy = {}

    def route(self, path, methods=("GET",), role=None):
        """Право объявляется здесь же. Без `role` маршрут не заводится."""
        if role is None:
            raise ValueError(f"маршрут {path} без объявленного права")

        def register(handler):
            canon = normalize(path)
            for method in methods:
                self.routes[(canon, method)] = handler
            self.policy[canon] = role
            return handler
        return register

    def dispatch(self, request):
        canon = normalize(request["path"])
        handler = self.routes.get((canon, request["method"]))
        if handler is None:
            return {"status": 404, "body": None}
        try:
            guard(request, self.policy.get(canon))
            return handler(request)
        except Denied:
            return {"status": 403, "body": None}


app = App()


def guard(request, required):
    """Отказ по умолчанию: нет объявленного права — нет доступа."""
    if required is None:
        raise Denied
    if required == "any":
        return
    if USERS[request["user"]]["role"] != required:
        raise Denied


@app.route("/profile", role="any")
def profile(request):
    return {"status": 200, "body": {"login": request["user"]}}


@app.route("/tickets", role="any")
def tickets(request):
    mine = {k: v for k, v in TICKETS.items() if v["owner"] == request["user"]}
    return {"status": 200, "body": mine}


@app.route("/admin/users", role="admin")
def admin_users(request):
    return {"status": 200, "body": sorted(USERS)}


@app.route("/admin/tickets/delete", methods=("GET", "POST"), role="admin")
def admin_tickets_delete(request):
    TICKETS.pop(int(request["query"]["id"]), None)
    return {"status": 200, "body": "удалено"}


@app.route("/admin/export", role="admin")
def admin_export(request):
    """Выгрузка всех заявок. Заведена позже остальных."""
    return {"status": 200, "body": dict(TICKETS)}


def handle(user, path, method="GET", query=None):
    return app.dispatch({"user": user, "path": path,
                         "method": method, "query": query or {}})


def reset():
    TICKETS.clear()
    TICKETS.update({
        1: {"owner": "anna", "text": "не открывается отчёт"},
        2: {"owner": "boris", "text": "нужен доступ к папке"},
    })
