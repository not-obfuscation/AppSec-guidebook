"""Пути проекта: единственное место, где они вычисляются.

Скрипты `tools/` берут пути отсюда, а не вычисляют от `__file__` каждый сам
и тем более не от текущего каталога: любой скрипт обязан работать при запуске
из любого каталога. Все константы — абсолютные пути.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CONTENT_DIR = ROOT / "content"
TEMPLATES_DIR = ROOT / "templates"
TOOLS_DIR = ROOT / "tools"

# Корневые реестры и собранный из `glossary.yaml` глоссарий.
TAXONOMY_YAML = ROOT / "taxonomy.yaml"
TOPICS_YAML = ROOT / "topics.yaml"
SOURCES_YAML = ROOT / "sources.yaml"
GLOSSARY_YAML = ROOT / "glossary.yaml"
GLOSSARY_MD = ROOT / "GLOSSARY.md"
LABS_YAML = ROOT / "labs.yaml"
AUDIT_YAML = ROOT / "audit.yaml"

EXCEPTIONS_YAML = TOOLS_DIR / "exceptions.yaml"

# Производное сборки: сносится `make clean`.
BUILD_DIR = ROOT / "build"
SITE_DIR = ROOT / "site"
DIST_DIR = ROOT / "dist"
