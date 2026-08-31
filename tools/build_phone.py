#!/usr/bin/env python3
"""Один файл для телефона: одиннадцать тем этапа 0 подряд, с оглавлением.

Собирается из уже собранного сайта (`site/`), а не из `content/` напрямую:
разметку тем уже превратил в HTML тот же конвейер, что проверен браузером, и
второй конвейер разошёлся бы с первым на первой же правке. Отсюда порядок:
`make site` и только потом `make phone`.

Что делается с готовыми страницами сайта

  * из страницы берётся её `<article>` — текст темы без навигации, шапки и
    подвала движка; вокруг тем ставится своя вёрстка, узкая и без хрома;
  * идентификаторы заголовков получают приставку с идентификатором темы,
    потому что в одном файле `#3-механика` из одиннадцати тем — это одиннадцать
    одинаковых адресов;
  * ссылка на другую тему этапа 0 становится ссылкой внутри файла; ссылка на
    страницу, которой в файле нет (глоссарий, карта, тема этапа 1), теряет
    адрес и остаётся текстом — мёртвых ссылок в книге быть не должно;
  * схема вклеивается как картинка в `data:`-адресе. Не отдельным файлом,
    потому что файл должен быть один, и не вставленным `<svg>`, потому что
    mermaid зовёт все свои рисунки `my-svg` и пять таких в одном документе
    столкнулись бы идентификаторами;
  * стили — свои, внутри файла, ничего внешнего: ни шрифтов, ни таблиц стилей.

Тексты при сборке не переписываются: сюда попадает то же, что на сайте.

    make phone                                  собрать dist/
    .venv-tools/bin/python tools/build_phone.py --out dist/имя.html
"""

from __future__ import annotations

import argparse
import base64
import html
import posixpath
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_content as vc  # noqa: E402

STAGE = "protocol-basics"          # этап 0; этап 1 в этот файл не входит
ARTICLE = '<article class="md-content__inner md-typeset">'

CSS = """
:root {
  --ink: #1a1a1a; --dim: #5a5a5a; --line: #d8d8d8; --bg: #fffdf9;
  --code-bg: #f4f2ee; --accent: #7a3b00; --quote: #f7f4ee;
}
@media (prefers-color-scheme: dark) {
  :root {
    --ink: #e6e3dd; --dim: #a5a09a; --line: #3a3a3a; --bg: #16181a;
    --code-bg: #202325; --accent: #e0a05a; --quote: #1d2022;
  }
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0 auto; padding: 1rem 1rem 4rem; max-width: 42rem;
  background: var(--bg); color: var(--ink);
  font: 1.05rem/1.62 -apple-system, "Segoe UI", Roboto, "Helvetica Neue",
        system-ui, sans-serif;
  overflow-wrap: break-word;
}
h1, h2, h3 { line-height: 1.25; margin: 1.6em 0 0.6em; }
h1 { font-size: 1.55rem; }
h2 { font-size: 1.25rem; border-bottom: 1px solid var(--line);
     padding-bottom: 0.2em; }
h3 { font-size: 1.08rem; color: var(--accent); }
a { color: var(--accent); }
p, li { margin: 0.7em 0; }
ol, ul { padding-left: 1.4em; }
abbr { text-decoration: underline dotted; }
hr { border: 0; border-top: 1px solid var(--line); margin: 2em 0; }
code {
  background: var(--code-bg); border-radius: 3px; padding: 0.1em 0.3em;
  font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  font-size: 0.86em;
}
pre { margin: 1em 0; }
pre code { background: none; padding: 0; }
.highlight, pre {
  background: var(--code-bg); border-radius: 4px; padding: 0.7em 0.8em;
  overflow-x: auto; font-size: 0.8rem; line-height: 1.45;
}
.highlight pre { margin: 0; padding: 0; background: none; }
.highlight .c, .highlight .c1, .highlight .cm, .highlight .ch {
  color: var(--dim); font-style: italic; }
.highlight .k, .highlight .kd, .highlight .kn, .highlight .kr,
.highlight .kt, .highlight .nb { font-weight: 600; }
.highlight .s, .highlight .s1, .highlight .s2, .highlight .sb,
.highlight .dl, .highlight .m, .highlight .mi, .highlight .mf { color: #0b6a53; }
.highlight .na, .highlight .nf, .highlight .nc, .highlight .nn { color: #7a3b00; }
@media (prefers-color-scheme: dark) {
  .highlight .s, .highlight .s1, .highlight .s2, .highlight .sb,
  .highlight .dl, .highlight .m, .highlight .mi, .highlight .mf { color: #7fd0b5; }
  .highlight .na, .highlight .nf, .highlight .nc, .highlight .nn { color: #e0a05a; }
}
blockquote {
  margin: 1.1em 0; padding: 0.6em 0.9em; background: var(--quote);
  border-left: 3px solid var(--accent); border-radius: 0 4px 4px 0;
}
blockquote p:first-child { margin-top: 0; }
blockquote p:last-child { margin-bottom: 0; }
.tw { overflow-x: auto; margin: 1.1em 0; }
table { border-collapse: collapse; font-size: 0.9rem; }
th, td { border: 1px solid var(--line); padding: 0.35em 0.6em;
         text-align: left; vertical-align: top; }
th { background: var(--code-bg); }
img.diagram { display: block; width: 100%; height: auto; margin: 1.2em 0;
              background: #fff; border-radius: 4px; }
details { margin: 1em 0; border: 1px solid var(--line); border-radius: 4px;
          padding: 0.5em 0.8em; }
summary { cursor: pointer; font-weight: 600; }
.book-head { border-bottom: 2px solid var(--accent); padding-bottom: 0.8em; }
.book-head p { color: var(--dim); font-size: 0.92rem; }
nav.toc ol { list-style: none; padding-left: 0; counter-reset: t; }
nav.toc > ol > li { counter-increment: t; margin: 0.5em 0; }
nav.toc > ol > li > details > summary::before { content: counter(t) ". "; }
nav.toc details { border: 0; padding: 0; margin: 0.3em 0; }
nav.toc summary { font-weight: 400; }
nav.toc .meta { color: var(--dim); font-size: 0.85rem; }
nav.toc ol ol { padding-left: 1.4em; font-size: 0.92rem; }
nav.toc ol ol li { list-style: disc; margin: 0.2em 0; }
section.topic { border-top: 1px solid var(--line); margin-top: 3em; }
p.up { margin-top: 2em; font-size: 0.9rem; }
"""


