#!/bin/sh
# Стенд лабы vault: postgres в контейнере + dev-сервер Vault.
# Оба слушают только 127.0.0.1. Команды: start, reset, stop.
#
# Требования: docker (образ postgres:16-alpine, одна загрузка), бинарник
# vault — путь в VAULT_BIN или vault из PATH.

set -e
PG=lab-vault-pg
VAULT_BIN="${VAULT_BIN:-vault}"
PGIMAGE=postgres:16-alpine

wait_pg() {
    for i in $(seq 1 30); do
        docker exec "$PG" pg_isready -U postgres >/dev/null 2>&1 && return 0
        sleep 1
    done
    echo "postgres не поднялся" >&2; exit 1
}

wait_vault() {
    for i in $(seq 1 30); do
        VAULT_ADDR=http://127.0.0.1:8200 "$VAULT_BIN" status >/dev/null 2>&1 \
            && return 0
        sleep 1
    done
    echo "vault не поднялся" >&2; exit 1
}

case "$1" in
start)
    docker start "$PG" >/dev/null 2>&1 || docker run -d --name "$PG" \
        -e POSTGRES_PASSWORD=postgres-root \
        -p 127.0.0.1:5432:5432 "$PGIMAGE" >/dev/null
    wait_pg
    VAULT_ADDR=http://127.0.0.1:8200 "$VAULT_BIN" server -dev \
        -dev-root-token-id=devroot \
        -dev-listen-address=127.0.0.1:8200 >/dev/null 2>&1 &
    wait_vault
    ;;
reset)
    export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=devroot
    "$VAULT_BIN" secrets disable database >/dev/null 2>&1 || true
    "$VAULT_BIN" secrets enable database >/dev/null
    "$VAULT_BIN" write database/config/reports \
        plugin_name=postgresql-database-plugin \
        connection_url='postgresql://{{username}}:{{password}}@127.0.0.1:5432/postgres?sslmode=disable' \
        username=postgres password=postgres-root allowed_roles='*' >/dev/null
    docker exec "$PG" psql -U postgres -qc \
        "DROP TABLE IF EXISTS report_data" >/dev/null
    docker exec "$PG" psql -U postgres -qc \
        "CREATE TABLE report_data (id int, note text)" >/dev/null
    docker exec "$PG" psql -U postgres -qc \
        "INSERT INTO report_data VALUES (1, 'черновик')" >/dev/null
    ;;
stop)
    docker rm -f "$PG" >/dev/null 2>&1 || true
    pkill -f "vault server -dev" >/dev/null 2>&1 || true
    ;;
*)
    echo "usage: $0 start|reset|stop" >&2; exit 2
    ;;
esac
