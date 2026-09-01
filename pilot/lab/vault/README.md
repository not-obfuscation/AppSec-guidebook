# Лаба: выдача секрета по политике из Vault

Формат «разверни-и-проверь»: правите два файла — `app-policy.hcl`
(политика приложения) и `app-role.sql` (создание учётки базы), — пока
`check.py` не станет зелёным.

**Цель одной фразой:** добиться, чтобы `check.py` вышел с кодом 0 на
ваших двух файлах.

Стенд: postgres в контейнере и dev-сервер Vault, оба слушают только
127.0.0.1. Требования: docker с образом postgres:16-alpine (одна
загрузка) и бинарник vault (путь в переменной VAULT_BIN или в PATH).
После первой загрузки обоих сеть не нужна.

## Запуск

Проверено на Vault 1.21.3, postgres:16-alpine, Docker 29.7.2.

```bash
cd pilot/lab/vault
VAULT_BIN=/tmp/vaultbin/vault sh stand.sh start   # или vault из PATH
VAULT_BIN=/tmp/vaultbin/vault sh stand.sh reset
VAULT_BIN=/tmp/vaultbin/vault python3 check.py
```

Бланк `app-policy.hcl` + `app-role.sql` в исходном виде даёт
«не зачтено» с ровно двумя провалами: учётка умеет писать, политика
видит конфигурацию движка.

## Файлы

| Файл | Что это |
|---|---|
| `app-policy.hcl` | Политика приложения — правится |
| `app-role.sql` | Создание учётки базы — правится |
| `check.py` | Проверялка: применяет оба файла и гоняет стенд |
| `stand.sh` | Стенд: start / reset / stop |
| `hint.md` | Одна подсказка |
| `solution/` | Эталонная пара файлов |

## Сброс

```bash
VAULT_BIN=/tmp/vaultbin/vault sh stand.sh reset
```

Стенд приводится к исходному состоянию; ваши файлы не трогаются.

## Удаление

```bash
VAULT_BIN=/tmp/vaultbin/vault sh stand.sh stop
rm -rf pilot/lab/vault
```

Стенд останавливается, контейнер удаляется. Образ postgres:16-alpine
остаётся в кеше docker; удалить его — `docker rmi postgres:16-alpine`.
Ничего вне каталога лабы и этого контейнера стенд не создаёт.