def article(page_html: str) -> str:
    """Текст темы из страницы сайта: только `<article>`, без хрома движка."""
    if ARTICLE not in page_html:
        raise SystemExit("в странице сайта нет <article>: сайт собран другой версией")
    body = page_html.split(ARTICLE, 1)[1].split("</article>", 1)[0]
    # Блок «Дальше» сборка сайта генерирует сама (решение оператора 2026-08-31),
    # а в линейной книге следующая тема — просто следующий раздел файла.
    body = re.sub(r'<h2 id="дальше">.*\Z', "", body, flags=re.S)
    body = re.sub(r'<nav class="md-tags".*?</nav>', "", body, flags=re.S)
    body = re.sub(r'<a class="headerlink".*?</a>', "", body, flags=re.S)
    return body.strip()


def diagram(match: re.Match, seen: dict) -> str:
    """Схему — картинкой в `data:`-адресе, чтобы файл остался один."""
    src = match.group("src")
    name = posixpath.basename(src)
    svg = (SITE / "assets" / "diagrams" / name).read_bytes()
    seen[name] = len(svg)
    data = base64.b64encode(svg).decode("ascii")
    return ('<img class="diagram" alt="Схема (описание — в абзаце под ней)" '
            f'src="data:image/svg+xml;base64,{data}">')


def localize(body: str, pid: str, targets: dict[str, str]) -> tuple[str, int, int]:
    """Адреса внутри одного файла: приставка к идентификаторам, ссылки на темы."""
    body = re.sub(r'\b(id|name)="([^"]+)"', rf'\1="{pid}--\2"', body)
    body = re.sub(r'href="#([^"]+)"', rf'href="#{pid}--\1"', body)

    kept, dropped = 0, 0

    def cross(m: re.Match) -> str:
        nonlocal kept, dropped
        href, inner = m.group("href"), m.group("inner")
        path, _, frag = href.partition("#")
        rel = posixpath.normpath(posixpath.join(posixpath.dirname(targets["_self"]), path))
        target = targets.get(rel)
        if target is None:                      # такой страницы в файле нет
            dropped += 1
            return inner
        kept += 1
        anchor = f"#{target}--{frag}" if frag else f"#{target}"
        return f'<a href="{anchor}">{inner}</a>'

    body = re.sub(r'<a href="(?P<href>[^"]*?\.html(?:#[^"]*)?)"[^>]*>(?P<inner>.*?)</a>',
                  cross, body, flags=re.S)
    return body, kept, dropped


