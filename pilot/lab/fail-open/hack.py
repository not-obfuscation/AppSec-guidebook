"""Эксплойт лабы fail-open. Три опыта плюс контрольный.

Опыт 1 (отказ службы прав): обычный пользователь просит привилегированное
             действие, служба мертва — обработчик отвечает 200.
Опыт 2 (отказ хранилища счётчиков): ограничитель частоты пропускает подбор
             пароля без предела.
Опыт 3 (ответ без решения): служба жива, решения не приняла, а разбор ответа
             подставляет разрешение по умолчанию.
Контроль: при живых зависимостях права работают — админу 200, обычному 403.

Возврат 0 — все три обхода закрыты и контроль цел; 1 — хотя бы один открыт.
Всё в памяти, сети нет.
"""

import sys

import labtarget
import sandbox

USER = {"name": "alice", "role": "user"}
ADMIN = {"name": "root", "role": "admin"}


def experiment_policy_down(mod) -> bool:
    """Отказ службы прав пропускает привилегированные действия."""
    policy, _ = sandbox.new_world()
    policy.state = "down"
    granted = [a for a in sorted(sandbox.PRIVILEGED)
               if mod.authorize(policy, USER, a).startswith("200")]
    print(f"  [1] служба прав мертва: привилегированных обычному "
          f"разрешено {len(granted)} из {len(sandbox.PRIVILEGED)}")
    return bool(granted)


def experiment_store_down(mod) -> bool:
    """Отказ хранилища снимает ограничение частоты."""
    _, store = sandbox.new_world()
    store.state = "down"
    passed = sum(1 for _ in range(60)
                 if mod.login_attempt(store, "alice", "guess"))
    over = max(0, passed - sandbox.RATE_LIMIT)
    print(f"  [2] хранилище мертво: пропущено {passed} из 60 при лимите "
          f"{sandbox.RATE_LIMIT}, сверх лимита {over}")
    return over > 0


def experiment_no_decision(mod) -> bool:
    """Ответ без поля решения разбирается как разрешение."""
    policy, _ = sandbox.new_world()
    policy.state = "degraded"
    answer = mod.authorize(policy, USER, "grant_admin")
    print(f"  [3] ответ без решения: обработчик ответил {answer!r}")
    return answer.startswith("200")


def control(mod) -> bool:
    """При живых зависимостях права обязаны работать по-прежнему."""
    policy, store = sandbox.new_world()
    ok = (mod.authorize(policy, ADMIN, "grant_admin").startswith("200")
          and mod.authorize(policy, USER, "grant_admin") == "403"
          and mod.authorize(policy, USER, "read").startswith("200"))
    allowed = sum(1 for _ in range(8)
                  if mod.login_attempt(store, "bob", "pw"))
    ok = ok and allowed == sandbox.RATE_LIMIT
    print(f"  [K] зависимости живы: права целы {ok}, попыток пропущено "
          f"{allowed} при лимите {sandbox.RATE_LIMIT}")
    return ok


def main() -> int:
    name, mod = labtarget.load()
    print(f"цель: {name}")
    bypasses = [experiment_policy_down(mod), experiment_store_down(mod),
                experiment_no_decision(mod)]
    intact = control(mod)
    open_count = sum(bypasses)
    print(f"обходов открыто: {open_count} из 3, контрольный опыт цел: {intact}")
    return 0 if open_count == 0 and intact else 1


if __name__ == "__main__":
    sys.exit(main())
