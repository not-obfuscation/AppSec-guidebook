#!/usr/bin/env python3
"""Стенд «Лавка» — намеренно уязвимое приложение для прогонов DAST.

Поднимается ТОЛЬКО на 127.0.0.1. Никаких внешних обращений не делает.
Что именно в нём подставлено, здесь не написано: это и есть задача.

Запуск:  python3 app.py [порт]
Среда:   SESSION_TTL   секунд жизни сессии, 0 — бессрочно (по умолчанию 0)
         ACCESS_LOG    путь к файлу журнала запросов
"""

import html
import http.cookies
import json
import os
import re
import sqlite3
import sys
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
SESSION_TTL = int(os.environ.get("SESSION_TTL", "0"))
ACCESS_LOG = os.environ.get("ACCESS_LOG", os.path.join(HERE, "access.log"))

USERS = {
    "alice": {"password": "alice-pass", "role": "user", "uid": 1},
    "bob": {"password": "bob-pass", "role": "user", "uid": 2},
    "admin": {"password": "admin-pass", "role": "admin", "uid": 3},
}

SESSIONS = {}
SESSION_SEQ = [1000]
LOCK = threading.Lock()
NOTES = {1: "", 2: "", 3: ""}
ORDERS = {
    101: {"uid": 1, "item": "чайник медный", "total": 2400},
    102: {"uid": 1, "item": "заварник", "total": 900},
    201: {"uid": 2, "item": "самовар", "total": 15400},
    202: {"uid": 2, "item": "поднос жестяной", "total": 700},
    301: {"uid": 3, "item": "служебная закупка", "total": 99000},
}


def db():
    con = sqlite3.connect(":memory:")
    con.executescript(
        """
        CREATE TABLE products (id INTEGER, cat TEXT, name TEXT, price INTEGER);
        INSERT INTO products VALUES (1,'посуда','чайник медный',2400);
        INSERT INTO products VALUES (2,'посуда','заварник',900);
        INSERT INTO products VALUES (3,'самовары','самовар тульский',15400);
        INSERT INTO products VALUES (4,'мелочь','поднос жестяной',700);
        CREATE TABLE staff (login TEXT, secret TEXT);
        INSERT INTO staff VALUES ('admin','sekret-lavka-2026');
        """
    )
    return con


PAGE = """<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><title>{title} — Лавка</title></head>
<body>
<h1>Лавка</h1>
<nav>
<a href="/">главная</a> |
<a href="/catalog?cat=%D0%BF%D0%BE%D1%81%D1%83%D0%B4%D0%B0">каталог</a> |
<a href="/search?q=%D1%87%D0%B0%D0%B9%D0%BD%D0%B8%D0%BA">поиск</a> |
<a href="/files?name=price.txt">прайс</a> |
{authlink}
</nav>
<hr>
{body}
</body></html>
"""


