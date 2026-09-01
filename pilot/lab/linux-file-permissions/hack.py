"""Эксплойт лабы: конфиг с токеном читают не только владелец.

Проверяет ровно одно свойство созданного файла — остаются ли в его
режиме биты чтения для группы и остальных при типичной umask 022.
Запускается локально, к сети не обращается, против чужих систем
неприменим.

Код возврата:
    0 — эксплойт НЕ сработал (лаба починена)
    1 — эксплойт сработал (конфиг читают не только владелец)
"""

import os
import sys
import tempfile

from labtarget import load


def mode_of_created(lab, umask: int) -> int:
    """Создать конфиг под заданной umask и вернуть биты его режима."""
    with tempfile.TemporaryDirectory() as workdir:
        path = os.path.join(workdir, "service.conf")
        old_umask = os.umask(umask)
        try:
            lab.write_config(path, "tok_secret_A9f3")
        finally:
            os.umask(old_umask)
        return os.stat(path).st_mode & 0o777


def experiment_1_default_umask(lab) -> bool:
    """Типичная umask 022: получают ли доступ группа и остальные."""
    mode = mode_of_created(lab, 0o022)
    group = bool(mode & 0o040)
    others = bool(mode & 0o004)
    print(f"  опыт 1 — umask 022: режим {mode:04o}, "
          f"группа читает: {'ДА' if group else 'нет'}, "
          f"остальные читают: {'ДА' if others else 'нет'}")
    return group or others


def experiment_2_strict_umask(lab) -> None:
    """Строгая umask 077: тот же вызов, другой результат.

    Справочный опыт: показывает, что безопасность файла зависит от
    настройки окружения, а не от кода. В критерий не входит.
    """
    mode = mode_of_created(lab, 0o077)
    print(f"  опыт 2 — umask 077: режим {mode:04o} "
          f"(тот же вызов, другая маска)")


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")
    leaked = experiment_1_default_umask(lab)
    experiment_2_strict_umask(lab)
    if leaked:
        print("ЭКСПЛОЙТ СРАБОТАЛ: конфиг с токеном читают не только "
              "владелец.")
        return 1
    print("ЭКСПЛОЙТ НЕ СРАБОТАЛ: ни группа, ни остальные конфига "
          "не читают.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
