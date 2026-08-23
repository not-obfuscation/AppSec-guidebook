"""Внутренний портал заявок: маршруты, роли и охрана перед запросом.

Фрагмент сервиса, сведённый к одному вопросу: кто попадает в
административные функции. Хранилище держится в памяти, сети не
требуется, HTTP не поднимается — запрос представлен словарём.

Лаборатория гайдбука. Всё исполняется локально и применимо только к
этой лабе.

Задача: починить контроль доступа так, чтобы hack.py перестал
срабатывать, а tests.py продолжил проходить.
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


class App:
    """Мини-маршрутизатор: путь и метод к обработчику."""

    def __init__(self):
        self.routes = {}

    def route(self, path, methods=("GET",)):
        def register(handler):
            for method in methods:
                self.routes[(path.lower(), method)] = handler
            return handler
        return register

    def dispatch(self, request):
        # Путь приводится к нижнему регистру: так делает большинство
        # маршрутизаторов, и это часть задачи.
        key = (request["path"].lower(), request["method"])
        handler = self.routes.get(key)
        if handler is None:
            return {"status": 404, "body": None}
        try:
            guard(request)
            return handler(request)
        except Denied:
            return {"status": 403, "body": None}


app = App()

# УЯЗВИМО — демонстрация, не для продакшена.
# Список закрытых путей. Всё, чего в нём нет, открыто всем вошедшим.
PROTECTED = {"/admin/users", "/admin/tickets/delete"}


def guard(request):
    """Охрана перед запросом: сверка пути со списком закрытых."""
    if request["path"] in PROTECTED:
        if USERS[request["user"]]["role"] != "admin":
            raise Denied


@app.route("/profile")
def profile(request):
    return {"status": 200, "body": {"login": request["user"]}}


@app.route("/tickets")
def tickets(request):
    mine = {k: v for k, v in TICKETS.items() if v["owner"] == request["user"]}
    return {"status": 200, "body": mine}


@app.route("/admin/users")
def admin_users(request):
    return {"status": 200, "body": sorted(USERS)}


@app.route("/admin/tickets/delete", methods=("GET", "POST"))
def admin_tickets_delete(request):
    TICKETS.pop(int(request["query"]["id"]), None)
    return {"status": 200, "body": "удалено"}


@app.route("/admin/export")
def admin_export(request):
    """Выгрузка всех заявок. Заведена позже остальных."""
    return {"status": 200, "body": dict(TICKETS)}


def handle(user, path, method="GET", query=None):
    """Единая точка входа лабы: собрать запрос и отдать его диспетчеру."""
    return app.dispatch({"user": user, "path": path,
                         "method": method, "query": query or {}})


def reset():
    TICKETS.clear()
    TICKETS.update({
        1: {"owner": "anna", "text": "не открывается отчёт"},
        2: {"owner": "boris", "text": "нужен доступ к папке"},
    })
