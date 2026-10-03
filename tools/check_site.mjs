// Проверка собранного сайта в настоящем браузере: сайт открывается из file://,
// в сеть не ходит ни за одним байтом, читается как книга.
//
// Зачем отдельная проверка. Свойство «офлайновый» сломалось молча: плагин
// `offline` у Material вставляет в каждую страницу шим WebWorker с unpkg, и
// собранный сайт без сети висел на «Инициализация поиска», хотя сборка была
// зелёной. Ни один линтер этого не видит — здесь нужен браузер.
//
// Что проверяется, по разделу «как это читают» досье приёмки этапа 0:
//   * страница открывается из file:// и не делает ни одного внешнего запроса;
//   * офлайновый поиск находит (на корневой и на вложенной странице);
//   * навигация есть на каждой странице, оглавление страницы — на темах;
//   * схемы видны как картинки, а не как битые ссылки (naturalWidth > 0);
//   * внутренние ссылки живые: файл существует, анкорь в нём есть;
//   * страница темы читается как статья (решение оператора 2026-10-02): нет
//     шапки «Уровень L…», строки «Что прочитать сначала», номеров у H2 и
//     канонических названий блоков, нет отдельного раздела «Первоисточники»;
//     есть хлебные крошки и футер «Назад / Вперёд» (А6);
//   * контраст текста, ссылок, заголовков и токенов подсветки не ниже 4,5:1
//     в тёмной и в светлой теме (WCAG 1.4.3) — по getComputedStyle.
//
//   node tools/check_site.mjs           проверить site/
//   node tools/check_site.mjs --keep    не гасить браузер (для отладки)
//   node tools/check_site.mjs --only sqli   только страницы с этой подстрокой
//                                           в пути (для отладки; вердикт
//                                           гейта — только по полному прогону)
//
// Браузер — тот же chrome-headless-shell, которым рисуются схемы; ставится
// `tools/setup.sh`. Флаги — по умолчанию: с `--allow-file-access-from-files`
// воркер из file:// создаётся и без шима, то есть проверка стала бы ложно
// зелёной.

import { readdirSync, existsSync, readFileSync } from 'node:fs';
import { resolve, dirname, join, relative, posix } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const SITE = join(ROOT, 'site');
const PUP = join(ROOT, 'tools/node/node_modules/.pnpm');
const QUERY = 'cookie';
const NAV_MIN = 12;          // двенадцать тем корпуса должны быть в навигации

function puppeteerPath() {
  const dirs = readdirSync(PUP).filter(d => d.startsWith('puppeteer@'));
  if (!dirs.length) throw new Error('нет puppeteer в tools/node — `make setup`');
  return join(PUP, dirs[0], 'node_modules/puppeteer/lib/puppeteer/puppeteer.js');
}

function chromePath() {
  const base = join(process.env.HOME, '.cache/puppeteer/chrome-headless-shell');
  if (!existsSync(base)) throw new Error('нет chrome-headless-shell — `make setup`');
  const v = readdirSync(base).sort().pop();
  return join(base, v, 'chrome-headless-shell-linux64/chrome-headless-shell');
}

/** Все страницы сайта, кроме служебной 404: относительными путями. */
function pages() {
  const out = [];
  const walk = (dir) => {
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      const p = join(dir, e.name);
      if (e.isDirectory()) { if (!['assets', 'search'].includes(e.name)) walk(p); }
      else if (e.name.endsWith('.html') && e.name !== '404.html')
        out.push(relative(SITE, p));
    }
  };
  walk(SITE);
  return out.sort();
}

// Поиск проверяется на двух страницах, а не на восемнадцати: он грузит весь
// индекс, и относительный путь к шиму и к индексу у корневой и у вложенной
// страницы разный — ошибка в глубине пути видна только на вложенной.
const SEARCH_ON = new Set(['index.html', join('stage-0', 'cookies.html')]);

// Страницы, на которых меряется контраст: главная и две темы с листингами
// разных языков. Мерить все 249 незачем — палитра одна на сайт, а токены
// подсветки на этих страницах встречаются все основные.
const CONTRAST_ON = new Set(['index.html', join('stage-1', 'sqli-basics.html'),
                             join('stage-0', 'tls-and-proxy.html'),
                             join('stage-0', 'cookies.html')]);
const CONTRAST_MIN = 4.5;

