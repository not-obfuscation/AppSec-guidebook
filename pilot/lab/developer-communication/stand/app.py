#!/usr/bin/env python3
"""Стенд лабы developer-communication. Только 127.0.0.1, наружу не ходит.

Три случая, про которые пишутся заявки:
  Т-1  обработчик ошибок печатает текст исключения без экранирования;
  Т-2  комментарий FIXME на главной — приманка для правила «подозрительные
       комментарии»: находка инструмента есть, дефекта нет;
  Т-3  страница заказа не проверяет владельца.

Запуск: python3 app.py [порт], по умолчанию 8082.
"""
import html
import os
import sys
import threading
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

USERS = {
    "alice": {"password": "alice-pass", "uid": 1},
    "bob": {"password": "bob-pass", "uid": 2},
}
ORDERS = {
    101: {"uid": 1, "item": "чайник медный", "total": 2400},
    201: {"uid": 2, "item": "самовар", "total": 15400},
    301: {"uid": 2, "item": "служебная закупка", "total": 99000},
}
SESSIONS = {}
SEQ = [1000]
LOCK = threading.Lock()

PAGE = (
    "<!doctype html>\n<html lang=\"ru\"><head><meta charset=\"utf-8\">"
    "<title>%s — Лавка</title></head>\n<body>\n<h1>Лавка</h1>\n%s\n"
    "</body></html>\n"
)


class Lavka(BaseHTTPRequestHandler):
    server_version = "LavkaHTTP/0.9"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    def send_html(self, title, body, code=200):
        blob = (PAGE % (title, body)).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(blob)))
        self.end_headers()
        self.wfile.write(blob)

    def session(self):
        raw = self.headers.get("Cookie")
        if not raw:
            return None
        jar = SimpleCookie(raw)
        if "session" not in jar:
            return None
        return SESSIONS.get(jar["session"].value)

    def one(self, qs, name, default=""):
        return qs.get(name, [default])[0]

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        try:
            self.route(parsed.path, qs)
        except Exception as exc:      # Т-1: текст исключения уходит в разметку
            self.send_html("ошибка", "<pre>%s: %s</pre>" % (type(exc).__name__, exc), 500)

    def route(self, path, qs):
        if path == "/":
            return self.send_html(
                "главная",
                "<!-- FIXME: убрать тестовый вход перед релизом -->\n"
                "<p>Медная посуда и самовары.</p>\n"
                "<p><a href=\"/files?name=price.txt\">прайс</a></p>",
            )
        if path == "/files":
            name = self.one(qs, "name", "price.txt")
            with open(os.path.join(DATA, name), "rb") as fh:
                blob = fh.read()
            return self.send_html("файл", "<pre>%s</pre>" % html.escape(blob.decode("utf-8")))
        if path == "/order":
            rec = self.session()
            if not rec:
                return self.send_html("вход", "<p>Нужен вход.</p>", 401)
            oid = int(self.one(qs, "id", "0"))
            order = ORDERS.get(oid)
            if not order:
                return self.send_html("нет такого", "<p>Заказ не найден.</p>", 404)
            # Т-3: владелец заказа не проверяется
            return self.send_html(
                "заказ",
                "<p>Заказ %d: %s, %d ₽ (владелец uid=%d)</p>"
                % (oid, html.escape(order["item"]), order["total"], order["uid"]),
            )
        return self.send_html("нет такой страницы", "<p>404</p>", 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        params = parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)
        if urlparse(self.path).path != "/login":
            return self.send_html("нет такой страницы", "<p>404</p>", 404)
        login = params.get("login", [""])[0]
        rec = USERS.get(login)
        if not rec or rec["password"] != params.get("password", [""])[0]:
            return self.send_html("вход", "<p>Неверный логин или пароль.</p>", 401)
        with LOCK:
            SEQ[0] += 1
            sid = "lavka%d" % SEQ[0]
            SESSIONS[sid] = {"login": login, "uid": rec["uid"]}
        blob = (PAGE % ("вход", "<p>Здравствуйте, %s.</p>" % html.escape(login))).encode("utf-8")
        self.send_response(200)
        self.send_header("Set-Cookie", "session=%s; Path=/" % sid)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(blob)))
        self.end_headers()
        self.wfile.write(blob)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8082
    srv = ThreadingHTTPServer(("127.0.0.1", port), Lavka)
    print("Лавка на http://127.0.0.1:%d/" % port, flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
