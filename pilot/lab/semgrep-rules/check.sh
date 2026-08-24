#!/bin/sh
# Прогон разметки ожиданий. Код возврата 0 — оба правила сошлись.
cd "$(dirname "$0")" || exit 1
exec ../../../.venv-tools/bin/semgrep --test --metrics=off rules/
