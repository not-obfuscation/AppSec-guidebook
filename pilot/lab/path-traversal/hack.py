"""Эксплойт лабы path-traversal: выход за базовый каталог выдачи.

Служба сверяет собранный путь с базовым каталогом, но делает это до того, как
из пути убраны переходы вверх. Строка вида `../service.env` проверку проходит,
а открывается уже снаружи. Тем же способом наружу выводит символическая
ссылка, лежащая внутри базового каталога.

Локально, к сети не обращается, против чужих систем неприменимо.

Код возврата:
    0 — эксплойт НЕ сработал (за базовый каталог выйти не удалось)
    1 — эксплойт сработал (файл снаружи прочитан)
"""

import sys

import sandbox
from labtarget import load


def _leaked(text):
    """Признак утечки: в ответе видно содержимое файла снаружи."""
    return sandbox.SECRET_LINE.split("=")[0] in text


def experiment_1_dotdot(lab):
    """Переход вверх из базового каталога."""
    try:
        body = lab.read_document("../service.env")
    except (OSError, PermissionError, ValueError) as e:
        print(f"  опыт 1 — ../service.env: отказ ({type(e).__name__})")
        return False
    got = _leaked(body)
    print(f"  опыт 1 — ../service.env: "
          f"{'ПРОЧИТАН ' + body.strip() if got else 'пусто'}")
    return got


def experiment_2_from_subdir(lab):
    """Переход вверх из законного подкаталога."""
    try:
        body = lab.read_document("archive/../../service.env")
    except (OSError, PermissionError, ValueError) as e:
        print(f"  опыт 2 — archive/../../service.env: "
              f"отказ ({type(e).__name__})")
        return False
    got = _leaked(body)
    print(f"  опыт 2 — archive/../../service.env: "
          f"{'ПРОЧИТАН ' + body.strip() if got else 'пусто'}")
    return got


def experiment_3_symlink(lab):
    """Символическая ссылка внутри базового каталога ведёт наружу."""
    try:
        body = lab.read_document("notes.txt")
    except (OSError, PermissionError, ValueError) as e:
        print(f"  опыт 3 — notes.txt (ссылка наружу): "
              f"отказ ({type(e).__name__})")
        return False
    got = _leaked(body)
    print(f"  опыт 3 — notes.txt (ссылка наружу): "
          f"{'ПРОЧИТАН ' + body.strip() if got else 'пусто'}")
    return got


def experiment_4_control_read(lab):
    """Контроль на живучесть: законный документ по-прежнему отдаётся."""
    try:
        body = lab.read_document("invoice-2026-01.txt")
        ok = "январь" in body
    except Exception:
        ok = False
    print(f"  опыт 4 — контроль, законный invoice-2026-01.txt: "
          f"{'отдан' if ok else 'ПОЧИНКА СЛОМАЛА ВЫДАЧУ'}")
    return ok


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")
    print(f"базовый каталог: {sandbox.base()}")
    print(f"файл снаружи:    {sandbox.secret_path()}")
    print()
    leaks = [
        experiment_1_dotdot(lab),
        experiment_2_from_subdir(lab),
        experiment_3_symlink(lab),
    ]
    control = experiment_4_control_read(lab)
    print()
    if any(leaks):
        print(f"ЭКСПЛОЙТ СРАБОТАЛ: файл снаружи базового каталога прочитан "
              f"({sum(leaks)} из 3 опытов)")
        return 1
    if not control:
        print("ЭКСПЛОЙТ НЕ СРАБОТАЛ, но контроль упал: выдача перестала "
              "работать")
        return 1
    print("эксплойт не сработал: за базовый каталог выйти не удалось, "
          "законная выдача работает")
    return 0


if __name__ == "__main__":
    sys.exit(main())
