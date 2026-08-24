"""Эксплойт лабы oauth-basics: токен доступа в адресе переадресации.

Неявный поток возвращает токен доступа во фрагменте адреса. Фрагмент едет через
браузер и оседает там, где адрес сохраняется: история, журналы, заголовок
Referer. Опыт показывает, виден ли токен в самом адресе, не разбирая обратный
канал.

Локально, к сети не обращается, против чужих систем неприменимо.

Код возврата:
    0 — эксплойт НЕ сработал (токена в адресе нет)
    1 — эксплойт сработал (токен доступа виден в адресе)
"""

import sys
from urllib.parse import urlparse, parse_qs

from labtarget import load


def experiment_1_token_in_url(lab):
    """Токен доступа виден прямо в адресе переадресации."""
    lab.reset()
    request = lab.build_authorization_request()
    redirect = lab.authorize(request, "wiener")
    parsed = urlparse(redirect)
    in_fragment = "access_token" in (parsed.fragment or "")
    in_query = "access_token" in parse_qs(parsed.query)
    got = in_fragment or in_query
    where = "во фрагменте" if in_fragment else ("в строке запроса" if in_query else "нет")
    print(f"  опыт 1 — токен доступа в адресе переадресации: "
          f"{'ВИДЕН ' + where if got else 'нет в адресе'}")
    return got


def experiment_2_request_type(lab):
    """Запрос авторизации просит неявный поток."""
    request = lab.build_authorization_request()
    rt = parse_qs(urlparse(request).query).get("response_type", [""])[0]
    got = rt == "token"
    print(f"  опыт 2 — запрос авторизации просит response_type: "
          f"{rt!r} {'(неявный поток)' if got else '(поток кода)'}")
    return got


def experiment_3_control_login(lab):
    """Контроль: вход по-прежнему выдаёт токен доступа клиенту."""
    lab.reset()
    request = lab.build_authorization_request()
    redirect = lab.authorize(request, "wiener")
    token = lab.complete_login(redirect)
    ok = token == "AT-wiener-7a1c"
    print(f"  опыт 3 — контроль, вход wiener даёт токен: "
          f"{'да' if ok else 'ПОЧИНКА СЛОМАЛА ВХОД'}")
    return ok


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")
    hits = [experiment_1_token_in_url(lab), experiment_2_request_type(lab)]
    control = experiment_3_control_login(lab)
    print()
    if any(hits):
        print("ЭКСПЛОЙТ СРАБОТАЛ: токен доступа уходит по фронтальному каналу "
              f"({sum(hits)} из 2 признаков)")
        return 1
    if not control:
        print("ЭКСПЛОЙТ НЕ СРАБОТАЛ, но контроль упал: вход перестал работать")
        return 1
    print("эксплойт не сработал: токен в адресе не появляется, вход работает")
    return 0


if __name__ == "__main__":
    sys.exit(main())
