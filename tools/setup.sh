#!/usr/bin/env bash
# Восстановление окружения проекта: два venv, бинарь Vale, пакеты node, браузер
# для отрисовки схем. Всё это в `.gitignore` — в истории лежат только исходники и
# версии, которыми они проверены.
#
# Скрипт идемпотентен и ничего не удаляет. Отдельно про `.venv-tools`: он НЕ
# пересоздаётся, даже если выглядит неполным. В нём стоит semgrep, поставленный
# другой миссией, и его переустановка — это полчаса и полгигабайта; недостающие
# пакеты доставляются в существующее окружение.
#
# Что нужно на машине заранее: python3 (venv), pnpm, node, curl, tar. Ни один из
# них скрипт не ставит: это дело системного пакетного менеджера.
#
#   tools/setup.sh          восстановить всё, чего нет
#   tools/setup.sh --check  только проверить и напечатать версии

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

# Версии, на которых проверены проверки и сборка. Пины намеренные: обновление
# линтера — отдельная работа с прогоном всего корпуса, а не побочный эффект
# восстановления окружения.
VALE_VERSION="3.18.0"
MATERIAL_VERSION="9.7.7"
PYYAML_VERSION="6.0.3"
JSONSCHEMA_VERSION="4.25.1"

CHECK_ONLY=0
[ "${1:-}" = "--check" ] && CHECK_ONLY=1

fail=0
step() { printf '\n== %s\n' "$1"; }
ok()   { printf '   ок   %s\n' "$1"; }
bad()  { printf '   нет  %s\n' "$1"; fail=1; }
need() {
    command -v "$1" >/dev/null 2>&1 || { bad "нет команды $1 — поставьте её системным пакетом"; return 1; }
}

step "предпосылки"
for cmd in python3 curl tar pnpm node; do
    if need "$cmd"; then ok "$cmd — $(command -v "$cmd")"; fi
done
[ "$fail" = 1 ] && { printf '\nнет предпосылок, дальше идти незачем\n'; exit 1; }

# --- .venv-tools: проверки --------------------------------------------------
step ".venv-tools — проверки (pyyaml, jsonschema)"
if [ ! -x .venv-tools/bin/python ]; then
    if [ "$CHECK_ONLY" = 1 ]; then bad ".venv-tools нет"; else
        python3 -m venv .venv-tools || bad "не удалось создать .venv-tools"
    fi
fi
if [ -x .venv-tools/bin/python ] && [ "$CHECK_ONLY" = 0 ]; then
    # Ставится ровно то, что импортируют инструменты. Остальное в этом окружении
    # (semgrep и его 66 зависимостей) поставлено другой миссией и не трогается.
    .venv-tools/bin/python -m pip install --quiet --disable-pip-version-check \
        "pyyaml==$PYYAML_VERSION" "jsonschema==$JSONSCHEMA_VERSION" \
        || bad "pip не поставил pyyaml/jsonschema"
fi
if [ -x .venv-tools/bin/python ]; then
    .venv-tools/bin/python -c 'import yaml, jsonschema' 2>/dev/null \
        && ok "python $(.venv-tools/bin/python -V 2>&1 | cut -d' ' -f2), yaml и jsonschema на месте" \
        || bad "в .venv-tools не импортируются yaml/jsonschema"
fi

# --- .venv-site: сборка сайта ----------------------------------------------
step ".venv-site — сборка сайта (mkdocs-material $MATERIAL_VERSION)"
if [ ! -x .venv-site/bin/python ]; then
    if [ "$CHECK_ONLY" = 1 ]; then bad ".venv-site нет"; else
        python3 -m venv .venv-site || bad "не удалось создать .venv-site"
    fi
fi
if [ -x .venv-site/bin/python ] && [ "$CHECK_ONLY" = 0 ]; then
    .venv-site/bin/python -m pip install --quiet --disable-pip-version-check \
        "mkdocs-material==$MATERIAL_VERSION" || bad "pip не поставил mkdocs-material"
fi
if [ -x .venv-site/bin/mkdocs ]; then
    ok "$(.venv-site/bin/mkdocs --version 2>&1 | head -1)"
else
    bad "нет .venv-site/bin/mkdocs"
fi

