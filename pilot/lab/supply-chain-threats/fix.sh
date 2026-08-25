#!/usr/bin/env bash
# ЗАГОТОВКА: сейчас установка берёт атакующую версию 9.9.9 из публичного индекса.
# Задача — поправить эту команду так, чтобы shop-telemetry снова ставился из
# внутреннего индекса (версия 1.0.0). Решение — в fix.sh.example и solution.md.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
PRIV="file://$HERE/registry/private-simple"
PUB="file://$HERE/registry/public-simple"
rm -rf /tmp/sc-lab-fix-venv; python3 -m venv /tmp/sc-lab-fix-venv >/dev/null 2>&1
/tmp/sc-lab-fix-venv/bin/pip install -q --no-cache-dir \
  --index-url "$PRIV" --extra-index-url "$PUB" shop-telemetry 2>&1 | grep -vi "is ignored" || true
