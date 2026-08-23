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
//   * внутренние ссылки живые: файл существует, анкорь в нём есть.
//
//   node tools/check_site.mjs           проверить site/
//   node tools/check_site.mjs --keep    не гасить браузер (для отладки)
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
  let images = 0, links = 0;
  for (const rel of pages()) {
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

    const say = [];
    if (external.size) say.push(`ходит в сеть: ${[...external].join(', ')}`);
    if (errors.size) say.push(`ошибки в консоли: ${[...errors].join(' | ')}`);
    if (seen.nav < NAV_MIN) say.push(`навигации нет или она короче ${NAV_MIN} ссылок: ${seen.nav}`);
    const isTopic = rel.startsWith('stage-');
    if (isTopic && seen.toc < 5)
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
console.log('ИТОГ: сайт офлайновый, навигация и схемы на месте, ссылки живые, поиск находит — пройдено');
