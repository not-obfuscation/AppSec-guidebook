"""Эксплойт лабы race-conditions: два предела, снесённые одновременностью.

Обработчики проверяют состояние одним запросом, а записывают решение другим.
Двадцать одновременных запросов попадают в окно между этими запросами:
остаток проверен всеми, списан каждым.

Локально, к сети не обращается, против чужих систем неприменимо.

Код возврата:
    0 — эксплойт НЕ сработал (пределы удержаны во всех прогонах)
    1 — эксплойт сработал (предел превышен хотя бы раз)
"""

import sys
import threading

import sandbox
from labtarget import load

THREADS = 20
ROUNDS = 30


def _parallel(call):
    """Двадцать потоков, отпущенных одним барьером."""
    start = threading.Barrier(THREADS)

    def worker():
        start.wait()
        call()

    threads = [threading.Thread(target=worker) for _ in range(THREADS)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


def experiment_1_overdraft(lab):
    """Снятие всего остатка двадцатью запросами сразу."""
    worst, bad = 0, 0
    for _ in range(ROUNDS):
        sandbox.reset(lab.SCHEMA_UNIQUE_REDEEM)
        issued = []
        _parallel(lambda: issued.append(
            lab.withdraw(sandbox.START_BALANCE) == "выдано"))
        paid = sum(issued)
        worst = max(worst, paid)
        if paid > 1:
            bad += 1
    print(f"  опыт 1 — {THREADS} снятий по {sandbox.START_BALANCE}: "
          f"перерасход в {bad} из {ROUNDS}, выдач до {worst}")
    return bad > 0


def experiment_2_limit_overrun(lab):
    """Одноразовый промокод, применённый двадцатью запросами сразу."""
    worst, bad = 0, 0
    for _ in range(ROUNDS):
        sandbox.reset(lab.SCHEMA_UNIQUE_REDEEM)
        _parallel(lambda: lab.redeem(sandbox.PROMO_CODE, "u1"))
        got = sandbox.redemptions()
        worst = max(worst, got)
        if got > 1:
            bad += 1
    print(f"  опыт 2 — {THREADS} применений кода: сверхлимит в {bad} из "
          f"{ROUNDS}, начислений до {worst}")
    return bad > 0


def experiment_3_control(lab):
    """Контроль на живучесть: последовательная работа обязана сохраниться."""
    sandbox.reset(lab.SCHEMA_UNIQUE_REDEEM)
    ok = (lab.withdraw(40) == "выдано"
          and lab.withdraw(40) == "выдано"
          and lab.withdraw(40) == "недостаточно средств"
          and sandbox.balance() == 20
          and lab.redeem(sandbox.PROMO_CODE, "u1") == "скидка начислена"
          and lab.redeem(sandbox.PROMO_CODE, "u1") == "код уже использован")
    print(f"  опыт 3 — контроль, последовательная работа: "
          f"{'сохранена' if ok else 'ПОЧИНКА СЛОМАЛА КОШЕЛЁК'}")
    return ok


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")
    print(f"счёт: {sandbox.START_BALANCE}, код: {sandbox.PROMO_CODE}, "
          f"потоков: {THREADS}, прогонов: {ROUNDS}")
    print()
    broken = [experiment_1_overdraft(lab), experiment_2_limit_overrun(lab)]
    control = experiment_3_control(lab)
    print()
    if any(broken):
        print(f"ЭКСПЛОЙТ СРАБОТАЛ: предел снесён одновременностью "
              f"({sum(broken)} из 2 опытов)")
        return 1
    if not control:
        print("ЭКСПЛОЙТ НЕ СРАБОТАЛ, но контроль упал: кошелёк перестал "
              "работать")
        return 1
    print("эксплойт не сработал: оба предела удержаны, кошелёк работает")
    return 0


if __name__ == "__main__":
    sys.exit(main())
