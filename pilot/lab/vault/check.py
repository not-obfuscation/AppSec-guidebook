"""Проверялка лабы vault: выдача по политике.

Применяет бланк автора (app-policy.hcl и app-role.sql из каталога лабы)
к работающему стенду и проверяет восемь свойств выдачи.

Стенд поднимается отдельно: sh stand.sh start && sh stand.sh reset.

Запуск из каталога лабы:
    python3 check.py
Код возврата 0 — зачтено, 1 — нет.
"""

import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
VAULT = os.environ.get("VAULT_BIN", "vault")
ENV = dict(os.environ, VAULT_ADDR="http://127.0.0.1:8200",
           VAULT_TOKEN="devroot")
FAILED = []


def check(name, condition):
    print(f"  {'OK  ' if condition else 'ПАДАЕТ'} {name}")
    if not condition:
        FAILED.append(name)


def vault(*args, token="devroot", input=None):
    env = dict(ENV, VAULT_TOKEN=token)
    return subprocess.run([VAULT] + list(args), cwd=HERE, env=env,
                          capture_output=True, text=True, input=input)


def psql(user, password, sql):
    return subprocess.run(
        ["docker", "run", "--rm", "--network", "host",
         "-e", f"PGPASSWORD={password}", "postgres:16-alpine",
         "psql", "-h", "127.0.0.1", "-U", user, "-d", "postgres",
         "-c", sql], capture_output=True, text=True)


def read_creds(token):
    out = vault("read", "-format=json", "database/creds/reporting-app",
                token=token)
    if out.returncode != 0:
        return None
    return json.loads(out.stdout)


def main():
    policy = (HERE / "app-policy.hcl").read_text(encoding="utf-8")
    role_sql = (HERE / "app-role.sql").read_text(encoding="utf-8")

    vault("write", "database/roles/reporting-app", "db_name=reports",
          f"creation_statements={role_sql}", "default_ttl=15m",
          "max_ttl=1h")
    vault("policy", "write", "reporting-app", "-",
          # политика читается из файла через stdin
          input=policy)
    token = vault("token", "create", "-policy=reporting-app",
                  "-format=json")
    app_token = json.loads(token.stdout)["auth"]["client_token"]

    first = read_creds(app_token)
    check("политика пускает читать учётку приложения", first is not None)

    if first:
        data = first["data"]
        check("у учётки есть срок годности (ttl)",
              first["lease_duration"] > 0 and first["lease_id"])
        check("динамическая учётка пускает в базу на чтение",
              psql(data["username"], data["password"],
                   "SELECT * FROM report_data").returncode == 0)
        check("та же учётка не может писать",
              psql(data["username"], data["password"],
                   "INSERT INTO report_data VALUES (2, 'x')").returncode != 0)
        second = read_creds(app_token)
        check("второе чтение даёт другую учётку",
              second and second["data"]["username"] != data["username"])
        vault("lease", "revoke", first["lease_id"])
        check("после отзыва аренды учётка мертва",
              psql(data["username"], data["password"],
                   "SELECT 1").returncode != 0)

    denied = vault("read", "database/config/reports", token=app_token)
    check("политика не даёт читать конфигурацию движка",
          denied.returncode != 0 and "denied" in denied.stderr)
    denied_sys = vault("read", "sys/mounts", token=app_token)
    check("политика не даёт ходить в sys/",
          denied_sys.returncode != 0)

    print("зачтено" if not FAILED else "не зачтено")
    for item in FAILED:
        print(f"  - {item}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
