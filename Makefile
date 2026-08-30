# Все команды проекта. Две из них нужны каждый день:
#
#   make check   один вердикт по всем проверкам
#   make site    сайт в `site/`, открывается с диска
#
# Остальные — части этих двух, вынесенные наружу, чтобы гонять по одной. Полный
# список: `make` без цели.
#
# Проверки и сборка живут в разных окружениях и это не случайность: `.venv-site`
# держит mkdocs-material, `.venv-tools` — проверки и semgrep другой миссии.
# Смешивать их значит ронять одно обновлением другого.

PY      := .venv-tools/bin/python
PY_SITE := .venv-site/bin/python
CHECK   := $(PY) tools/check.py

.DEFAULT_GOAL := help
.PHONY: help check check-lang check-md check-model check-glossary check-code \
        lint-selftest links site serve diagrams glossary topics report setup \
        clean check-site phone check-phone labs

help:                     ## показать этот список
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) \
	| sed 's/:.*## /\t/' | expand -t 18

check:                    ## все проверки, код возврата — вердикт
	@$(CHECK)

check-lang:               ## только Vale: язык и редполитика
	@$(CHECK) --only vale

check-md:                 ## только markdownlint: разметка
	@$(CHECK) --only markdownlint

check-model:              ## только контентная модель: frontmatter, блоки, связи
	@$(CHECK) --only model

check-glossary:           ## только глоссарий: канон написания, аббревиатуры
	@$(CHECK) --only glossary

check-code:               ## только синтаксис листингов: python, javascript, bash, yaml
	@$(CHECK) --only code

links:                    ## ссылки, включая внешние адреса: единственная проверка с сетью
	@$(CHECK) --only links --external

labs:                     ## все лабы и сверка semgrep-правил: офлайн, стенды гасятся за собой
	@$(PY) tools/run_labs.py

lint-selftest:            ## у каждого правила есть фикстура: ловит своё, молчит на законном
	@$(PY) tools/lint_selftest.py

report:                   ## замечания целиком, без вердикта: список для docs/reports/INFRA.md
	@$(CHECK) --full || true

site:                     ## собрать сайт в site/ и проверить его в браузере
	@$(PY) tools/build_site.py
	@node tools/check_site.mjs || test $$? -eq 2

check-site:               ## сайт из file:// в браузере: не ходит в сеть, поиск находит
	@node tools/check_site.mjs

phone:                    ## один файл этапа 0 для телефона в dist/ (после make site)
	@$(PY) tools/build_phone.py
	@node tools/check_phone.mjs || test $$? -eq 2

check-phone:              ## файл для телефона: узкий экран, живые ссылки, схемы
	@node tools/check_phone.mjs

serve:                    ## собрать и открыть локальный сервер
	@$(PY) tools/build_site.py --serve

diagrams:                 ## нарисовать схемы mermaid в SVG (кэш по содержимому)
	@$(PY) tools/render_diagrams.py

glossary:                 ## пересобрать GLOSSARY.md из glossary.yaml
	@$(PY) tools/gen_glossary.py

topics:                   ## пересобрать topics.yaml из плана обучения
	@$(PY) tools/gen_topics.py

setup:                    ## восстановить окружение: venv, Vale, пакеты node, браузер
	@tools/setup.sh

clean:                    ## снести производное: site/, build/, dist/
	@rm -rf site build dist
	@echo "снесено: site/, build/, dist/ — схемы будут нарисованы заново"
