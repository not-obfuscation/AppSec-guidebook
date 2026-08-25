#!/usr/bin/env python3
"""Проверялка лабы supply-chain-threats.

Задача «почини»: закрепить установку так, чтобы shop-telemetry снова брался из
внутреннего индекса (версия 1.0.0, источник internal), несмотря на публичный
индекс с версией 9.9.9. Ученик правит fix.sh; проверялка запускает его и
сверяет установленный источник.

Запуск из каталога лабы:
    python3 check.py
Код возврата 0 — фикс закрыл подмену, 1 — нет.
"""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).parent


def run(script):
    p = subprocess.run(["bash", str(HERE / script)], capture_output=True, text=True)
    return p.stdout + p.stderr


def installed():
    venv = "/tmp/sc-lab-fix-venv"
    py = pathlib.Path(venv) / "bin" / "python"
    if not py.exists():
        return None, None
    ver = subprocess.run([str(py), "-c",
                          "import importlib.metadata as m;print(m.version('shop-telemetry'))"],
                         capture_output=True, text=True).stdout.strip()
    org = subprocess.run([str(py), "-c", "import shop_telemetry as s;print(s.ORIGIN)"],
                         capture_output=True, text=True).stdout.strip()
    return ver, org


def main():
    if not (HERE / "fix.sh").exists():
        print("нет fix.sh: скопируйте fix.sh.example и закройте подмену")
        return 1
    run("fix.sh")
    ver, org = installed()
    if org is None:
        print("fix.sh не установил shop-telemetry в /tmp/sc-lab-fix-venv")
        return 1
    if org == "internal" and ver == "1.0.0":
        print(f"зачтено: установлен внутренний shop-telemetry {ver} ({org})")
        return 0
    print(f"подмена не закрыта: установлен {ver} ({org}), ждали 1.0.0 (internal)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