def log_line(text):
    try:
        with open(ACCESS_LOG, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")
    except OSError:
        pass


class Handler(BaseHTTPRequestHandler):
    server_version = "LavkaHTTP/0.9"
    sys_version = "Python/3.14.7"
    protocol_version = "HTTP/1.1"

    # -- служебное ---------------------------------------------------------

    def log_message(self, fmt, *args):
        rec = self.user()
        who = rec["login"] if rec else "-"
        log_line("%s\t%s\t%s" % (who, self.command, self.path))

    def send_page(self, body, code=200, title="Лавка", ctype="text/html; charset=utf-8"):
        raw = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def send_html(self, title, body, code=200):
        authlink = (
            '<a href="/account">кабинет</a> | <a href="/logout">выйти</a>'
            if self.user()
            else '<a href="/login">войти</a>'
        )
        self.send_page(PAGE.format(title=title, body=body, authlink=authlink), code, title)

    def send_json(self, obj, code=200):
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def query(self):
        parts = urllib.parse.urlsplit(self.path)
        return parts.path, urllib.parse.parse_qs(parts.query, keep_blank_values=True)

    def one(self, qs, key, default=""):
        return qs.get(key, [default])[0]

    def user(self):
        raw = self.headers.get("Cookie", "")
        jar = http.cookies.SimpleCookie()
        try:
            jar.load(raw)
        except http.cookies.CookieError:
            return None
        if "session" not in jar:
            return None
        with LOCK:
            rec = SESSIONS.get(jar["session"].value)
            if rec is None:
                return None
            if SESSION_TTL and time.time() - rec["born"] > SESSION_TTL:
                SESSIONS.pop(jar["session"].value, None)
                return None
        return rec

    def body_params(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8", "replace") if length else ""
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip()
        if ctype == "application/json":
            try:
                return json.loads(raw or "{}"), raw
            except ValueError:
                return {}, raw
        return {k: v[0] for k, v in urllib.parse.parse_qs(raw, keep_blank_values=True).items()}, raw

    # -- маршруты ----------------------------------------------------------

    def do_GET(self):
        path, qs = self.query()
        try:
            self.route_get(path, qs)
        except Exception as exc:
            self.send_html("ошибка", "<pre>%s: %s</pre>" % (type(exc).__name__, exc), 500)

    def do_POST(self):
        path, _ = self.query()
        try:
            self.route_post(path)
        except Exception as exc:
            self.send_html("ошибка", "<pre>%s: %s</pre>" % (type(exc).__name__, exc), 500)

    def do_PUT(self):
        self.do_POST()

    def route_get(self, path, qs):
        if path == "/":
            return self.send_html(
                "главная",
                "<!-- FIXME: подтянуть новые фото самоваров, старые с 2019 года -->"
                "<p>Медная посуда и самовары с 1998 года.</p>"
                "<p>Последний заказ в лавке: №1787619506.</p>"
                '<p><a href="/catalog?cat=%D1%81%D0%B0%D0%BC%D0%BE%D0%B2%D0%B0%D1%80%D1%8B">'
                "самовары</a></p>",
            )

        if path == "/search":
            q = self.one(qs, "q")
            return self.send_html(
                "поиск",
                "<p>Искали: %s</p><form action='/search'><input name='q'>"
                "<button>найти</button></form>" % q,
            )

        if path == "/catalog":
            cat = self.one(qs, "cat", "посуда")
            con = db()
            sql = "SELECT name, price FROM products WHERE cat = '%s'" % cat
            rows = con.execute(sql).fetchall()
            body = "<ul>" + "".join(
                "<li>%s — %d ₽</li>" % (html.escape(n), p) for n, p in rows
            ) + "</ul>"
            return self.send_html("каталог", body)

        if path == "/files":
            name = self.one(qs, "name", "price.txt")
            with open(os.path.join(DATA, name), "rb") as fh:
                blob = fh.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(blob)))
            self.end_headers()
            return self.wfile.write(blob)

        if path == "/login":
            return self.send_html(
                "вход",
                "<form method='post' action='/login'>"
                "<input name='login' placeholder='логин'>"
                "<input name='password' type='password' placeholder='пароль'>"
                "<button>войти</button></form>",
            )

        if path == "/logout":
            raw = self.headers.get("Cookie", "")
            jar = http.cookies.SimpleCookie()
            try:
                jar.load(raw)
                with LOCK:
                    SESSIONS.pop(jar["session"].value, None)
            except (http.cookies.CookieError, KeyError):
                pass
            return self.send_html("выход", "<p>Сессия закрыта.</p>")

        if path == "/account":
            rec = self.user()
            if not rec:
                return self.send_html("вход нужен", "<p>Сначала <a href='/login'>войдите</a>.</p>", 401)
            mine = [i for i, o in ORDERS.items() if o["uid"] == rec["uid"]]
            body = "<p>Здравствуйте, %s.</p><ul>%s</ul>" % (
                html.escape(rec["login"]),
                "".join("<li><a href='/order?id=%d'>заказ %d</a></li>" % (i, i) for i in mine),
            )
            body += "<p><a href='/profile'>заметка о себе</a></p>"
            body += "<p><a href='/admin/users'>список пользователей</a></p>"
            body += (
                "<form method='post' action='/cart/checkout'>"
                "<input name='item' value='чайник медный'>"
                "<input name='qty' value='1'>"
                "<button>оформить</button></form>"
            )
            return self.send_html("кабинет", body)

        if path == "/order":
            rec = self.user()
            if not rec:
                return self.send_html("вход нужен", "<p>Сначала войдите.</p>", 401)
            oid = int(self.one(qs, "id", "101") or 0)
            order = ORDERS.get(oid)
            if not order:
                return self.send_html("нет такого", "<p>Заказ не найден.</p>", 404)
            return self.send_html(
                "заказ",
                "<p>Заказ %d: %s, %d ₽ (владелец uid=%d)</p>"
                % (oid, html.escape(order["item"]), order["total"], order["uid"]),
            )

        if path == "/profile":
            rec = self.user()
            if not rec:
                return self.send_html("вход нужен", "<p>Сначала войдите.</p>", 401)
            note = NOTES.get(rec["uid"], "")
            return self.send_html(
                "заметка",
                "<div>%s</div><form method='post' action='/profile'>"
                "<input name='note'><button>сохранить</button></form>" % note,
            )

        if path == "/admin/users":
            rec = self.user()
            if not rec:
                return self.send_html("вход нужен", "<p>Сначала войдите.</p>", 401)
            body = "<table><tr><th>логин</th><th>роль</th></tr>" + "".join(
                "<tr><td>%s</td><td>%s</td></tr>" % (l, u["role"]) for l, u in USERS.items()
            ) + "</table>"
            return self.send_html("пользователи", body)

        if path == "/api/openapi.json":
            with open(os.path.join(HERE, "openapi.json"), "rb") as fh:
                blob = fh.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(blob)))
            self.end_headers()
            return self.wfile.write(blob)

        if path == "/api/v1/products":
            flt = self.one(qs, "filter", "посуда")
            con = db()
            sql = "SELECT id, name, price FROM products WHERE cat = '%s'" % flt
            rows = con.execute(sql).fetchall()
            return self.send_json([{"id": r[0], "name": r[1], "price": r[2]} for r in rows])

        m = re.match(r"^/api/v1/orders/(\d+)$", path)
        if m:
            rec = self.user()
            if not rec:
                return self.send_json({"error": "auth required"}, 401)
            order = ORDERS.get(int(m.group(1)))
            if not order:
                return self.send_json({"error": "not found"}, 404)
            return self.send_json({"id": int(m.group(1)), **order})

        if path == "/api/v1/reports":
            name = self.one(qs, "path", "sales.txt")
            with open(os.path.join(DATA, name), "rb") as fh:
                blob = fh.read()
            return self.send_json({"report": name, "text": blob.decode("utf-8", "replace")})

        if path == "/api/v1/whoami":
            rec = self.user()
            return self.send_json({"login": rec["login"], "role": rec["role"]} if rec else {"login": None})

        return self.send_html("нет страницы", "<p>404</p>", 404)

    def route_post(self, path):
        params, raw = self.body_params()

        if path == "/login":
            login = params.get("login", "")
            password = params.get("password", "")
            rec = USERS.get(login)
            if not rec or rec["password"] != password:
                return self.send_html("вход", "<p>Неверный логин или пароль.</p>", 401)
            with LOCK:
                SESSION_SEQ[0] += 1
                sid = "lavka%d" % SESSION_SEQ[0]
                SESSIONS[sid] = {
                    "login": login,
                    "uid": rec["uid"],
                    "role": rec["role"],
                    "born": time.time(),
                }
            self.send_response(302)
            self.send_header("Set-Cookie", "session=%s; Path=/" % sid)
            self.send_header("Location", "/account")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        if path == "/profile":
            rec = self.user()
            if not rec:
                return self.send_html("вход нужен", "<p>Сначала войдите.</p>", 401)
            NOTES[rec["uid"]] = params.get("note", "")
            return self.send_html("заметка", "<p>Сохранено.</p>")

        if path == "/cart/checkout":
            rec = self.user()
            if not rec:
                return self.send_html("вход нужен", "<p>Сначала войдите.</p>", 401)
            item = params.get("item", "чайник медный")
            try:
                qty = int(params.get("qty", "1"))
            except ValueError:
                qty = 1
            price = {"чайник медный": 2400, "заварник": 900, "самовар тульский": 15400}.get(item, 1000)
            total = price * qty
            return self.send_html(
                "заказ оформлен",
                "<p>%s × %d = <b>%d ₽</b></p>" % (html.escape(item), qty, total),
            )

        if path == "/api/v1/coupons/validate":
            code = params.get("code", "") if isinstance(params, dict) else ""
            return self.send_json({"code": code, "valid": code == "LAVKA2026"})

        return self.send_html("нет страницы", "<p>404</p>", 404)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print("Лавка на http://127.0.0.1:%d/ (SESSION_TTL=%d)" % (port, SESSION_TTL), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