def build(out: Path) -> None:
    pages = [p for p in vc.load_pages() if str(p.front.get("stage")) == STAGE]
    pages.sort(key=lambda p: int(p.front.get("order", 0)))
    if not pages:
        raise SystemExit(f"нет тем этапа «{STAGE}»: собирать нечего")
    ctx = vc.Ctx()
    sdir = ctx.stages[STAGE]["dir"]
    rels = {f"{sdir}/{p.id}.html": p.id for p in pages}

    toc, sections, svgs = [], [], {}
    links_kept = links_dropped = 0
    for p in pages:
        rel = f"{sdir}/{p.id}.html"
        page_html = (SITE / rel).read_text(encoding="utf-8")
        body = article(page_html)
        body, kept, dropped = localize(body, p.id, {**rels, "_self": rel})
        links_kept += kept
        links_dropped += dropped
        body = re.sub(r'<img[^>]*class="diagram"[^>]*src="(?P<src>[^"]+)"[^>]*/?>',
                      lambda m: diagram(m, svgs), body)
        body = body.replace("<table>", '<div class="tw"><table>')
        body = body.replace("</table>", "</table></div>")
        # Заголовок темы уже есть в её тексте: здесь только оболочка и возврат.
        sections.append(
            f'<section class="topic" id="{p.id}">\n{body}\n'
            f'<p class="up"><a href="#toc">↑ Оглавление</a></p>\n</section>')

        heads = [(html.escape(re.sub(r"<[^>]+>", "", t).strip()), a) for a, t in
                 re.findall(rf'<h2 id="{p.id}--([^"]+)">(.*?)</h2>', body, flags=re.S)]
        inner = "".join(f'<li><a href="#{p.id}--{a}">{t}</a></li>' for t, a in heads)
        title = html.escape(str(p.front.get("title", p.id)))
        meta = (f'<span class="meta"> · {p.front.get("depth")}'
                f' · {p.front.get("time_min")} мин</span>')
        toc.append(f'<li><details><summary><a href="#{p.id}">{title}</a>{meta}'
                   f'</summary><ol>{inner}</ol></details></li>')

    today = date.today().isoformat()
    doc = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AppSec-гайдбук · этап 0</title>
<style>{CSS}</style>
</head>
<body>
<header class="book-head">
<h1 id="toc">Этап 0: как работает веб</h1>
<p>Одиннадцать тем подряд, собрано {today} из локального сайта гайдбука.
Файл самодостаточный: стили и схемы внутри, в сеть не обращается. Ссылки на
темы этапа 0 ведут внутрь файла; ссылки на глоссарий, карту тем и темы других
этапов оставлены текстом — их в этом файле нет.</p>
</header>
<nav class="toc" aria-label="Оглавление">
<ol>
{chr(10).join(toc)}
</ol>
</nav>
{chr(10).join(sections)}
</body>
</html>
"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    size = out.stat().st_size
    print(f"{out.relative_to(ROOT)}: {len(pages)} тем, {size / 1024:.0f} КиБ, "
          f"схем {len(svgs)} ({sum(svgs.values()) / 1024:.0f} КиБ в base64 → "
          f"{sum(len(base64.b64encode(b'x' * n)) for n in svgs.values()) / 1024:.0f} КиБ)",
          file=sys.stderr)
    print(f"ссылок между темами {links_kept}, ссылок наружу файла обезврежено "
          f"{links_dropped}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="один файл этапа 0 для телефона")
    ap.add_argument("--out", default="dist/appsec-stage-0.html",
                    help="куда положить файл (по умолчанию dist/appsec-stage-0.html)")
    args = ap.parse_args(argv)
    if not (SITE / "index.html").exists():
        raise SystemExit("нет собранного сайта: сначала `make site`")
    build(ROOT / args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
