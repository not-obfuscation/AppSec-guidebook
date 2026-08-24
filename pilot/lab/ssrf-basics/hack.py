"""Эксплойт лабы: пять адресов, по которым витрине ходить не положено.

Проверяет одно свойство: решает ли приложение само, куда уйдёт его
исходящий запрос. Запускается локально, к сети не обращается, против
чужих систем неприменим.

Код возврата:
    0 — эксплойт НЕ сработал (лаба починена)
    1 — эксплойт сработал (лаба ещё уязвима)
"""

import sys

from labtarget import load

LOOPBACK = "http://127.0.0.1:8080/admin/session"
INTERNAL = "http://10.0.7.5/invoices/7781"
METADATA = "http://169.254.169.254/latest/meta-data/iam/"
LOCALFILE = "file:///srv/app/.env"
REDIRECT = "http://partner.example/go"


def probe(lab, url, title, prize):
    """Один опыт: сходить по адресу и посмотреть, что вернулось."""
    resp = lab.handle(url)
    got = resp["status"] == 200
    print(f"  {title}: код {resp['status']}"
          f"{' — ' + prize if got else ''}")
    return got


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")
    hits = [
        probe(lab, LOOPBACK, "опыт 1 — петля, 127.0.0.1:8080",
              "СЕССИЯ АДМИНИСТРАТОРА ПОЛУЧЕНА"),
        probe(lab, INTERNAL, "опыт 2 — внутренняя сеть, 10.0.7.5",
              "ЧУЖОЙ СЧЁТ ПОЛУЧЕН"),
        probe(lab, METADATA, "опыт 3 — метаданные, 169.254.169.254",
              "КЛЮЧИ РОЛИ ПОЛУЧЕНЫ"),
        probe(lab, LOCALFILE, "опыт 4 — схема file:",
              "ФАЙЛ НАСТРОЕК ПОЛУЧЕН"),
        probe(lab, REDIRECT, "опыт 5 — партнёр ведёт внутрь",
              "КЛЮЧИ РОЛИ ЧЕРЕЗ ХОСТ СПИСКА"),
    ]
    control = probe(lab, "http://partner.example/catalog/42",
                    "опыт 6 — контроль, карточка партнёра",
                    "карточка отдана")
    print()
    if any(hits):
        print("ЭКСПЛОЙТ СРАБОТАЛ: витрина сходила туда, куда её "
              f"попросили ({sum(hits)} из 5 опытов)")
        return 1
    if not control:
        print("ЭКСПЛОЙТ НЕ СРАБОТАЛ, но контроль упал: карточка "
              "партнёра больше не отдаётся — это не починка")
        return 1
    print("эксплойт не сработал: все пять адресов отвергнуты, "
          "карточка партнёра отдаётся")
    return 0


if __name__ == "__main__":
    sys.exit(main())
