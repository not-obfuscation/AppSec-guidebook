#!/usr/bin/env bash
# Две атаки цепочки поставок на локальных индексах. Наружу ничего не уходит:
# оба индекса — каталоги file:// формата PEP 503. Сети установка не требует.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
PRIV="file://$HERE/registry/private-simple"
PUB="file://$HERE/registry/public-simple"
run(){ rm -rf /tmp/sc-lab-venv; python3 -m venv /tmp/sc-lab-venv >/dev/null 2>&1
  /tmp/sc-lab-venv/bin/pip install -q --no-cache-dir "$@" 2>&1 | grep -vi "is ignored" || true; }
origin(){ /tmp/sc-lab-venv/bin/python -c 'import shop_telemetry as s;print(s.ORIGIN)' 2>/dev/null; }
echo "1. dependency confusion"
run --index-url "$PRIV" shop-telemetry
echo "   только приватный индекс      -> версия $(/tmp/sc-lab-venv/bin/pip show shop-telemetry|awk '/Version/{print $2}'), источник $(origin)"
run --index-url "$PRIV" --extra-index-url "$PUB" shop-telemetry
echo "   приватный + публичный        -> версия $(/tmp/sc-lab-venv/bin/pip show shop-telemetry|awk '/Version/{print $2}'), источник $(origin)"
echo "2. typosquatting"
run --index-url "$PUB" shop-telementry
echo "   опечатка установлена         -> $(/tmp/sc-lab-venv/bin/pip show shop-telementry|awk '/Name/{print $2}') $(/tmp/sc-lab-venv/bin/pip show shop-telementry|awk '/Version/{print $2}')"