// Канонические названия блоков, которых на странице быть не должно: сборка
// заменяет их живыми (`BLOCK_TITLES` в `tools/build_site.py`). «Проверь себя»
// остаётся как есть и в список не входит.
const OLD_H2 = ['Коротко', 'Цели', 'Предвопросы', 'Механика', 'Эксплуатация',
  'Как выглядит в коде', 'Как чинится', 'Как проверить фикс',
  'Как ловится автоматикой', 'Ловушка', 'Чеклист ревью', 'Лаба', 'Задача',
  'Источники', 'Первоисточники'];

/** Замер контраста в браузере: цвет текста против фактического фона под ним
 *  (первый непрозрачный фон вверх по дереву). Возвращает худшие пары. */
function contrastProbe(min) {
  const parse = (c) => {
    const m = c.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const [r, g, b, a = 1] = m[1].split(/[ ,/]+/).filter(Boolean).map(Number);
    return { r, g, b, a };
  };
  const lum = ({ r, g, b }) => {
    const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  const bgOf = (el) => {
    const layers = [];
    for (let e = el; e; e = e.parentElement) {
      const c = parse(getComputedStyle(e).backgroundColor);
      if (c && c.a > 0) { layers.push(c); if (c.a >= 1) break; }
    }
    let base = { r: 255, g: 255, b: 255 };
    for (const c of layers.reverse())
      base = { r: c.r * c.a + base.r * (1 - c.a), g: c.g * c.a + base.g * (1 - c.a),
               b: c.b * c.a + base.b * (1 - c.a) };
    return base;
  };
  const ratio = (el) => {
    const fg = parse(getComputedStyle(el).color), bg = bgOf(el);
    const mix = { r: fg.r * fg.a + bg.r * (1 - fg.a), g: fg.g * fg.a + bg.g * (1 - fg.a),
                  b: fg.b * fg.a + bg.b * (1 - fg.a) };
    const [x, y] = [lum(mix), lum(bg)].sort((p, q) => q - p);
    return (x + 0.05) / (y + 0.05);
  };
  const groups = {
    'текст': '.md-typeset p, .md-typeset li',
    'ссылки': '.md-typeset a:not(.headerlink):not(.md-tag)',
    'заголовки': '.md-typeset h1, .md-typeset h2, .md-typeset h3',
    'меню': '.md-nav__link, .md-nav__link--active, .md-path__link',
    'врезки': '.md-typeset .admonition-title, .md-typeset summary',
    'код': '.md-typeset code',
    'токены': '.md-typeset .highlight code span[class]:not([id]):not(:empty)',
  };
  const out = {};
  for (const [name, sel] of Object.entries(groups)) {
    let worst = Infinity, at = '', n = 0;
    for (const el of document.querySelectorAll(sel)) {
      if (!el.textContent.trim() || !el.getClientRects().length) continue;
      const r = ratio(el); n += 1;
      if (r < worst) { worst = r; at = `${el.tagName.toLowerCase()}.${el.className || ''} «${el.textContent.trim().slice(0, 24)}»`; }
    }
    if (n) out[name] = { worst: Math.round(worst * 100) / 100, at, n, bad: worst < min };
  }
  return out;
}

/** Анкоря страницы: id любого элемента. Читается с диска, а не из браузера. */
const anchorsCache = new Map();
function anchors(rel) {
  if (!anchorsCache.has(rel)) {
    const html = existsSync(join(SITE, rel)) ? readFileSync(join(SITE, rel), 'utf8') : '';
    anchorsCache.set(rel, new Set([...html.matchAll(/\sid="([^"]+)"/g)].map(m => m[1])));
  }
  return anchorsCache.get(rel);
}

async function searchFinds(page) {
  await page.evaluate(q => {
    const t = document.querySelector('#__search');
    if (t) { t.checked = true; t.dispatchEvent(new Event('change', { bubbles: true })); }
    const input = document.querySelector('[data-md-component=search-query]');
    input.focus(); input.value = q;
    input.dispatchEvent(new Event('input', { bubbles: true }));
  }, QUERY);
  let found = 0;
  for (let i = 0; i < 20 && !found; i++) {
    await new Promise(r => setTimeout(r, 500));
    found = await page.evaluate(() => document.querySelectorAll(
      '[data-md-component=search-result] .md-search-result__link').length);
  }
  return found;
}

// Карта сайта. Движок собирает её пустой, потому что `site_url` не задан, а
// задать его нечем: гайдбук нигде не опубликован. Сборщик такой файл сносит
// (`tools/build_site.py`, `drop_sitemap`). Здесь проверяется, что он не
// вернулся: пустой `<urlset>` выглядит как карта сайта с нулём страниц, и
// именно так этот дефект однажды и прошёл мимо всех проверок.
function sitemapProblem() {
  const path = join(SITE, 'sitemap.xml');
  if (!existsSync(path)) return null;
  const xml = readFileSync(path, 'utf8');
  const urls = (xml.match(/<url>/g) || []).length;
  if (urls === 0) return 'sitemap.xml собран с пустым urlset: карты сайта с '
    + 'нулём страниц не бывает. Либо задан адрес публикации, либо файла нет';
  return null;
}

async function check() {
  if (!existsSync(join(SITE, 'index.html')))
    throw new Error('нет site/index.html — сначала `make site`');

  const puppeteer = (await import(puppeteerPath())).default;
  const browser = await puppeteer.launch({
    headless: true,
    executablePath: chromePath(),
    args: ['--no-sandbox', '--disable-gpu'],
  });

  const problems = [];
  const sitemap = sitemapProblem();
  console.log(`  ${sitemap ? 'НЕТ ' : 'ок  '}sitemap.xml: `
    + (sitemap ?? 'не собран, и это решение — адрес публикации не задан'));
  if (sitemap) problems.push(sitemap);
  let images = 0, links = 0;
  const only = process.argv.includes('--only')
    ? process.argv[process.argv.indexOf('--only') + 1] : null;
  for (const rel of pages().filter(r => !only || r.includes(only))) {
    const page = await browser.newPage();
    const external = new Set(), errors = new Set();
    page.on('console', m => { if (m.type() === 'error') errors.add(m.text().slice(0, 160)); });
    page.on('pageerror', e => errors.add(String(e).slice(0, 160)));
    await page.setRequestInterception(true);
    page.on('request', r => {
      if (/^https?:/.test(r.url())) {           // сети нет: так же, как в самолёте
        external.add(r.url().slice(0, 120));
        r.abort();
      } else r.continue();
    });

    await page.goto(`file://${join(SITE, rel)}`, { waitUntil: 'networkidle2', timeout: 30000 });

    const seen = await page.evaluate(() => ({
      nav: document.querySelectorAll('.md-nav__link').length,
      toc: document.querySelectorAll('.md-nav--secondary .md-nav__link').length,
      h1: (document.querySelector('h1') || {}).textContent || '',
      broken: [...document.images]
        .filter(i => !i.complete || i.naturalWidth === 0)
        .map(i => i.getAttribute('src')),
      imgs: document.images.length,
      hrefs: [...document.querySelectorAll('a[href]')]
        .map(a => a.getAttribute('href'))
        .filter(h => h && !/^(https?:|mailto:|#)/.test(h)),
    }));

    const isTopic = rel.startsWith('stage-') && !/(povtor|svodka)\.html$/.test(rel);
    const article = isTopic ? await page.evaluate((OLD) => {
      const art = document.querySelector('article') || document.body;
      const h2 = [...art.querySelectorAll('h2')].map(h => h.textContent.replace(/¶$/, '').trim());
      return {
        // Шапка — «Уровень L2 · время 33 мин»; «Уровень L1 — минимум…» в
        // теме про ASVS — текст статьи, а не шапка.
        lead: /Уровень\s+L\d\s*·|·\s*время\s+\d+\s*мин/.test(art.textContent),
        prereq: art.textContent.includes('Что прочитать сначала'),
        numbered: h2.filter(t => /^\d+\.\s/.test(t)),
        old: h2.filter(t => OLD.includes(t)),
        path: document.querySelectorAll('.md-path').length,
        footer: document.querySelectorAll('.md-footer__link').length,
      };
    }, OLD_H2) : null;

    const say = [];
    if (article) {
      if (article.lead) say.push('на странице темы осталась шапка «Уровень L…»');
      if (article.prereq) say.push('на странице темы осталась строка «Что прочитать сначала»');
      if (article.numbered.length) say.push(`нумерация у H2: ${article.numbered.join(' | ')}`);
      if (article.old.length) say.push(`канонические названия блоков вместо живых: ${article.old.join(' | ')}`);
      if (!article.path) say.push('нет хлебных крошек (.md-path)');
      if (!article.footer) say.push('нет футера «Назад / Вперёд» (.md-footer__link)');
    }

    let contrast = null;
    if (CONTRAST_ON.has(rel)) {
      contrast = {};
      for (const scheme of ['slate', 'default']) {
        await page.evaluate(s => document.body.setAttribute('data-md-color-scheme', s), scheme);
        // Раскрыть свёрнутые врезки: подпись меряется, а текст внутри — тоже.
        await page.evaluate(() => document.querySelectorAll('details').forEach(d => { d.open = true; }));
        // Ссылки и меню у темы с переходом цвета (transition): без паузы
        // getComputedStyle отдаёт цвет посреди перехода от прежней палитры.
        await new Promise(r => setTimeout(r, 600));
        contrast[scheme] = await page.evaluate(contrastProbe, CONTRAST_MIN);
        for (const [group, r] of Object.entries(contrast[scheme]))
          if (r.bad) say.push(`контраст «${group}» в теме ${scheme}: ${r.worst}:1 < ${CONTRAST_MIN}:1 — ${r.at}`);
      }
      await page.evaluate(() => document.body.setAttribute('data-md-color-scheme', 'slate'));
    }

    if (external.size) say.push(`ходит в сеть: ${[...external].join(', ')}`);
    if (errors.size) say.push(`ошибки в консоли: ${[...errors].join(' | ')}`);
    if (seen.nav < NAV_MIN) say.push(`навигации нет или она короче ${NAV_MIN} ссылок: ${seen.nav}`);
    if (rel.startsWith('stage-') && seen.toc < 5)
      say.push(`оглавление страницы короче пяти пунктов: ${seen.toc}`);
    if (!seen.h1.trim()) say.push('нет заголовка h1');
    for (const src of seen.broken) say.push(`картинка не отрисовалась: ${src}`);
    images += seen.imgs;

    // Внутренние ссылки: файл на диске и анкорь в нём. Живой ссылкой считается
    // та, по которой читатель попадёт в существующее место, а не 404 браузера.
    for (const href of seen.hrefs) {
      const [pathPart, frag] = href.split('#');
      const target = pathPart
        ? posix.normalize(posix.join(posix.dirname(rel.split(/[\\/]/).join('/')), pathPart))
        : rel.split(/[\\/]/).join('/');
      if (!existsSync(join(SITE, target))) { say.push(`ссылка в никуда: ${href}`); continue; }
      if (frag && !anchors(target).has(decodeURIComponent(frag)))
        say.push(`анкоря нет: ${href}`);
      links += 1;
    }

    let found = null;
    if (SEARCH_ON.has(rel)) {
      found = await searchFinds(page);
      if (!found) say.push(`поиск «${QUERY}» ничего не нашёл`);
    }

    const tail = [`нав. ${seen.nav}`, isTopic ? `оглавл. ${seen.toc}` : null,
                  `картинок ${seen.imgs}`, `ссылок ${seen.hrefs.length}`,
                  found === null ? null : `поиск ${found}`].filter(Boolean).join(', ');
    console.log(`  ${say.length ? 'НЕТ ' : 'ок  '}${rel}: ${tail}`);
    if (contrast) for (const [scheme, groups] of Object.entries(contrast))
      console.log(`        контраст, ${scheme === 'slate' ? 'тёмная' : 'светлая'}: `
        + Object.entries(groups).map(([g, r]) => `${g} ≥ ${r.worst} (${r.n})`).join(', '));
    for (const s of say) { problems.push(`${rel}: ${s}`); console.log(`        ${s}`); }
    await page.close();
  }

  if (!process.argv.includes('--keep')) await browser.close();
  console.log(`\nстраниц ${pages().length}, картинок ${images}, внутренних ссылок ${links}`);
  return problems;
}

console.log(`сайт из file:// без сети: навигация, схемы, ссылки, поиск «${QUERY}»`);
let problems;
try {
  problems = await check();
} catch (e) {
  console.error(`не удалось проверить: ${e.message}`);
  process.exit(2);
}
if (problems.length) {
  console.log(`ИТОГ: ${problems.length} — не пройдено`);
  process.exit(1);
}
console.log('ИТОГ: сайт офлайновый, навигация и схемы на месте, ссылки живые, поиск находит, темы без служебной обвязки, контраст ≥ 4,5:1 в обеих темах — пройдено');
