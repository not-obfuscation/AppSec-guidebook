"""Эксплойт лабы crypto-misuse. Три опыта плюс контрольный.

Опыт 1 (ECB): по профилю виден повтор блоков — два одинаковых поля дают
             одинаковый блок шифротекста; структура читается без ключа.
Опыт 2 (повтор nonce в CTR): два сеанса под одним nonce складываются в
             сумму открытых текстов, и известный свой сеанс выдаёт чужой.
Опыт 3 (податливость CTR): зная своё поле role=user0, атакующий правит
             шифротекст и получает role=admin0 без ключа и без ошибки.
Контроль: законно выданный сеанс читается обратно тем же приложением.

Возврат 0 — все три обхода закрыты и контроль цел; 1 — хотя бы один открыт.
Всё в памяти, сети нет.
"""

import base64
import sys

import labtarget


def xor(a: bytes, b: bytes) -> bytes:
    return bytes(p ^ q for p, q in zip(a, b))


def blocks(data: bytes, n: int = 16) -> list:
    return [data[i:i + n] for i in range(0, len(data), n)]


def experiment_ecb(mod) -> bool:
    """Повтор блоков в профиле виден снаружи -> обход, если совпали блоки.

    Длинное однобайтовое поле даёт два выровненных одинаковых блока открытого
    текста: в ECB им достаются два одинаковых блока шифротекста.
    """
    cookie = mod.issue_profile("A" * 48, "user0", 0)
    ct = base64.b64decode(cookie)
    bs = blocks(ct)
    repeated = len(bs) != len(set(bs))
    print(f"  [1] ECB: блоков {len(bs)}, различных {len(set(bs))}, "
          f"повтор виден: {repeated}")
    return repeated


def experiment_nonce(mod) -> bool:
    """Свой сеанс + сумма шифротекстов раскрывает чужой при общем nonce."""
    victim = mod.issue_session("victim01", "admin", 9999)
    mine = mod.issue_session("attacker", "user0", 1)
    cv = base64.b64decode(victim)
    cm = base64.b64decode(mine)
    mine_plain = b"user=attacker;role=user0;credit=1"
    recovered = xor(cv[:len(mine_plain)], xor(cm[:len(mine_plain)], mine_plain))
    leaked = b"role=admin" in recovered
    print(f"  [2] повтор nonce: восстановлено из чужого сеанса "
          f"{recovered.decode('utf-8', 'replace')!r}")
    return leaked


def experiment_malleable(mod) -> bool:
    """Правка шифротекста CTR меняет role=user0 на role=admin0 без ключа."""
    cookie = mod.issue_session("attacker", "user0", 1)
    ct = bytearray(base64.b64decode(cookie))
    plain = b"user=attacker;role=user0;credit=1"
    i = plain.index(b"user0")
    target = b"admin"
    for k in range(len(target)):
        ct[i + k] ^= plain[i + k] ^ target[k]
    forged = base64.b64encode(bytes(ct)).decode()
    try:
        state = mod.load_session(forged)
    except Exception as exc:                       # noqa: BLE001
        print(f"  [3] податливость CTR: подделка отвергнута "
              f"({type(exc).__name__})")
        return False
    got = state.get("role", "")
    print(f"  [3] податливость CTR: роль после правки шифротекста -> {got!r}")
    return got.startswith("admin")


def control(mod) -> bool:
    """Законный сеанс читается обратно тем же приложением."""
    cookie = mod.issue_session("alice", "user0", 50)
    state = mod.load_session(cookie)
    ok = state.get("user") == "alice" and state.get("role") == "user0"
    print(f"  [K] контроль: свой сеанс прочитан обратно: {ok}")
    return ok


def main() -> int:
    name, mod = labtarget.load()
    print(f"цель: {name}")
    broken = []
    if experiment_ecb(mod):
        broken.append("ECB")
    if experiment_nonce(mod):
        broken.append("повтор nonce")
    if experiment_malleable(mod):
        broken.append("податливость CTR")
    ok_control = control(mod)
    print()
    if broken:
        print(f"обходов открыто: {len(broken)} — {', '.join(broken)}")
        return 1
    if not ok_control:
        print("контроль не прошёл: починка сломала законную работу")
        return 1
    print("все три обхода закрыты, контроль цел")
    return 0


if __name__ == "__main__":
    sys.exit(main())
