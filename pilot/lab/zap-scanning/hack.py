#!/usr/bin/env python3
"""Повтор полезных нагрузок, которыми ZAP нашёл на стенде дефекты высокого риска.

Шесть проб, все против http://127.0.0.1:8081 и только против него. Скрипт
ничего не чинит: он печатает, какие пробы всё ещё проходят.

    ./stand.sh start
    python3 hack.py
"""
import http.cookiejar
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8081"
JAR = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(JAR))


def get(path):
    try:
        with OPENER.open(BASE + path, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8", "replace")


def post(path, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(BASE + path, data=body, method="POST")
    try:
        with OPENER.open(req, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8", "replace")


def login():
    post("/login", {"login": "alice", "password": "alice-pass"})


PROBES = []


def probe(name):
    def wrap(fn):
        PROBES.append((name, fn))
        return fn

    return wrap


@probe("отражённая XSS в поиске")
def p1():
    _, body = get("/search?q=" + urllib.parse.quote("</p><scrIpt>alert(1);</scRipt><p>"))
    return "<scrIpt>alert(1);</scRipt>" in body


@probe("отражение полезной нагрузки на странице ошибки (/files)")
def p2():
    _, body = get("/files?name=" + urllib.parse.quote("<script>alert(1)</script>"))
    return "<script>alert(1)</script>" in body


@probe("отражение полезной нагрузки на странице ошибки (/order)")
def p3():
    login()
    _, body = get("/order?id=" + urllib.parse.quote("<script>alert(1)</script>"))
    return "<script>alert(1)</script>" in body


@probe("хранимая XSS в заметке")
def p4():
    login()
    post("/profile", {"note": '<img src=x onerror=alert(1)>'})
    _, body = get("/profile")
    return "<img src=x onerror=alert(1)>" in body


@probe("обход каталога в /files")
def p5():
    _, body = get("/files?name=" + urllib.parse.quote("/etc/passwd"))
    return "root:x:0:0" in body


@probe("SQL-инъекция в каталоге")
def p6():
    code, body = get("/catalog?cat=" + urllib.parse.quote("посуда' OR '1'='1"))
    # признак: запрос вернул больше строк, чем есть в категории «посуда»
    return code == 200 and body.count("<li>") > 2


def main():
    try:
        get("/")
    except OSError:
        print("стенд не отвечает: сначала ./stand.sh start")
        return 2

    alive = 0
    for name, fn in PROBES:
        ok = fn()
        alive += ok
        print(f"{'ПРОХОДИТ' if ok else 'закрыта '}  {name}")
    print(f"\nпроб проходит: {alive} из {len(PROBES)}")
    return 0 if alive == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
