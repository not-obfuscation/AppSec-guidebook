#!/usr/bin/env python3
"""Функциональные проверки стенда: чинить дефекты, не ломая лавку.

Семь проверок того, что приложение продолжает работать. Запускаются на
поднятом стенде и никуда, кроме 127.0.0.1:8081, не ходят.

    ./stand.sh start
    python3 tests.py
"""
import http.cookiejar
import json
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


TESTS = []


def test(name):
    def wrap(fn):
        TESTS.append((name, fn))
        return fn

    return wrap


@test("каталог отдаёт две позиции категории «посуда»")
def t1():
    code, body = get("/catalog?cat=" + urllib.parse.quote("посуда"))
    return code == 200 and body.count("<li>") == 2 and "чайник медный" in body


@test("каталог отдаёт одну позицию категории «самовары»")
def t2():
    code, body = get("/catalog?cat=" + urllib.parse.quote("самовары"))
    return code == 200 and body.count("<li>") == 1


@test("поиск показывает, что искали")
def t3():
    code, body = get("/search?q=" + urllib.parse.quote("чайник"))
    return code == 200 and "чайник" in body


@test("прайс отдаётся целиком")
def t4():
    code, body = get("/files?name=price.txt")
    return code == 200 and "самовар тульский" in body


@test("вход работает и кабинет показывает два заказа")
def t5():
    post("/login", {"login": "alice", "password": "alice-pass"})
    code, body = get("/account")
    return code == 200 and body.count("/order?id=") == 2


@test("заметка сохраняется и читается обратно")
def t6():
    post("/login", {"login": "alice", "password": "alice-pass"})
    post("/profile", {"note": "заказать ещё меди"})
    code, body = get("/profile")
    return code == 200 and "заказать ещё меди" in body


@test("API отдаёт товары категории «самовары»")
def t7():
    code, body = get("/api/v1/products?filter=" + urllib.parse.quote("самовары"))
    if code != 200:
        return False
    try:
        rows = json.loads(body)
    except ValueError:
        return False
    return len(rows) == 1 and rows[0]["price"] == 15400


def main():
    try:
        get("/")
    except OSError:
        print("стенд не отвечает: сначала ./stand.sh start")
        return 2

    bad = 0
    for name, fn in TESTS:
        try:
            ok = fn()
        except Exception as exc:  # проверка упала — это тоже провал
            ok, name = False, f"{name} [{type(exc).__name__}]"
        bad += not ok
        print(f"{'ок  ' if ok else 'СБОЙ'}  {name}")
    print(f"\nпровалено: {bad} из {len(TESTS)}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