# --- Vale -------------------------------------------------------------------
step "Vale $VALE_VERSION — язык и редполитика"
if [ ! -x tools/bin/vale ] && [ "$CHECK_ONLY" = 0 ]; then
    mkdir -p tools/bin
    tmp="$(mktemp -d)"
    url="https://github.com/errata-ai/vale/releases/download/v${VALE_VERSION}/vale_${VALE_VERSION}_Linux_64-bit.tar.gz"
    if curl -fsSL "$url" -o "$tmp/vale.tar.gz"; then
        tar -xzf "$tmp/vale.tar.gz" -C "$tmp" vale && mv "$tmp/vale" tools/bin/vale
        chmod +x tools/bin/vale
    else
        bad "не скачался Vale: $url"
    fi
    rm -rf "$tmp"
fi
if [ -x tools/bin/vale ]; then
    ok "$(tools/bin/vale --version 2>&1 | head -1)"
    # Правила стайлгайда лежат в репозитории, докачивать из сети нечего:
    # `tools/vale/styles/AppSec/` — свои правила, внешних пакетов Vale нет.
    [ -d tools/vale/styles/AppSec ] && ok "стайлгайд tools/vale/styles/AppSec на месте" \
        || bad "нет tools/vale/styles/AppSec — это часть репозитория, а не загрузка"
else
    bad "нет tools/bin/vale"
fi

# --- пакеты node ------------------------------------------------------------
step "пакеты node — markdownlint-cli2 и mermaid-cli"
if [ ! -d tools/node/node_modules ] && [ "$CHECK_ONLY" = 0 ]; then
    ( cd tools/node && pnpm install --silent ) || bad "pnpm install не прошёл"
fi
if [ -x tools/node/node_modules/.bin/markdownlint-cli2 ]; then
    ok "markdownlint-cli2 $(tools/node/node_modules/.bin/markdownlint-cli2 --version 2>&1 | head -1)"
else
    bad "нет markdownlint-cli2"
fi
[ -x tools/node/node_modules/.bin/mmdc ] && ok "mermaid-cli на месте" || bad "нет mmdc"

# --- браузер для схем -------------------------------------------------------
step "chrome-headless-shell — им mermaid-cli рисует SVG"
# pnpm блокирует postinstall-скрипты, поэтому браузер, который mermaid-cli
# обычно ставит сам, ставится отдельной командой. Это единственная причина, по
# которой шаг существует.
if [ -x tools/node/node_modules/.bin/puppeteer ]; then
    if ! ls "$HOME"/.cache/puppeteer/chrome-headless-shell/*/chrome-headless-shell-linux64/chrome-headless-shell >/dev/null 2>&1; then
        if [ "$CHECK_ONLY" = 0 ]; then
            tools/node/node_modules/.bin/puppeteer browsers install chrome-headless-shell \
                || bad "не поставился chrome-headless-shell"
        else
            bad "браузера нет в ~/.cache/puppeteer"
        fi
    fi
    if ls "$HOME"/.cache/puppeteer/chrome-headless-shell/*/chrome-headless-shell-linux64/chrome-headless-shell >/dev/null 2>&1; then
        ok "$(ls -d "$HOME"/.cache/puppeteer/chrome-headless-shell/* | head -1 | xargs basename)"
    fi
else
    bad "нет tools/node/node_modules/.bin/puppeteer"
fi

step "локальные копии чужих файлов"
# Не загрузка: файл лежит в репозитории. Проверяется потому, что без него сайт
# из `file://` тянет шим поиска с unpkg, то есть перестаёт быть офлайновым, а
# сборка при этом остаётся зелёной.
if [ -s tools/vendor/iframe-worker-shim.js ]; then
    ok "iframe-worker-shim.js ($(wc -c < tools/vendor/iframe-worker-shim.js) байт) — провенанс в tools/vendor/README.md"
else
    bad "нет tools/vendor/iframe-worker-shim.js — он часть репозитория; при утрате см. tools/vendor/README.md"
fi

# --- итог -------------------------------------------------------------------
printf '\n'
if [ "$fail" = 0 ]; then
    printf 'окружение на месте. Дальше: make check, make site\n'
    exit 0
fi
printf 'окружение неполно — что именно, видно выше по строкам «нет»\n'
printf 'частичная работа возможна: `make check` печатает недоступный инструмент\n'
printf 'отдельной строкой и не выдаёт его молчание за зелёный вердикт\n'
exit 1
