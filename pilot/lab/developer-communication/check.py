#!/usr/bin/env python3
"""Проверялка заявок: повторяет шаги из текста заявки на стенде.

Запуск из каталога лабы (стенд должен быть поднят):
    ./stand.sh start
    ../../../.venv-tools/bin/python check.py

Код возврата 0 — зачтено (все три заявки прошли), 1 — нет.
Сети не требует: единственный адрес — 127.0.0.1:8082.
"""
import http.cookiejar
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

import yaml

BASE = "http://127.0.0.1:8082"
HERE = pathlib.Path(__file__).parent
NEEDED = ["Вердикт", "Шаги", "Ожидалось", "Получено", "Влияние", "Предложение", "Срок"]


def sections(text):
    """Разбить заявку на разделы по заголовкам второго уровня."""
    out, name, buf = {}, None, []
    for line in text.splitlines():
        head = re.match(r"^##\s+(.+?)\s*$", line)
        if head:
            if name:
                out[name] = "\n".join(buf).strip()
            name, buf = head.group(1), []
        elif name:
            buf.append(line)
    if name:
        out[name] = "\n".join(buf).strip()
    return out


def steps_of(block):
    """Строки вида `METHOD PATH [тело]` из ограждённого листинга раздела."""
    fenced = re.findall(r"```[a-z]*\n(.*?)```", block, re.S)
    body = fenced[0] if fenced else block
    steps = []
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 2)
        if len(parts) < 2 or parts[0] not in ("GET", "POST"):
            continue
        steps.append((parts[0], parts[1], parts[2] if len(parts) > 2 else ""))
    return steps


def replay(steps):
    """Повторить шаги одной сессией и вернуть тело последнего ответа."""
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    last = ""
    for method, path, payload in steps:
        url = BASE + urllib.parse.quote(path, safe="/?&=%:+")
        data = payload.encode("utf-8") if method == "POST" else None
        req = urllib.request.Request(url, data=data, method=method)
        if data is not None:
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
        try:
            with opener.open(req, timeout=10) as resp:
                last = resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as err:
            last = err.read().decode("utf-8", "replace")
        except OSError as err:
            print(f"    стенд не отвечает: {err}")
            return None
    return last


def check_one(entry):
    path = HERE / "tickets" / entry["файл"]
    print(f"== {entry['файл']}")
    if not path.exists():
        print("    заявки нет")
        return False
    parts = sections(path.read_text(encoding="utf-8"))
    missing = [n for n in NEEDED if not parts.get(n) or "⟨" in parts[n]]
    if missing:
        print("    не заполнены разделы: " + ", ".join(missing))
        return False
    verdict = parts["Вердикт"].strip().lower()
    if verdict != entry["вердикт"]:
        print(f"    вердикт «{verdict}», в ключе «{entry['вердикт']}»")
        return False
    steps = steps_of(parts["Шаги"])
    if not steps:
        print("    в разделе «Шаги» нет ни одной строки вида «GET /путь»")
        return False
    body = replay(steps)
    if body is None:
        return False
    if entry["признак"] not in body:
        print(f"    шаги повторены ({len(steps)}), но в ответе нет «{entry['признак']}»:")
        print("    заявка не воспроизводится по собственному тексту")
        return False
    print(f"    шаги повторены ({len(steps)}), признак «{entry['признак']}» в ответе есть")
    return True


def main():
    key = yaml.safe_load((HERE / "key.yaml").read_text(encoding="utf-8"))["key"]
    good = sum(1 for entry in key if check_one(entry))
    print(f"\nпрошло {good} из {len(key)}")
    if good == len(key):
        print("зачтено")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
